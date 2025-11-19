const express = require('express');
const axios = require('axios');
const { Pool } = require('pg');
const Redis = require('ioredis');
const winston = require('winston');
const cron = require('node-cron');

// Configure logging
const logger = winston.createLogger({
  level: 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.json()
  ),
  transports: [
    new winston.transports.File({ filename: 'weather-service.log' }),
    new winston.transports.Console()
  ]
});

class WeatherService {
  constructor() {
    this.app = express();
    this.port = process.env.PORT || 3005;
    
    // Database connections
    this.db = new Pool({
      host: process.env.DB_HOST || 'localhost',
      port: process.env.DB_PORT || 5432,
      database: process.env.DB_NAME || 'geofarm_weather',
      user: process.env.DB_USER || 'postgres',
      password: process.env.DB_PASSWORD || 'password',
      ssl: false
    });
    
    this.redis = new Redis({
      host: process.env.REDIS_HOST || 'localhost',
      port: process.env.REDIS_PORT || 6379,
      password: process.env.REDIS_PASSWORD || undefined
    });
    
    // Weather API configuration
    this.weatherApiKey = process.env.WEATHER_API_KEY || 'your-weather-api-key';
    this.weatherBaseUrl = 'https://api.openweathermap.org/data/2.5';
    
    this.setupMiddleware();
    this.setupRoutes();
    this.setupErrorHandling();
    this.initializeDatabase();
    this.startWeatherUpdates();
  }
  
  setupMiddleware() {
    this.app.use(express.json({ limit: '10mb' }));
    this.app.use(express.urlencoded({ extended: true }));
  }
  
  setupRoutes() {
    // Current weather
    this.app.get('/current', this.getCurrentWeather.bind(this));
    this.app.post('/current', this.updateCurrentWeather.bind(this));
    
    // Weather forecast
    this.app.get('/forecast', this.getWeatherForecast.bind(this));
    this.app.post('/forecast', this.updateWeatherForecast.bind(this));
    
    // Historical weather
    this.app.get('/historical', this.getHistoricalWeather.bind(this));
    this.app.post('/historical', this.storeHistoricalWeather.bind(this));
    
    // Weather alerts
    this.app.get('/alerts', this.getWeatherAlerts.bind(this));
    this.app.post('/alerts', this.createWeatherAlert.bind(this));
    
    // Weather stations
    this.app.get('/stations', this.getWeatherStations.bind(this));
    this.app.post('/stations', this.addWeatherStation.bind(this));
    
    // Weather analytics
    this.app.get('/analytics', this.getWeatherAnalytics.bind(this));
    this.app.get('/trends', this.getWeatherTrends.bind(this));
    
    // Weather recommendations
    this.app.get('/recommendations', this.getWeatherRecommendations.bind(this));
    
    // Health check
    this.app.get('/health', (req, res) => {
      res.json({ 
        status: 'healthy', 
        service: 'weather-service', 
        timestamp: new Date().toISOString(),
        lastUpdate: this.lastWeatherUpdate
      });
    });
  }
  
  setupErrorHandling() {
    this.app.use((error, req, res, next) => {
      logger.error('Error in weather service:', error);
      res.status(500).json({ 
        error: 'Internal server error',
        message: process.env.NODE_ENV === 'development' ? error.message : undefined
      });
    });
  }
  
