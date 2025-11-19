const express = require('express');
const { Pool } = require('pg');
const Redis = require('ioredis');
const winston = require('winston');
const nodemailer = require('nodemailer');
const { Expo } = require('expo-server-sdk');

// Configure logging
const logger = winston.createLogger({
  level: 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.json()
  ),
  transports: [
    new winston.transports.File({ filename: 'notification-service.log' }),
    new winston.transports.Console()
  ]
});

class NotificationService {
  constructor() {
    this.app = express();
    this.port = process.env.PORT || 3004;
    
    // Database connections
    this.db = new Pool({
      host: process.env.DB_HOST || 'localhost',
      port: process.env.DB_PORT || 5432,
      database: process.env.DB_NAME || 'geofarm_notifications',
      user: process.env.DB_USER || 'postgres',
      password: process.env.DB_PASSWORD || 'password',
      ssl: false
    });
    
    this.redis = new Redis({
      host: process.env.REDIS_HOST || 'localhost',
      port: process.env.REDIS_PORT || 6379,
      password: process.env.REDIS_PASSWORD || undefined
    });
    
    // Email configuration
    this.emailTransporter = nodemailer.createTransporter({
      host: process.env.SMTP_HOST || 'smtp.gmail.com',
      port: process.env.SMTP_PORT || 587,
      secure: false,
      auth: {
        user: process.env.SMTP_USER,
        pass: process.env.SMTP_PASS
      }
    });
    
    // Push notification configuration
    this.expo = new Expo();
    
    this.setupMiddleware();
    this.setupRoutes();
    this.setupErrorHandling();
    this.initializeDatabase();
    this.startNotificationProcessor();
  }
  
  setupMiddleware() {
    this.app.use(express.json({ limit: '10mb' }));
    this.app.use(express.urlencoded({ extended: true }));
  }
  
  setupRoutes() {
    // Notification management
    this.app.post('/notifications', this.createNotification.bind(this));
    this.app.get('/notifications', this.getNotifications.bind(this));
    this.app.put('/notifications/:id/read', this.markAsRead.bind(this));
    this.app.delete('/notifications/:id', this.deleteNotification.bind(this));
    
    // Device management
    this.app.post('/devices', this.registerDevice.bind(this));
    this.app.put('/devices/:id', this.updateDevice.bind(this));
    this.app.delete('/devices/:id', this.unregisterDevice.bind(this));
    
    // Preferences
    this.app.get('/preferences', this.getNotificationPreferences.bind(this));
    this.app.put('/preferences', this.updateNotificationPreferences.bind(this));
    
    // Real-time notifications
    this.app.get('/realtime', this.handleRealtimeConnection.bind(this));
    
    // Health check
    this.app.get('/health', (req, res) => {
      res.json({ 
        status: 'healthy', 
        service: 'notification-service', 
        timestamp: new Date().toISOString(),
        pendingNotifications: this.notificationQueue.length
      });
    });
  }
  
  setupErrorHandling() {
    this.app.use((error, req, res, next) => {
      logger.error('Error in notification service:', error);
      res.status(500).json({ 
        error: 'Internal server error',
        message: process.env.NODE_ENV === 'development' ? error.message : undefined
      });
    });
  }
  
