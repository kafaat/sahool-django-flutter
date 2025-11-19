/**
 * IoT Gateway Service for Sahool Smart Agriculture Platform
 * Handles MQTT communication, device management, and data processing
 */

const mqtt = require('mqtt');
const express = require('express');
const redis = require('redis');
const winston = require('winston');
const { v4: uuidv4 } = require('uuid');

class IoTGateway {
  constructor() {
    this.app = express();
    this.mqttClient = null;
    this.redisClient = null;
    this.devices = new Map(); // In-memory device registry
    this.dataBuffer = new Map(); // Buffer for batch processing
    
    this.setupLogging();
    this.setupExpress();
    this.setupRedis();
    this.setupMQTT();
  }

  setupLogging() {
    this.logger = winston.createLogger({
      level: process.env.LOG_LEVEL || 'info',
      format: winston.format.combine(
        winston.format.timestamp(),
        winston.format.errors({ stack: true }),
        winston.format.json()
      ),
      defaultMeta: { service: 'iot-gateway' },
      transports: [
        new winston.transports.File({ filename: 'logs/iot-error.log', level: 'error' }),
        new winston.transports.File({ filename: 'logs/iot-combined.log' }),
        new winston.transports.Console({
          format: winston.format.combine(
            winston.format.colorize(),
            winston.format.simple()
          )
        })
      ]
    });
  }

  setupExpress() {
    this.app.use(express.json());
    this.app.use(express.urlencoded({ extended: true }));

    // Device management endpoints
    this.app.post('/devices/register', this.registerDevice.bind(this));
    this.app.get('/devices/:deviceId/status', this.getDeviceStatus.bind(this));
    this.app.post('/devices/:deviceId/command', this.sendCommand.bind(this));
    
    // Data endpoints
    this.app.get('/data/:deviceId', this.getDeviceData.bind(this));
    this.app.get('/data/:deviceId/latest', this.getLatestData.bind(this));
    
    // Gateway status
    this.app.get('/health', this.getHealthStatus.bind(this));
  }

  async setupRedis() {
    try {
      this.redisClient = redis.createClient({
        host: process.env.REDIS_HOST || 'localhost',
        port: process.env.REDIS_PORT || 6379
      });

      this.redisClient.on('error', (err) => {
        this.logger.error('Redis connection error:', err);
      });

      this.redisClient.on('connect', () => {
        this.logger.info('Connected to Redis');
      });

      await this.redisClient.connect();
    } catch (error) {
      this.logger.error('Failed to connect to Redis:', error);
    }
  }

  setupMQTT() {
    const mqttOptions = {
      host: process.env.MQTT_BROKER_HOST || 'localhost',
      port: process.env.MQTT_BROKER_PORT || 1883,
      clientId: `iot-gateway-${uuidv4()}`,
      keepalive: 60,
      reconnectPeriod: 1000,
      connectTimeout: 30 * 1000,
      will: {
        topic: 'gateway/status',
        payload: JSON.stringify({ status: 'offline', timestamp: Date.now() }),
        qos: 1,
        retain: false
      }
    };

    this.mqttClient = mqtt.connect(mqttOptions);

    this.mqttClient.on('connect', () => {
      this.logger.info('Connected to MQTT broker');
      this.subscribeToTopics();
      this.publishGatewayStatus('online');
    });

    this.mqttClient.on('message', this.handleMQTTMessage.bind(this));
    this.mqttClient.on('error', (error) => {
      this.logger.error('MQTT connection error:', error);
    });

    this.mqttClient.on('disconnect', () => {
      this.logger.warn('Disconnected from MQTT broker');
      this.publishGatewayStatus('offline');
    });
  }

  subscribeToTopics() {
    const topics = [
      'devices/+/data',      // Device sensor data
      'devices/+/status',    // Device status updates
      'devices/+/register',  // Device registration
      'gateway/commands',    // Commands to gateway
      'alerts/+'            // Alert messages
    ];

    topics.forEach(topic => {
      this.mqttClient.subscribe(topic, { qos: 1 }, (err) => {
        if (err) {
          this.logger.error(`Failed to subscribe to ${topic}:`, err);
        } else {
          this.logger.info(`Subscribed to topic: ${topic}`);
        }
      });
    });
  }