  async initializeDatabase() {
    try {
      await this.db.query(`
        CREATE TABLE IF NOT EXISTS weather_stations (
          id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          farm_id UUID NOT NULL,
          name VARCHAR(100) NOT NULL,
          latitude DECIMAL(10, 8) NOT NULL,
          longitude DECIMAL(11, 8) NOT NULL,
          elevation DECIMAL(8, 2),
          timezone VARCHAR(50),
          is_active BOOLEAN DEFAULT true,
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
      `);
      
      await this.db.query(`
        CREATE TABLE IF NOT EXISTS current_weather (
          id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          station_id UUID REFERENCES weather_stations(id) ON DELETE CASCADE,
          temperature DECIMAL(5, 2),
          feels_like DECIMAL(5, 2),
          humidity INTEGER,
          pressure DECIMAL(6, 2),
          wind_speed DECIMAL(5, 2),
          wind_direction INTEGER,
          visibility INTEGER,
          uv_index DECIMAL(3, 1),
          cloud_coverage INTEGER,
          weather_condition VARCHAR(50),
          weather_description TEXT,
          sunrise TIMESTAMP,
          sunset TIMESTAMP,
          recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
      `);
      
      await this.db.query(`
        CREATE TABLE IF NOT EXISTS weather_forecast (
          id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          station_id UUID REFERENCES weather_stations(id) ON DELETE CASCADE,
          forecast_date DATE NOT NULL,
          forecast_time TIMESTAMP NOT NULL,
          temperature_min DECIMAL(5, 2),
          temperature_max DECIMAL(5, 2),
          temperature_avg DECIMAL(5, 2),
          humidity INTEGER,
          precipitation DECIMAL(5, 2),
          precipitation_probability INTEGER,
          wind_speed DECIMAL(5, 2),
          wind_direction INTEGER,
          pressure DECIMAL(6, 2),
          cloud_coverage INTEGER,
          weather_condition VARCHAR(50),
          weather_description TEXT,
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
      `);
      
      await this.db.query(`
        CREATE TABLE IF NOT EXISTS weather_alerts (
          id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          station_id UUID REFERENCES weather_stations(id) ON DELETE CASCADE,
          alert_type VARCHAR(50) NOT NULL,
          severity VARCHAR(20) NOT NULL,
          title VARCHAR(200) NOT NULL,
          description TEXT NOT NULL,
          start_time TIMESTAMP,
          end_time TIMESTAMP,
          is_active BOOLEAN DEFAULT true,
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
      `);
      
      await this.db.query(`
        CREATE TABLE IF NOT EXISTS historical_weather (
          id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          station_id UUID REFERENCES weather_stations(id) ON DELETE CASCADE,
          date DATE NOT NULL,
          temperature_min DECIMAL(5, 2),
          temperature_max DECIMAL(5, 2),
          temperature_avg DECIMAL(5, 2),
          humidity_avg INTEGER,
          precipitation DECIMAL(5, 2),
          wind_speed_avg DECIMAL(5, 2),
          pressure_avg DECIMAL(6, 2),
          weather_condition VARCHAR(50),
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
      `);
      
      await this.db.query(`
        CREATE INDEX IF NOT EXISTS idx_stations_farm_id ON weather_stations(farm_id);
        CREATE INDEX IF NOT EXISTS idx_current_weather_station_id ON current_weather(station_id);
        CREATE INDEX IF NOT EXISTS idx_current_weather_recorded_at ON current_weather(recorded_at DESC);
        CREATE INDEX IF NOT EXISTS idx_forecast_station_date ON weather_forecast(station_id, forecast_date);
        CREATE INDEX IF NOT EXISTS idx_alerts_station_active ON weather_alerts(station_id, is_active);
        CREATE INDEX IF NOT EXISTS idx_historical_station_date ON historical_weather(station_id, date);
      `);
      
      logger.info('Weather service database initialized successfully');
    } catch (error) {
      logger.error('Database initialization error:', error);
      throw error;
    }
  }
  
  async getCurrentWeather(req, res) {
    try {
      const { stationId, farmId } = req.query;
      
      if (!stationId && !farmId) {
        return res.status(400).json({ error: 'Station ID or Farm ID required' });
      }
      
      let query = `
        SELECT cw.*, ws.name as station_name, ws.latitude, ws.longitude
        FROM current_weather cw
        JOIN weather_stations ws ON cw.station_id = ws.id
        WHERE 1=1
      `;
      let params = [];
      let paramCount = 0;
      
      if (stationId) {
        paramCount++;
        query += ` AND cw.station_id = $${paramCount}`;
        params.push(stationId);
      }
      
      if (farmId) {
        paramCount++;
        query += ` AND ws.farm_id = $${paramCount}`;
        params.push(farmId);
      }
      
      query += ` ORDER BY cw.recorded_at DESC LIMIT 1`;
      
      const result = await this.db.query(query, params);
      
      if (result.rows.length === 0) {
        return res.status(404).json({ error: 'No current weather data found' });
      }
      
      const weather = result.rows[0];
      
      // Get cached data if available
      const cacheKey = `current_weather:${stationId || farmId}`;
      const cached = await this.redis.get(cacheKey);
      
      if (cached) {
        return res.json({ weather: JSON.parse(cached) });
      }
      
      const weatherData = {
        id: weather.id,
        stationId: weather.station_id,
        stationName: weather.station_name,
        coordinates: {
          latitude: weather.latitude,
          longitude: weather.longitude
        },
        temperature: weather.temperature,
        feelsLike: weather.feels_like,
        humidity: weather.humidity,
        pressure: weather.pressure,
        windSpeed: weather.wind_speed,
        windDirection: weather.wind_direction,
        visibility: weather.visibility,
        uvIndex: weather.uv_index,
        cloudCoverage: weather.cloud_coverage,
        condition: weather.weather_condition,
        description: weather.weather_description,
        sunrise: weather.sunrise,
        sunset: weather.sunset,
        recordedAt: weather.recorded_at
      };
      
      // Cache for 10 minutes
      await this.redis.setex(cacheKey, 600, JSON.stringify(weatherData));
      
      res.json({ weather: weatherData });
    } catch (error) {
      logger.error('Get current weather error:', error);
      res.status(500).json({ error: 'Failed to get current weather' });
    }
  }
  