  async initializeDatabase() {
    try {
      await this.db.query(`
        CREATE TABLE IF NOT EXISTS notification_preferences (
          id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          user_id UUID NOT NULL,
          email_enabled BOOLEAN DEFAULT true,
          push_enabled BOOLEAN DEFAULT true,
          sms_enabled BOOLEAN DEFAULT false,
          daily_digest BOOLEAN DEFAULT true,
          alert_types JSONB DEFAULT '{}',
          quiet_hours JSONB DEFAULT '{"start": "22:00", "end": "08:00"}',
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          UNIQUE(user_id)
        );
      `);
      
      await this.db.query(`
        CREATE TABLE IF NOT EXISTS devices (
          id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          user_id UUID NOT NULL,
          device_token VARCHAR(500) NOT NULL,
          device_type VARCHAR(50) NOT NULL,
          device_name VARCHAR(100),
          is_active BOOLEAN DEFAULT true,
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
      `);
      
      await this.db.query(`
        CREATE TABLE IF NOT EXISTS notifications (
          id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          user_id UUID NOT NULL,
          type VARCHAR(50) NOT NULL,
          title VARCHAR(200) NOT NULL,
          message TEXT NOT NULL,
          data JSONB DEFAULT '{}',
          priority VARCHAR(20) DEFAULT 'normal',
          is_read BOOLEAN DEFAULT false,
          sent_at TIMESTAMP,
          read_at TIMESTAMP,
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
      `);
      
      await this.db.query(`
        CREATE INDEX IF NOT EXISTS idx_preferences_user_id ON notification_preferences(user_id);
        CREATE INDEX IF NOT EXISTS idx_devices_user_id ON devices(user_id);
        CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id);
        CREATE INDEX IF NOT EXISTS idx_notifications_created_at ON notifications(created_at DESC);
        CREATE INDEX IF NOT EXISTS idx_notifications_is_read ON notifications(is_read);
      `);
      
      logger.info('Notification service database initialized successfully');
    } catch (error) {
      logger.error('Database initialization error:', error);
      throw error;
    }
  }
  
  async createNotification(req, res) {
    try {
      const { userId, type, title, message, data = {}, priority = 'normal' } = req.body;
      
      if (!userId || !type || !title || !message) {
        return res.status(400).json({ error: 'Missing required notification fields' });
      }
      
      const validTypes = ['info', 'warning', 'alert', 'success', 'reminder', 'system'];
      if (!validTypes.includes(type)) {
        return res.status(400).json({ error: 'Invalid notification type' });
      }
      
      const validPriorities = ['low', 'normal', 'high', 'urgent'];
      if (!validPriorities.includes(priority)) {
        return res.status(400).json({ error: 'Invalid priority level' });
      }
      
      // Create notification record
      const result = await this.db.query(
        'INSERT INTO notifications (user_id, type, title, message, data, priority) VALUES ($1, $2, $3, $4, $5, $6) RETURNING *',
        [userId, type, title, message, JSON.stringify(data), priority]
      );
      
      const notification = result.rows[0];
      
      // Get user preferences
      const preferences = await this.db.query(
        'SELECT * FROM notification_preferences WHERE user_id = $1',
        [userId]
      );
      
      const userPreferences = preferences.rows[0] || {
        email_enabled: true,
        push_enabled: true,
        sms_enabled: false
      };
      
      // Queue notification for delivery
      await this.queueNotification({
        id: notification.id,
        userId,
        type,
        title,
        message,
        data,
        priority,
        preferences: userPreferences
      });
      
      logger.info(`Notification created for user ${userId}: ${title}`);
      
      res.status(201).json({
        message: 'Notification created successfully',
        notification: {
          id: notification.id,
          userId: notification.user_id,
          type: notification.type,
          title: notification.title,
          message: notification.message,
          priority: notification.priority,
          isRead: notification.is_read,
          createdAt: notification.created_at
        }
      });
    } catch (error) {
      logger.error('Create notification error:', error);
      res.status(500).json({ error: 'Failed to create notification' });
    }
  }
  