  handleMQTTMessage(topic, message) {
    try {
      const data = JSON.parse(message.toString());
      this.logger.info(`Received message on topic ${topic}:`, data);

      // Extract device ID from topic
      const topicParts = topic.split('/');
      const deviceId = topicParts[1];

      switch (topicParts[0]) {
        case 'devices':
          this.handleDeviceMessage(deviceId, topicParts[2], data);
          break;
        case 'gateway':
          this.handleGatewayMessage(topicParts[1], data);
          break;
        case 'alerts':
          this.handleAlertMessage(topicParts[1], data);
          break;
        default:
          this.logger.warn(`Unhandled topic: ${topic}`);
      }
    } catch (error) {
      this.logger.error('Error handling MQTT message:', error);
    }
  }

  handleDeviceMessage(deviceId, messageType, data) {
    switch (messageType) {
      case 'data':
        this.processDeviceData(deviceId, data);
        break;
      case 'status':
        this.updateDeviceStatus(deviceId, data);
        break;
      case 'register':
        this.handleDeviceRegistration(deviceId, data);
        break;
      default:
        this.logger.warn(`Unhandled device message type: ${messageType}`);
    }
  }

  processDeviceData(deviceId, data) {
    // Add timestamp
    data.timestamp = new Date().toISOString();
    data.device_id = deviceId;

    // Store in Redis for fast access
    this.storeDataInRedis(deviceId, data);

    // Add to buffer for batch processing
    if (!this.dataBuffer.has(deviceId)) {
      this.dataBuffer.set(deviceId, []);
    }
    this.dataBuffer.get(deviceId).push(data);

    // Process data if buffer reaches threshold
    if (this.dataBuffer.get(deviceId).length >= 10) {
      this.processDataBuffer(deviceId);
    }

    // Publish processed data to other services
    this.publishProcessedData(deviceId, data);
  }

  async storeDataInRedis(deviceId, data) {
    try {
      const key = `device:${deviceId}:data`;
      await this.redisClient.lpush(key, JSON.stringify(data));
      await this.redisClient.ltrim(key, 0, 999); // Keep last 1000 records
      await this.redisClient.expire(key, 86400); // Expire after 24 hours

      // Store latest reading separately
      await this.redisClient.set(`device:${deviceId}:latest`, JSON.stringify(data));
      await this.redisClient.expire(`device:${deviceId}:latest`, 3600); // Expire after 1 hour
    } catch (error) {
      this.logger.error('Error storing data in Redis:', error);
    }
  }

  async processDataBuffer(deviceId) {
    const dataArray = this.dataBuffer.get(deviceId);
    this.dataBuffer.set(deviceId, []);

    try {
      // Calculate averages and trends
      const processedData = this.processSensorData(dataArray);
      
      // Send to analytics service
      await this.sendToAnalytics(deviceId, processedData);
      
      // Check for alerts
      this.checkForAlerts(deviceId, processedData);
      
    } catch (error) {
      this.logger.error('Error processing data buffer:', error);
    }
  }

  processSensorData(dataArray) {
    const processed = {
      device_id: dataArray[0].device_id,
      timestamp: new Date().toISOString(),
      averages: {},
      trends: {},
      count: dataArray.length
    };

    // Calculate averages for numeric fields
    const numericFields = ['temperature', 'humidity', 'soil_moisture', 'ph', 'ec', 'n', 'p', 'k'];
    
    numericFields.forEach(field => {
      const values = dataArray.map(d => d[field]).filter(v => v !== undefined && v !== null);
      if (values.length > 0) {
        processed.averages[field] = values.reduce((sum, val) => sum + val, 0) / values.length;
        
        // Calculate trend
        if (values.length >= 2) {
          const firstHalf = values.slice(0, Math.floor(values.length / 2));
          const secondHalf = values.slice(Math.floor(values.length / 2));
          const firstAvg = firstHalf.reduce((sum, val) => sum + val, 0) / firstHalf.length;
          const secondAvg = secondHalf.reduce((sum, val) => sum + val, 0) / secondHalf.length;
          
          if (secondAvg > firstAvg * 1.05) {
            processed.trends[field] = 'increasing';
          } else if (secondAvg < firstAvg * 0.95) {
            processed.trends[field] = 'decreasing';
          } else {
            processed.trends[field] = 'stable';
          }
        }
      }
    });

    return processed;
  }