  async updateCurrentWeather(req, res) {
    try {
      const { stationId } = req.body;
      
      if (!stationId) {
        return res.status(400).json({ error: 'Station ID required' });
      }
      
      // Get station details
      const stationResult = await this.db.query(
        'SELECT * FROM weather_stations WHERE id = $1',
        [stationId]
      );
      
      if (stationResult.rows.length === 0) {
        return res.status(404).json({ error: 'Weather station not found' });
      }
      
      const station = stationResult.rows[0];
      
      // Fetch current weather from external API
      const weatherData = await this.fetchCurrentWeather(station.latitude, station.longitude);
      
      // Store in database
      const result = await this.db.query(`
        INSERT INTO current_weather (
          station_id, temperature, feels_like, humidity, pressure, 
          wind_speed, wind_direction, visibility, uv_index, cloud_coverage,
          weather_condition, weather_description, sunrise, sunset
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
        RETURNING *
      `, [
        stationId,
        weatherData.main.temp,
        weatherData.main.feels_like,
        weatherData.main.humidity,
        weatherData.main.pressure,
        weatherData.wind.speed,
        weatherData.wind.deg,
        weatherData.visibility,
        weatherData.uvi || null,
        weatherData.clouds.all,
        weatherData.weather[0].main,
        weatherData.weather[0].description,
        new Date(weatherData.sys.sunrise * 1000),
        new Date(weatherData.sys.sunset * 1000)
      ]);
      
      // Clear cache
      await this.redis.del(`current_weather:${stationId}`);
      
      logger.info(`Current weather updated for station ${stationId}`);
      
      res.json({
        message: 'Current weather updated successfully',
        weather: result.rows[0]
      });
    } catch (error) {
      logger.error('Update current weather error:', error);
      res.status(500).json({ error: 'Failed to update current weather' });
    }
  }
  
  async getWeatherForecast(req, res) {
    try {
      const { stationId, farmId, days = 7 } = req.query;
      
      if (!stationId && !farmId) {
        return res.status(400).json({ error: 'Station ID or Farm ID required' });
      }
      
      let query = `
        SELECT wf.*, ws.name as station_name
        FROM weather_forecast wf
        JOIN weather_stations ws ON wf.station_id = ws.id
        WHERE wf.forecast_date >= CURRENT_DATE
      `;
      let params = [];
      let paramCount = 0;
      
      if (stationId) {
        paramCount++;
        query += ` AND wf.station_id = $${paramCount}`;
        params.push(stationId);
      }
      
      if (farmId) {
        paramCount++;
        query += ` AND ws.farm_id = $${paramCount}`;
        params.push(farmId);
      }
      
      paramCount++;
      query += ` AND wf.forecast_date <= CURRENT_DATE + INTERVAL '${days} days'`;
      query += ` ORDER BY wf.forecast_date, wf.forecast_time`;
      
      const result = await this.db.query(query, params);
      
      const forecasts = result.rows.map(forecast => ({
        id: forecast.id,
        stationId: forecast.station_id,
        stationName: forecast.station_name,
        date: forecast.forecast_date,
        time: forecast.forecast_time,
        temperature: {
          min: forecast.temperature_min,
          max: forecast.temperature_max,
          avg: forecast.temperature_avg
        },
        humidity: forecast.humidity,
        precipitation: {
          amount: forecast.precipitation,
          probability: forecast.precipitation_probability
        },
        wind: {
          speed: forecast.wind_speed,
          direction: forecast.wind_direction
        },
        pressure: forecast.pressure,
        cloudCoverage: forecast.cloud_coverage,
        condition: forecast.weather_condition,
        description: forecast.weather_description
      }));
      
      res.json({ forecasts });
    } catch (error) {
      logger.error('Get weather forecast error:', error);
      res.status(500).json({ error: 'Failed to get weather forecast' });
    }
  }
  