  async getNotifications(req, res) {
    try {
      const userId = req.query.userId || req.headers['x-user-id'];
      const { page = 1, limit = 20, type = '', isRead = '' } = req.query;
      const offset = (page - 1) * limit;
      
      if (!userId) {
        return res.status(400).json({ error: 'User ID required' });
      }
      
      let query = 'SELECT * FROM notifications WHERE user_id = $1';
      let params = [userId];
      let paramCount = 1;
      
      if (type) {
        paramCount++;
        query += ` AND type = $${paramCount}`;
        params.push(type);
      }
      
      if (isRead !== '') {
        paramCount++;
        query += ` AND is_read = $${paramCount}`;
        params.push(isRead === 'true');
      }
      
      paramCount++;
      query += ` ORDER BY created_at DESC LIMIT $${paramCount}`;
      params.push(limit);
      
      paramCount++;
      query += ` OFFSET $${paramCount}`;
      params.push(offset);
      
      const result = await this.db.query(query, params);
      
      // Get unread count
      const unreadResult = await this.db.query(
        'SELECT COUNT(*) FROM notifications WHERE user_id = $1 AND is_read = false',
        [userId]
      );
      
      const notifications = result.rows.map(notification => ({
        id: notification.id,
        userId: notification.user_id,
        type: notification.type,
        title: notification.title,
        message: notification.message,
        data: notification.data,
        priority: notification.priority,
        isRead: notification.is_read,
        sentAt: notification.sent_at,
        readAt: notification.read_at,
        createdAt: notification.created_at
      }));
      
      res.json({
        notifications,
        unreadCount: parseInt(unreadResult.rows[0].count),
        pagination: {
          page: parseInt(page),
          limit: parseInt(limit)
        }
      });
    } catch (error) {
      logger.error('Get notifications error:', error);
      res.status(500).json({ error: 'Failed to get notifications' });
    }
  }
  
  async markAsRead(req, res) {
    try {
      const notificationId = req.params.id;
      const userId = req.headers['x-user-id'];
      
      const result = await this.db.query(
        'UPDATE notifications SET is_read = true, read_at = CURRENT_TIMESTAMP WHERE id = $1 AND user_id = $2 RETURNING *',
        [notificationId, userId]
      );
      
      if (result.rows.length === 0) {
        return res.status(404).json({ error: 'Notification not found' });
      }
      
      res.json({ message: 'Notification marked as read' });
    } catch (error) {
      logger.error('Mark as read error:', error);
      res.status(500).json({ error: 'Failed to mark notification as read' });
    }
  }
  
  async deleteNotification(req, res) {
    try {
      const notificationId = req.params.id;
      const userId = req.headers['x-user-id'];
      
      const result = await this.db.query(
        'DELETE FROM notifications WHERE id = $1 AND user_id = $2 RETURNING id',
        [notificationId, userId]
      );
      
      if (result.rows.length === 0) {
        return res.status(404).json({ error: 'Notification not found' });
      }
      
      res.json({ message: 'Notification deleted successfully' });
    } catch (error) {
      logger.error('Delete notification error:', error);
      res.status(500).json({ error: 'Failed to delete notification' });
    }
  }
  
  async registerDevice(req, res) {
    try {
      const { userId, deviceToken, deviceType, deviceName } = req.body;
      
      if (!userId || !deviceToken || !deviceType) {
        return res.status(400).json({ error: 'Missing required device fields' });
      }
      
      const validDeviceTypes = ['ios', 'android', 'web', 'desktop'];
      if (!validDeviceTypes.includes(deviceType)) {
        return res.status(400).json({ error: 'Invalid device type' });
      }
      
      // Check if device already exists
      const existingDevice = await this.db.query(
        'SELECT id FROM devices WHERE user_id = $1 AND device_token = $2',
        [userId, deviceToken]
      );
      
      if (existingDevice.rows.length > 0) {
        // Update existing device
        const result = await this.db.query(
          'UPDATE devices SET device_name = $1, is_active = true, updated_at = CURRENT_TIMESTAMP WHERE id = $2 RETURNING *',
          [deviceName, existingDevice.rows[0].id]
        );
        
        return res.json({
          message: 'Device updated successfully',
          device: result.rows[0]
        });
      }
      
      // Register new device
      const result = await this.db.query(
        'INSERT INTO devices (user_id, device_token, device_type, device_name) VALUES ($1, $2, $3, $4) RETURNING *',
        [userId, deviceToken, deviceType, deviceName]
      );
      
      logger.info(`Device registered for user ${userId}: ${deviceType}`);
      
      res.status(201).json({
        message: 'Device registered successfully',
        device: result.rows[0]
      });
    } catch (error) {
      logger.error('Register device error:', error);
      res.status(500).json({ error: 'Failed to register device' });
    }
  }
  