  async sendToAnalytics(deviceId, processedData) {
    try {
      const response = await fetch(`${process.env.ANALYTICS_SERVICE_URL || 'http://localhost:8006'}/api/v1/analytics/process`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.getServiceToken()}`
        },
        body: JSON.stringify(processedData)
      });

      if (!response.ok) {
        throw new Error(`Analytics service returned ${response.status}`);
      }

      this.logger.info(`Sent processed data to analytics for device ${deviceId}`);
    } catch (error) {
      this.logger.error('Error sending data to analytics:', error);
    }
  }

  checkForAlerts(deviceId, processedData) {
    const alerts = [];
    const { averages } = processedData;

    // Temperature alerts
    if (averages.temperature !== undefined) {
      if (averages.temperature > 40) {
        alerts.push({
          type: 'extreme_heat',
          severity: 'critical',
          message: `Temperature is extremely high: ${averages.temperature.toFixed(1)}°C`,
          device_id: deviceId,
          timestamp: new Date().toISOString()
        });
      } else if (averages.temperature < 5) {
        alerts.push({
          type: 'frost_risk',
          severity: 'high',
          message: `Temperature is very low: ${averages.temperature.toFixed(1)}°C`,
          device_id: deviceId,
          timestamp: new Date().toISOString()
        });
      }
    }

    // Soil moisture alerts
    if (averages.soil_moisture !== undefined) {
      if (averages.soil_moisture < 20) {
        alerts.push({
          type: 'low_soil_moisture',
          severity: 'high',
          message: `Soil moisture is critically low: ${averages.soil_moisture.toFixed(1)}%`,
          device_id: deviceId,
          timestamp: new Date().toISOString()
        });
      } else if (averages.soil_moisture > 80) {
        alerts.push({
          type: 'high_soil_moisture',
          severity: 'medium',
          message: `Soil moisture is very high: ${averages.soil_moisture.toFixed(1)}%`,
          device_id: deviceId,
          timestamp: new Date().toISOString()
        });
      }
    }

    // pH alerts
    if (averages.ph !== undefined) {
      if (averages.ph < 5.5 || averages.ph > 7.5) {
        alerts.push({
          type: 'ph_imbalance',
          severity: 'medium',
          message: `Soil pH is outside optimal range: ${averages.ph.toFixed(1)}`,
          device_id: deviceId,
          timestamp: new Date().toISOString()
        });
      }
    }

    // Publish alerts
    alerts.forEach(alert => {
      this.publishAlert(alert);
    });
  }

  publishAlert(alert) {
    const topic = `alerts/${alert.type}`;
    this.mqttClient.publish(topic, JSON.stringify(alert), { qos: 1, retain: false }, (err) => {
      if (err) {
        this.logger.error('Error publishing alert:', err);
      } else {
        this.logger.info(`Published alert: ${alert.type} for device ${alert.device_id}`);
      }
    });
  }

  publishProcessedData(deviceId, data) {
    const topic = `processed/${deviceId}`;
    this.mqttClient.publish(topic, JSON.stringify(data), { qos: 0, retain: false });
  }

  updateDeviceStatus(deviceId, statusData) {
    const device = this.devices.get(deviceId) || { id: deviceId };
    device.status = statusData.status || 'unknown';
    device.last_seen = new Date().toISOString();
    device.battery_level = statusData.battery_level;
    device.signal_strength = statusData.signal_strength;
    
    this.devices.set(deviceId, device);
    
    // Update Redis
    this.redisClient.set(`device:${deviceId}:status`, JSON.stringify(device));
    
    this.logger.info(`Updated status for device ${deviceId}: ${device.status}`);
  }

  handleDeviceRegistration(deviceId, registrationData) {
    const device = {
      id: deviceId,
      name: registrationData.name || deviceId,
      type: registrationData.type || 'unknown',
      location: registrationData.location,
      registered_at: new Date().toISOString(),
      status: 'online',
      last_seen: new Date().toISOString()
    };
    
    this.devices.set(deviceId, device);
    
    // Store in Redis
    this.redisClient.set(`device:${deviceId}:info`, JSON.stringify(device));
    
    this.logger.info(`Registered new device: ${deviceId} (${device.name})`);
    
    // Send welcome/configuration message
    this.sendConfiguration(deviceId);
  }

  sendConfiguration(deviceId) {
    const config = {
      reading_interval: 300, // 5 minutes
      transmission_interval: 900, // 15 minutes
      power_save_mode: false,
      calibration: {}
    };
    
    this.mqttClient.publish(`devices/${deviceId}/config`, JSON.stringify(config), { qos: 1 });
    this.logger.info(`Sent configuration to device ${deviceId}`);
  }

  handleGatewayMessage(messageType, data) {
    switch (messageType) {
      case 'restart':
        this.logger.info('Restart command received');
        process.exit(0); // Will be restarted by process manager
        break;
      case 'status':
        this.publishGatewayStatus('online');
        break;
      default:
        this.logger.warn(`Unhandled gateway message type: ${messageType}`);
    }
  }

  handleAlertMessage(alertType, data) {
    this.logger.info(`Received alert: ${alertType}`, data);
    // Forward alerts to notification service
    this.forwardToNotificationService(data);
  }

  async forwardToNotificationService(alertData) {
    try {
      await fetch(`${process.env.NOTIFICATIONS_SERVICE_URL || 'http://localhost:8008'}/api/v1/notifications/send`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.getServiceToken()}`
        },
        body: JSON.stringify({
          type: 'alert',
          data: alertData
        })
      });
    } catch (error) {
      this.logger.error('Error forwarding alert to notifications:', error);
    }
  }

  // HTTP API Methods
  async registerDevice(req, res) {
    try {
      const { deviceId, name, type, location } = req.body;
      
      if (!deviceId) {
        return res.status(400).json({
          error: 'Device ID is required',
          message: 'Please provide a unique device identifier'
        });
      }

      const device = {
        id: deviceId,
        name: name || deviceId,
        type: type || 'unknown',
        location: location,
        registered_at: new Date().toISOString(),
        status: 'registered'
      };

      this.devices.set(deviceId, device);
      
      // Send registration acknowledgment
      this.mqttClient.publish(`devices/${deviceId}/ack`, JSON.stringify({
        status: 'registered',
        timestamp: new Date().toISOString()
      }), { qos: 1 });

      res.status(201).json({
        message: 'Device registered successfully',
        device: device
      });

    } catch (error) {
      this.logger.error('Error registering device:', error);
      res.status(500).json({
        error: 'Registration failed',
        message: error.message
      });
    }
  }

  async getDeviceStatus(req, res) {
    try {
      const { deviceId } = req.params;
      const device = this.devices.get(deviceId);
      
      if (!device) {
        return res.status(404).json({
          error: 'Device not found',
          message: `No device found with ID: ${deviceId}`
        });
      }

      res.json({
        device: device,
        last_seen: device.last_seen,
        status: device.status
      });

    } catch (error) {
      this.logger.error('Error getting device status:', error);
      res.status(500).json({
        error: 'Failed to get device status',
        message: error.message
      });
    }
  }

  async sendCommand(req, res) {
    try {
      const { deviceId } = req.params;
      const { command, parameters } = req.body;
      
      if (!command) {
        return res.status(400).json({
          error: 'Command is required',
          message: 'Please specify a command to send to the device'
        });
      }

      const device = this.devices.get(deviceId);
      if (!device) {
        return res.status(404).json({
          error: 'Device not found',
          message: `No device found with ID: ${deviceId}`
        });
      }

      const commandMessage = {
        command: command,
        parameters: parameters || {},
        timestamp: new Date().toISOString(),
        id: uuidv4()
      };

      this.mqttClient.publish(`devices/${deviceId}/commands`, JSON.stringify(commandMessage), { qos: 1 }, (err) => {
        if (err) {
          this.logger.error('Error sending command:', err);
          return res.status(500).json({
            error: 'Failed to send command',
            message: err.message
          });
        }

        res.json({
          message: 'Command sent successfully',
          command_id: commandMessage.id,
          device_id: deviceId,
          command: command
        });
      });

    } catch (error) {
      this.logger.error('Error sending command:', error);
      res.status(500).json({
        error: 'Command failed',
        message: error.message
      });
    }
  }

  async getDeviceData(req, res) {
    try {
      const { deviceId } = req.params;
      const { limit = 100, start_date, end_date } = req.query;

      const key = `device:${deviceId}:data`;
      const data = await this.redisClient.lrange(key, 0, parseInt(limit) - 1);
      
      let parsedData = data.map(item => JSON.parse(item));
      
      // Filter by date range if provided
      if (start_date || end_date) {
        parsedData = parsedData.filter(item => {
          const itemDate = new Date(item.timestamp);
          if (start_date && itemDate < new Date(start_date)) return false;
          if (end_date && itemDate > new Date(end_date)) return false;
          return true;
        });
      }

      res.json({
        device_id: deviceId,
        data: parsedData,
        count: parsedData.length,
        limit: parseInt(limit)
      });

    } catch (error) {
      this.logger.error('Error getting device data:', error);
      res.status(500).json({
        error: 'Failed to get device data',
        message: error.message
      });
    }
  }

  async getLatestData(req, res) {
    try {
      const { deviceId } = req.params;
      const key = `device:${deviceId}:latest`;
      
      const data = await this.redisClient.get(key);
      
      if (!data) {
        return res.status(404).json({
          error: 'No data found',
          message: `No recent data available for device: ${deviceId}`
        });
      }

      res.json({
        device_id: deviceId,
        data: JSON.parse(data)
      });

    } catch (error) {
      this.logger.error('Error getting latest data:', error);
      res.status(500).json({
        error: 'Failed to get latest data',
        message: error.message
      });
    }
  }

  getHealthStatus(req, res) {
    const status = {
      gateway_status: 'healthy',
      mqtt_connected: this.mqttClient && this.mqttClient.connected,
      redis_connected: this.redisClient && this.redisClient.isOpen,
      registered_devices: this.devices.size,
      uptime: process.uptime(),
      timestamp: new Date().toISOString(),
      version: require('./package.json').version
    };

    res.json(status);
  }

  publishGatewayStatus(status) {
    if (this.mqttClient && this.mqttClient.connected) {
      const statusMessage = {
        status: status,
        timestamp: new Date().toISOString(),
        uptime: process.uptime(),
        registered_devices: this.devices.size
      };

      this.mqttClient.publish('gateway/status', JSON.stringify(statusMessage), { qos: 1, retain: true });
      this.logger.info(`Gateway status: ${status}`);
    }
  }

  getServiceToken() {
    // In production, this should be a proper service-to-service authentication token
    return jwt.sign(
      { service: 'iot-gateway', timestamp: Date.now() },
      process.env.JWT_SECRET || 'your-secret-key',
      { expiresIn: '1h' }
    );
  }

  start(port = process.env.PORT || 8081) {
    return new Promise((resolve, reject) => {
      const server = this.app.listen(port, (error) => {
        if (error) {
          reject(error);
        } else {
          this.logger.info(`🚀 IoT Gateway running on port ${port}`);
          this.logger.info(`📡 Connected to MQTT broker`);
          this.logger.info(`💾 Connected to Redis`);
          resolve(server);
        }
      });
    });
  }
}

module.exports = IoTGateway;

// If run directly, start the server
if (require.main === module) {
  const gateway = new IoTGateway();
  gateway.start().catch(console.error);
}