  async updateWeatherForecast(req, res) {
    try {
      const { stationId, days = 7 } = req.body;
      
      if (!stationId) {
        return res.status(400).json({ error: 'Station ID required' });
      }
      
      // Get station details
      const stationResult = await this.db.query(
        'SELECT * FROM weather_stations WHERE id = $1',
        [stationId]
      );
      
      if (stationResult.rows.length === 0) {
        return res.status(404).json({ error: 'Weather station not found' });
      }
      
      const station = stationResult.rows[0];
      
      // Fetch forecast from external API
      const forecastData = await this.fetchWeatherForecast(station.latitude, station.longitude, days);
      
      // Clear existing forecast
      await this.db.query(
        'DELETE FROM weather_forecast WHERE station_id = $1 AND forecast_date >= CURRENT_DATE',
        [stationId]
      );
      
      // Store new forecast
      const insertedForecasts = [];
      
      for (const forecast of forecastData.daily) {
        const result = await this.db.query(`
          INSERT INTO weather_forecast (
            station_id, forecast_date, forecast_time, temperature_min, temperature_max,
            temperature_avg, humidity, precipitation, precipitation_probability,
            wind_speed, wind_direction, pressure, cloud_coverage, weather_condition,
            weather_description
          ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)
          RETURNING *
        `, [
          stationId,
          new Date(forecast.dt * 1000).toISOString().split('T')[0],
          new Date(forecast.dt * 1000),
          forecast.temp.min,
          forecast.temp.max,
          forecast.temp.day,
          forecast.humidity,
          forecast.rain || 0,
          Math.round(forecast.pop * 100),
          forecast.wind_speed,
          forecast.wind_deg,
          forecast.pressure,
          forecast.clouds,
          forecast.weather[0].main,
          forecast.weather[0].description
        ]);
        
        insertedForecasts.push(result.rows[0]);
      }
      
      logger.info(`Weather forecast updated for station ${stationId}: ${insertedForecasts.length} days`);
      
      res.json({
        message: 'Weather forecast updated successfully',
        forecasts: insertedForecasts
      });
    } catch (error) {
      logger.error('Update weather forecast error:', error);
      res.status(500).json({ error: 'Failed to update weather forecast' });
    }
  }
  
  async getHistoricalWeather(req, res) {
    try {
      const { stationId, farmId, startDate, endDate } = req.query;
      
      if (!stationId && !farmId) {
        return res.status(400).json({ error: 'Station ID or Farm ID required' });
      }
      
      if (!startDate || !endDate) {
        return res.status(400).json({ error: 'Start date and end date required' });
      }
      
      let query = `
        SELECT hw.*, ws.name as station_name
        FROM historical_weather hw
        JOIN weather_stations ws ON hw.station_id = ws.id
        WHERE hw.date >= $1 AND hw.date <= $2
      `;
      let params = [startDate, endDate];
      let paramCount = 2;
      
      if (stationId) {
        paramCount++;
        query += ` AND hw.station_id = $${paramCount}`;
        params.push(stationId);
      }
      
      if (farmId) {
        paramCount++;
        query += ` AND ws.farm_id = $${paramCount}`;
        params.push(farmId);
      }
      
      query += ` ORDER BY hw.date`;
      
      const result = await this.db.query(query, params);
      
      const historicalData = result.rows.map(record => ({
        id: record.id,
        stationId: record.station_id,
        stationName: record.station_name,
        date: record.date,
        temperature: {
          min: record.temperature_min,
          max: record.temperature_max,
          avg: record.temperature_avg
        },
        humidity: record.humidity_avg,
        precipitation: record.precipitation,
        windSpeed: record.wind_speed_avg,
        pressure: record.pressure_avg,
        condition: record.weather_condition
      }));
      
      res.json({ historicalData });
    } catch (error) {
      logger.error('Get historical weather error:', error);
      res.status(500).json({ error: 'Failed to get historical weather' });
    }
  }
  