  async updateDevice(req, res) {
    try {
      const deviceId = req.params.id;
      const { deviceName, isActive } = req.body;
      
      const result = await this.db.query(
        'UPDATE devices SET device_name = $1, is_active = $2, updated_at = CURRENT_TIMESTAMP WHERE id = $3 RETURNING *',
        [deviceName, isActive, deviceId]
      );
      
      if (result.rows.length === 0) {
        return res.status(404).json({ error: 'Device not found' });
      }
      
      res.json({
        message: 'Device updated successfully',
        device: result.rows[0]
      });
    } catch (error) {
      logger.error('Update device error:', error);
      res.status(500).json({ error: 'Failed to update device' });
    }
  }
  
  async unregisterDevice(req, res) {
    try {
      const deviceId = req.params.id;
      
      const result = await this.db.query(
        'DELETE FROM devices WHERE id = $1 RETURNING id',
        [deviceId]
      );
      
      if (result.rows.length === 0) {
        return res.status(404).json({ error: 'Device not found' });
      }
      
      res.json({ message: 'Device unregistered successfully' });
    } catch (error) {
      logger.error('Unregister device error:', error);
      res.status(500).json({ error: 'Failed to unregister device' });
    }
  }
  
  async getNotificationPreferences(req, res) {
    try {
      const userId = req.headers['x-user-id'];
      
      const result = await this.db.query(
        'SELECT * FROM notification_preferences WHERE user_id = $1',
        [userId]
      );
      
      if (result.rows.length === 0) {
        // Create default preferences
        const defaultResult = await this.db.query(
          'INSERT INTO notification_preferences (user_id) VALUES ($1) RETURNING *',
          [userId]
        );
        
        return res.json({ preferences: defaultResult.rows[0] });
      }
      
      res.json({ preferences: result.rows[0] });
    } catch (error) {
      logger.error('Get preferences error:', error);
      res.status(500).json({ error: 'Failed to get notification preferences' });
    }
  }
  
  async updateNotificationPreferences(req, res) {
    try {
      const userId = req.headers['x-user-id'];
      const { emailEnabled, pushEnabled, smsEnabled, dailyDigest, alertTypes, quietHours } = req.body;
      
      const result = await this.db.query(
        `UPDATE notification_preferences 
         SET email_enabled = $1, push_enabled = $2, sms_enabled = $3, daily_digest = $4, 
             alert_types = $5, quiet_hours = $6, updated_at = CURRENT_TIMESTAMP 
         WHERE user_id = $7 RETURNING *`,
        [
          emailEnabled,
          pushEnabled,
          smsEnabled,
          dailyDigest,
          JSON.stringify(alertTypes),
          JSON.stringify(quietHours),
          userId
        ]
      );
      
      if (result.rows.length === 0) {
        return res.status(404).json({ error: 'Preferences not found' });
      }
      
      res.json({
        message: 'Notification preferences updated successfully',
        preferences: result.rows[0]
      });
    } catch (error) {
      logger.error('Update preferences error:', error);
      res.status(500).json({ error: 'Failed to update notification preferences' });
    }
  }
  
  async handleRealtimeConnection(req, res) {
    // This would handle WebSocket connections for real-time notifications
    // For now, return a simple response
    res.json({ message: 'Real-time notifications endpoint' });
  }
  
  // Queue for notifications waiting to be sent
  notificationQueue = [];
  
  async queueNotification(notification) {
    this.notificationQueue.push(notification);
    
    // Store in Redis for processing
    await this.redis.lpush('notification_queue', JSON.stringify(notification));
    
    logger.info(`Notification queued: ${notification.id}`);
  }
  
  startNotificationProcessor() {
    // Process notifications every 5 seconds
    setInterval(async () => {
      await this.processNotificationQueue();
    }, 5000);
    
    logger.info('Notification processor started');
  }
  