  async storeHistoricalWeather(req, res) {
    try {
      const { stationId, date, weatherData } = req.body;
      
      if (!stationId || !date || !weatherData) {
        return res.status(400).json({ error: 'Missing required fields' });
      }
      
      const result = await this.db.query(`
        INSERT INTO historical_weather (
          station_id, date, temperature_min, temperature_max, temperature_avg,
          humidity_avg, precipitation, wind_speed_avg, pressure_avg,
          weather_condition
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
        RETURNING *
      `, [
        stationId,
        date,
        weatherData.temperature.min,
        weatherData.temperature.max,
        weatherData.temperature.avg,
        weatherData.humidity,
        weatherData.precipitation,
        weatherData.windSpeed,
        weatherData.pressure,
        weatherData.condition
      ]);
      
      res.status(201).json({
        message: 'Historical weather data stored successfully',
        data: result.rows[0]
      });
    } catch (error) {
      logger.error('Store historical weather error:', error);
      res.status(500).json({ error: 'Failed to store historical weather' });
    }
  }
  
  async getWeatherAlerts(req, res) {
    try {
      const { stationId, farmId, active = true } = req.query;
      
      let query = `
        SELECT wa.*, ws.name as station_name
        FROM weather_alerts wa
        JOIN weather_stations ws ON wa.station_id = ws.id
        WHERE 1=1
      `;
      let params = [];
      let paramCount = 0;
      
      if (stationId) {
        paramCount++;
        query += ` AND wa.station_id = $${paramCount}`;
        params.push(stationId);
      }
      
      if (farmId) {
        paramCount++;
        query += ` AND ws.farm_id = $${paramCount}`;
        params.push(farmId);
      }
      
      if (active === 'true') {
        query += ` AND wa.is_active = true AND (wa.end_time IS NULL OR wa.end_time > NOW())`;
      }
      
      query += ` ORDER BY wa.created_at DESC`;
      
      const result = await this.db.query(query, params);
      
      const alerts = result.rows.map(alert => ({
        id: alert.id,
        stationId: alert.station_id,
        stationName: alert.station_name,
        type: alert.alert_type,
        severity: alert.severity,
        title: alert.title,
        description: alert.description,
        startTime: alert.start_time,
        endTime: alert.end_time,
        isActive: alert.is_active,
        createdAt: alert.created_at
      }));
      
      res.json({ alerts });
    } catch (error) {
      logger.error('Get weather alerts error:', error);
      res.status(500).json({ error: 'Failed to get weather alerts' });
    }
  }
  
  async createWeatherAlert(req, res) {
    try {
      const { stationId, alertType, severity, title, description, startTime, endTime } = req.body;
      
      if (!stationId || !alertType || !severity || !title || !description) {
        return res.status(400).json({ error: 'Missing required alert fields' });
      }
      
      const validTypes = ['storm', 'frost', 'heatwave', 'drought', 'flood', 'wind', 'hail', 'fog'];
      if (!validTypes.includes(alertType)) {
        return res.status(400).json({ error: 'Invalid alert type' });
      }
      
      const validSeverities = ['minor', 'moderate', 'severe', 'extreme'];
      if (!validSeverities.includes(severity)) {
        return res.status(400).json({ error: 'Invalid severity level' });
      }
      
      const result = await this.db.query(
        'INSERT INTO weather_alerts (station_id, alert_type, severity, title, description, start_time, end_time) VALUES ($1, $2, $3, $4, $5, $6, $7) RETURNING *',
        [stationId, alertType, severity, title, description, startTime, endTime]
      );
      
      logger.info(`Weather alert created for station ${stationId}: ${title}`);
      
      res.status(201).json({
        message: 'Weather alert created successfully',
        alert: result.rows[0]
      });
    } catch (error) {
      logger.error('Create weather alert error:', error);
      res.status(500).json({ error: 'Failed to create weather alert' });
    }
  }
  
  async getWeatherStations(req, res) {
    try {
      const { farmId, active = true } = req.query;
      
      let query = 'SELECT * FROM weather_stations WHERE 1=1';
      let params = [];
      let paramCount = 0;
      
      if (farmId) {
        paramCount++;
        query += ` AND farm_id = $${paramCount}`;
        params.push(farmId);
      }
      
      if (active === 'true') {
        query += ` AND is_active = true`;
      }
      
      query += ` ORDER BY created_at`;
      
      const result = await this.db.query(query, params);
      
      const stations = result.rows.map(station => ({
        id: station.id,
        farmId: station.farm_id,
        name: station.name,
        coordinates: {
          latitude: station.latitude,
          longitude: station.longitude,
          elevation: station.elevation
        },
        timezone: station.timezone,
        isActive: station.is_active,
        createdAt: station.created_at
      }));
      
      res.json({ stations });
    } catch (error) {
      logger.error('Get weather stations error:', error);
      res.status(500).json({ error: 'Failed to get weather stations' });
    }
  }
  
  async addWeatherStation(req, res) {
    try {
      const { farmId, name, latitude, longitude, elevation, timezone } = req.body;
      
      if (!farmId || !name || !latitude || !longitude) {
        return res.status(400).json({ error: 'Missing required station fields' });
      }
      
      const result = await this.db.query(
        'INSERT INTO weather_stations (farm_id, name, latitude, longitude, elevation, timezone) VALUES ($1, $2, $3, $4, $5, $6) RETURNING *',
        [farmId, name, latitude, longitude, elevation, timezone]
      );
      
      logger.info(`Weather station added: ${name} for farm ${farmId}`);
      
      res.status(201).json({
        message: 'Weather station added successfully',
        station: result.rows[0]
      });
    } catch (error) {
      logger.error('Add weather station error:', error);
      res.status(500).json({ error: 'Failed to add weather station' });
    }
  }
  
  async getWeatherAnalytics(req, res) {
    try {
      const { stationId, farmId, period = '30days' } = req.query;
      
      if (!stationId && !farmId) {
        return res.status(400).json({ error: 'Station ID or Farm ID required' });
      }
      
      let days = 30;
      if (period === '7days') days = 7;
      else if (period === '90days') days = 90;
      else if (period === '365days') days = 365;
      
      let query = `
        SELECT 
          AVG(temperature_avg) as avg_temperature,
          MIN(temperature_min) as min_temperature,
          MAX(temperature_max) as max_temperature,
          AVG(humidity_avg) as avg_humidity,
          SUM(precipitation) as total_precipitation,
          AVG(wind_speed_avg) as avg_wind_speed,
          AVG(pressure_avg) as avg_pressure
        FROM historical_weather hw
        JOIN weather_stations ws ON hw.station_id = ws.id
        WHERE hw.date >= CURRENT_DATE - INTERVAL '${days} days'
      `;
      let params = [];
      let paramCount = 0;
      
      if (stationId) {
        paramCount++;
        query += ` AND hw.station_id = $${paramCount}`;
        params.push(stationId);
      }
      
      if (farmId) {
        paramCount++;
        query += ` AND ws.farm_id = $${paramCount}`;
        params.push(farmId);
      }
      
      const result = await this.db.query(query, params);
      
      const analytics = result.rows[0];
      
      res.json({
        period: period,
        analytics: {
          avgTemperature: parseFloat(analytics.avg_temperature) || 0,
          minTemperature: parseFloat(analytics.min_temperature) || 0,
          maxTemperature: parseFloat(analytics.max_temperature) || 0,
          avgHumidity: parseFloat(analytics.avg_humidity) || 0,
          totalPrecipitation: parseFloat(analytics.total_precipitation) || 0,
          avgWindSpeed: parseFloat(analytics.avg_wind_speed) || 0,
          avgPressure: parseFloat(analytics.avg_pressure) || 0
        }
      });
    } catch (error) {
      logger.error('Get weather analytics error:', error);
      res.status(500).json({ error: 'Failed to get weather analytics' });
    }
  }
  
  async getWeatherTrends(req, res) {
    try {
      const { stationId, farmId, metric = 'temperature', period = '30days' } = req.query;
      
      if (!stationId && !farmId) {
        return res.status(400).json({ error: 'Station ID or Farm ID required' });
      }
      
      let days = 30;
      if (period === '7days') days = 7;
      else if (period === '90days') days = 90;
      else if (period === '365days') days = 365;
      
      let metricColumn = 'temperature_avg';
      if (metric === 'humidity') metricColumn = 'humidity_avg';
      else if (metric === 'precipitation') metricColumn = 'precipitation';
      else if (metric === 'wind') metricColumn = 'wind_speed_avg';
      else if (metric === 'pressure') metricColumn = 'pressure_avg';
      
      let query = `
        SELECT hw.date, hw.${metricColumn} as value
        FROM historical_weather hw
        JOIN weather_stations ws ON hw.station_id = ws.id
        WHERE hw.date >= CURRENT_DATE - INTERVAL '${days} days'
      `;
      let params = [];
      let paramCount = 0;
      
      if (stationId) {
        paramCount++;
        query += ` AND hw.station_id = $${paramCount}`;
        params.push(stationId);
      }
      
      if (farmId) {
        paramCount++;
        query += ` AND ws.farm_id = $${paramCount}`;
        params.push(farmId);
      }
      
      query += ` ORDER BY hw.date`;
      
      const result = await this.db.query(query, params);
      
      const trends = result.rows.map(row => ({
        date: row.date,
        value: parseFloat(row.value) || 0
      }));
      
      res.json({
        metric: metric,
        period: period,
        trends: trends
      });
    } catch (error) {
      logger.error('Get weather trends error:', error);
      res.status(500).json({ error: 'Failed to get weather trends' });
    }
  }
  