  async processNotificationQueue() {
    try {
      // Get notification from Redis queue
      const notificationData = await this.redis.brpop('notification_queue', 1);
      
      if (!notificationData) return;
      
      const notification = JSON.parse(notificationData[1]);
      
      // Get user preferences
      const preferences = notification.preferences;
      
      // Check quiet hours
      if (this.isInQuietHours(preferences.quiet_hours)) {
        // Defer to next processing cycle
        await this.redis.lpush('notification_queue', JSON.stringify(notification));
        return;
      }
      
      // Send email notification
      if (preferences.email_enabled) {
        await this.sendEmailNotification(notification);
      }
      
      // Send push notification
      if (preferences.push_enabled) {
        await this.sendPushNotification(notification);
      }
      
      // Update notification as sent
      await this.db.query(
        'UPDATE notifications SET sent_at = CURRENT_TIMESTAMP WHERE id = $1',
        [notification.id]
      );
      
      logger.info(`Notification sent: ${notification.id}`);
    } catch (error) {
      logger.error('Process notification queue error:', error);
    }
  }
  
  async sendEmailNotification(notification) {
    try {
      const mailOptions = {
        from: process.env.SMTP_USER || 'noreply@geofarm.com',
        to: notification.userEmail, // You'd need to get this from user service
        subject: notification.title,
        html: `
          <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #2E7D32;">GeoFarm Notification</h2>
            <div style="background-color: #f5f5f5; padding: 20px; border-radius: 8px;">
              <h3>${notification.title}</h3>
              <p>${notification.message}</p>
              ${notification.data && Object.keys(notification.data).length > 0 ? `
                <div style="margin-top: 15px;">
                  <strong>Additional Information:</strong>
                  <pre style="background-color: white; padding: 10px; border-radius: 4px; overflow-x: auto;">${JSON.stringify(notification.data, null, 2)}</pre>
                </div>
              ` : ''}
            </div>
            <p style="font-size: 12px; color: #666; margin-top: 20px;">
              This is an automated notification from GeoFarm Platform.
            </p>
          </div>
        `
      };
      
      await this.emailTransporter.sendMail(mailOptions);
      logger.info(`Email notification sent: ${notification.id}`);
    } catch (error) {
      logger.error('Send email notification error:', error);
    }
  }
  
  async sendPushNotification(notification) {
    try {
      // Get user's devices
      const devices = await this.db.query(
        'SELECT device_token, device_type FROM devices WHERE user_id = $1 AND is_active = true',
        [notification.userId]
      );
      
      const messages = [];
      
      for (const device of devices.rows) {
        if (device.device_type === 'ios' || device.device_type === 'android') {
          if (Expo.isExpoPushToken(device.device_token)) {
            messages.push({
              to: device.device_token,
              sound: 'default',
              title: notification.title,
              body: notification.message,
              data: notification.data,
              priority: notification.priority === 'urgent' ? 'high' : 'normal'
            });
          }
        }
      }
      
      if (messages.length > 0) {
        const chunks = this.expo.chunkPushNotifications(messages);
        
        for (const chunk of chunks) {
          try {
            await this.expo.sendPushNotificationsAsync(chunk);
          } catch (error) {
            logger.error('Send push notification error:', error);
          }
        }
      }
      
      logger.info(`Push notifications sent: ${notification.id} (${messages.length} devices)`);
    } catch (error) {
      logger.error('Send push notification error:', error);
    }
  }
  
  isInQuietHours(quietHours) {
    if (!quietHours || !quietHours.start || !quietHours.end) return false;
    
    const now = new Date();
    const currentTime = now.getHours() * 60 + now.getMinutes();
    
    const [startHour, startMin] = quietHours.start.split(':').map(Number);
    const [endHour, endMin] = quietHours.end.split(':').map(Number);
    
    const startTime = startHour * 60 + startMin;
    const endTime = endHour * 60 + endMin;
    
    if (startTime > endTime) {
      // Quiet hours span midnight
      return currentTime >= startTime || currentTime <= endTime;
    } else {
      return currentTime >= startTime && currentTime <= endTime;
    }
  }
  
  start() {
    this.app.listen(this.port, () => {
      logger.info(`Notification service running on port ${this.port}`);
    });
  }
}

// Start the service
if (require.main === module) {
  const notificationService = new NotificationService();
  notificationService.start();
}

module.exports = NotificationService;