  async getWeatherRecommendations(req, res) {
    try {
      const { stationId, farmId, cropType } = req.query;
      
      if (!stationId && !farmId) {
        return res.status(400).json({ error: 'Station ID or Farm ID required' });
      }
      
      // Get current weather
      const currentWeather = await this.db.query(`
        SELECT * FROM current_weather cw
        JOIN weather_stations ws ON cw.station_id = ws.id
        WHERE ${stationId ? 'cw.station_id = $1' : 'ws.farm_id = $1'}
        ORDER BY cw.recorded_at DESC LIMIT 1
      `, [stationId || farmId]);
      
      // Get 7-day forecast
      const forecast = await this.db.query(`
        SELECT * FROM weather_forecast wf
        JOIN weather_stations ws ON wf.station_id = ws.id
        WHERE ${stationId ? 'wf.station_id = $1' : 'ws.farm_id = $1'}
        AND wf.forecast_date >= CURRENT_DATE
        ORDER BY wf.forecast_date LIMIT 7
      `, [stationId || farmId]);
      
      const recommendations = this.generateWeatherRecommendations(
        currentWeather.rows[0],
        forecast.rows,
        cropType
      );
      
      res.json({ recommendations });
    } catch (error) {
      logger.error('Get weather recommendations error:', error);
      res.status(500).json({ error: 'Failed to get weather recommendations' });
    }
  }
  
  generateWeatherRecommendations(currentWeather, forecast, cropType) {
    const recommendations = [];
    
    if (!currentWeather) {
      return [{ type: 'warning', message: 'No current weather data available' }];
    }
    
    // Temperature recommendations
    if (currentWeather.temperature > 35) {
      recommendations.push({
        type: 'warning',
        category: 'temperature',
        message: 'High temperatures detected. Consider providing shade or increasing irrigation.',
        actions: ['Increase irrigation frequency', 'Provide shade nets', 'Monitor soil moisture']
      });
    }
    
    if (currentWeather.temperature < 5) {
      recommendations.push({
        type: 'warning',
        category: 'temperature',
        message: 'Low temperatures detected. Protect crops from frost damage.',
        actions: ['Cover sensitive crops', 'Use frost protection methods', 'Delay planting']
      });
    }
    
    // Precipitation recommendations
    const totalPrecipitation = forecast.reduce((sum, day) => sum + (day.precipitation || 0), 0);
    
    if (totalPrecipitation < 10) {
      recommendations.push({
        type: 'info',
        category: 'precipitation',
        message: `Low precipitation expected (${totalPrecipitation.toFixed(1)}mm). Plan irrigation accordingly.`,
        actions: ['Increase irrigation', 'Check irrigation systems', 'Monitor soil moisture']
      });
    }
    
    if (totalPrecipitation > 50) {
      recommendations.push({
        type: 'warning',
        category: 'precipitation',
        message: `Heavy rainfall expected (${totalPrecipitation.toFixed(1)}mm). Take preventive measures.`,
        actions: ['Improve drainage', 'Protect against erosion', 'Harvest ready crops']
      });
    }
    
    // Wind recommendations
    const avgWindSpeed = forecast.reduce((sum, day) => sum + (day.wind_speed || 0), 0) / forecast.length;
    
    if (avgWindSpeed > 15) {
      recommendations.push({
        type: 'warning',
        category: 'wind',
        message: `Strong winds expected (avg ${avgWindSpeed.toFixed(1)} km/h). Secure equipment and structures.`,
        actions: ['Secure greenhouse structures', 'Stake tall plants', 'Protect young seedlings']
      });
    }
    
    // Crop-specific recommendations
    if (cropType) {
      const cropRecommendations = this.getCropSpecificRecommendations(cropType, currentWeather, forecast);
      recommendations.push(...cropRecommendations);
    }
    
    return recommendations;
  }
  
  getCropSpecificRecommendations(cropType, currentWeather, forecast) {
    const recommendations = [];
    
    switch (cropType.toLowerCase()) {
      case 'wheat':
        if (currentWeather.temperature > 30) {
          recommendations.push({
            type: 'warning',
            category: 'crop-specific',
            message: 'High temperatures may affect wheat grain filling.',
            actions: ['Increase irrigation', 'Provide shade during peak hours']
          });
        }
        break;
        
      case 'corn':
        if (currentWeather.humidity > 85) {
          recommendations.push({
            type: 'warning',
            category: 'crop-specific',
            message: 'High humidity increases disease risk for corn.',
            actions: ['Improve air circulation', 'Monitor for fungal diseases']
          });
        }
        break;
        
      case 'tomato':
        if (currentWeather.temperature < 15 || currentWeather.temperature > 30) {
          recommendations.push({
            type: 'warning',
            category: 'crop-specific',
            message: 'Temperature outside optimal range for tomato growth.',
            actions: ['Use greenhouse climate control', 'Adjust planting schedule']
          });
        }
        break;
        
      default:
        recommendations.push({
          type: 'info',
          category: 'general',
          message: 'Monitor weather conditions regularly for optimal crop management.',
          actions: ['Check weather updates daily', 'Adjust farming practices accordingly']
        });
    }
    
    return recommendations;
  }
  
  async fetchCurrentWeather(lat, lon) {
    try {
      const response = await axios.get(`${this.weatherBaseUrl}/weather`, {
        params: {
          lat: lat,
          lon: lon,
          appid: this.weatherApiKey,
          units: 'metric'
        }
      });
      
      return response.data;
    } catch (error) {
      logger.error('Fetch current weather error:', error);
      throw error;
    }
  }
  
  async fetchWeatherForecast(lat, lon, days = 7) {
    try {
      const response = await axios.get(`${this.weatherBaseUrl}/onecall`, {
        params: {
          lat: lat,
          lon: lon,
          appid: this.weatherApiKey,
          units: 'metric',
          exclude: 'current,minutely,hourly,alerts'
        }
      });
      
      return response.data;
    } catch (error) {
      logger.error('Fetch weather forecast error:', error);
      throw error;
    }
  }
  
  startWeatherUpdates() {
    // Update weather data every hour
    cron.schedule('0 * * * *', async () => {
      await this.updateAllWeatherData();
    });
    
    // Update forecasts twice daily
    cron.schedule('0 6,18 * * *', async () => {
      await this.updateAllForecasts();
    });
    
    logger.info('Weather update scheduler started');
  }
  
  async updateAllWeatherData() {
    try {
      const stations = await this.db.query('SELECT * FROM weather_stations WHERE is_active = true');
      
      for (const station of stations.rows) {
        try {
          await this.updateCurrentWeather({
            body: { stationId: station.id }
          }, {
            json: () => {}
          });
        } catch (error) {
          logger.error(`Failed to update weather for station ${station.id}:`, error);
        }
      }
      
      this.lastWeatherUpdate = new Date().toISOString();
      logger.info(`Updated weather data for ${stations.rows.length} stations`);
    } catch (error) {
      logger.error('Update all weather data error:', error);
    }
  }
  
  async updateAllForecasts() {
    try {
      const stations = await this.db.query('SELECT * FROM weather_stations WHERE is_active = true');
      
      for (const station of stations.rows) {
        try {
          await this.updateWeatherForecast({
            body: { stationId: station.id }
          }, {
            json: () => {}
          });
        } catch (error) {
          logger.error(`Failed to update forecast for station ${station.id}:`, error);
        }
      }
      
      logger.info(`Updated weather forecasts for ${stations.rows.length} stations`);
    } catch (error) {
      logger.error('Update all forecasts error:', error);
    }
  }
  
  start() {
    this.app.listen(this.port, () => {
      logger.info(`Weather service running on port ${this.port}`);
    });
  }
}

// Start the service
if (require.main === module) {
  const weatherService = new WeatherService();
  weatherService.start();
}

module.exports = WeatherService;