/**
 * API Gateway Service for Sahool Smart Agriculture Platform
 * Handles routing, authentication, rate limiting, and request/response transformation
 */

const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const rateLimit = require('express-rate-limit');
const jwt = require('jsonwebtoken');
const httpProxy = require('http-proxy-middleware');
const winston = require('winston');

class ApiGateway {
  constructor() {
    this.app = express();
    this.setupMiddleware();
    this.setupRoutes();
    this.setupProxy();
    this.setupErrorHandling();
  }

  setupMiddleware() {
    // Security middleware
    this.app.use(helmet({
      contentSecurityPolicy: false,
      crossOriginEmbedderPolicy: false
    }));

    // CORS configuration
    this.app.use(cors({
      origin: process.env.ALLOWED_ORIGINS?.split(',') || ['http://localhost:3000', 'http://localhost:8080'],
      credentials: true,
      optionsSuccessStatus: 200
    }));

    // Rate limiting
    const limiter = rateLimit({
      windowMs: 15 * 60 * 1000, // 15 minutes
      max: 1000, // limit each IP to 1000 requests per windowMs
      message: {
        error: 'Too many requests from this IP, please try again later.',
        retryAfter: '15 minutes'
      },
      standardHeaders: true,
      legacyHeaders: false,
    });
    this.app.use(limiter);

    // Body parsing
    this.app.use(express.json({ limit: '10mb' }));
    this.app.use(express.urlencoded({ extended: true, limit: '10mb' }));

    // Request logging
    this.setupLogging();
  }

  setupLogging() {
    const logger = winston.createLogger({
      level: process.env.LOG_LEVEL || 'info',
      format: winston.format.combine(
        winston.format.timestamp(),
        winston.format.errors({ stack: true }),
        winston.format.json()
      ),
      defaultMeta: { service: 'api-gateway' },
      transports: [
        new winston.transports.File({ filename: 'logs/error.log', level: 'error' }),
        new winston.transports.File({ filename: 'logs/combined.log' }),
        new winston.transports.Console({
          format: winston.format.combine(
            winston.format.colorize(),
            winston.format.simple()
          )
        })
      ]
    });

    this.app.use((req, res, next) => {
      logger.info(`${req.method} ${req.url}`, {
        ip: req.ip,
        userAgent: req.get('User-Agent'),
        timestamp: new Date().toISOString()
      });
      next();
    });
  }

  setupRoutes() {
    // Health check endpoint
    this.app.get('/health', (req, res) => {
      res.json({
        status: 'healthy',
        timestamp: new Date().toISOString(),
        uptime: process.uptime(),
        version: require('./package.json').version
      });
    });

    // Authentication endpoint
    this.app.post('/auth/verify', this.verifyToken.bind(this));
    this.app.post('/auth/refresh', this.refreshToken.bind(this));

    // API documentation
    this.app.get('/docs', (req, res) => {
      res.redirect('/swagger-ui.html');
    });

    // Load balancer status
    this.app.get('/status', this.getServiceStatus.bind(this));
  }

  setupProxy() {
    // Service discovery configuration
    const services = {
      '/api/v1/auth': {
        target: process.env.AUTH_SERVICE_URL || 'http://localhost:8001',
        changeOrigin: true,
        pathRewrite: { '^/api/v1/auth': '' }
      },
      '/api/v1/farms': {
        target: process.env.FARMS_SERVICE_URL || 'http://localhost:8002',
        changeOrigin: true,
        pathRewrite: { '^/api/v1/farms': '' }
      },
      '/api/v1/iot': {
        target: process.env.IOT_SERVICE_URL || 'http://localhost:8003',
        changeOrigin: true,
        pathRewrite: { '^/api/v1/iot': '' }
      },
      '/api/v1/ai': {
        target: process.env.AI_SERVICE_URL || 'http://localhost:8004',
        changeOrigin: true,
        pathRewrite: { '^/api/v1/ai': '' }
      },
      '/api/v1/marketplace': {
        target: process.env.MARKETPLACE_SERVICE_URL || 'http://localhost:8005',
        changeOrigin: true,
        pathRewrite: { '^/api/v1/marketplace': '' }
      },
      '/api/v1/analytics': {
        target: process.env.ANALYTICS_SERVICE_URL || 'http://localhost:8006',
        changeOrigin: true,
        pathRewrite: { '^/api/v1/analytics': '' }
      },
      '/api/v1/weather': {
        target: process.env.WEATHER_SERVICE_URL || 'http://localhost:8007',
        changeOrigin: true,
        pathRewrite: { '^/api/v1/weather': '' }
      },
      '/api/v1/notifications': {
        target: process.env.NOTIFICATIONS_SERVICE_URL || 'http://localhost:8008',
        changeOrigin: true,
        pathRewrite: { '^/api/v1/notifications': '' }
      }
    };

    // Setup proxy for each service
    Object.entries(services).forEach(([path, config]) => {
      const proxyMiddleware = httpProxy(config);
      this.app.use(path, this.authMiddleware.bind(this), proxyMiddleware);
    });
  }

  authMiddleware(req, res, next) {
    const token = req.headers.authorization?.split(' ')[1];
    
    if (!token) {
      return res.status(401).json({
        error: 'Access token required',
        message: 'Please provide a valid authentication token'
      });
    }

    try {
      const decoded = jwt.verify(token, process.env.JWT_SECRET || 'your-secret-key');
      req.user = decoded;
      next();
    } catch (error) {
      return res.status(401).json({
        error: 'Invalid token',
        message: error.message
      });
    }
  }

  async verifyToken(req, res) {
    try {
      const { token } = req.body;
      
      if (!token) {
        return res.status(400).json({
          error: 'Token required',
          message: 'Please provide a token to verify'
        });
      }

      const decoded = jwt.verify(token, process.env.JWT_SECRET || 'your-secret-key');
      
      res.json({
        valid: true,
        user: decoded,
        expires_at: new Date(decoded.exp * 1000).toISOString()
      });
    } catch (error) {
      res.status(401).json({
        valid: false,
        error: error.message
      });
    }
  }

  async refreshToken(req, res) {
    try {
      const { refresh_token } = req.body;
      
      if (!refresh_token) {
        return res.status(400).json({
          error: 'Refresh token required',
          message: 'Please provide a refresh token'
        });
      }

      const decoded = jwt.verify(refresh_token, process.env.JWT_REFRESH_SECRET || 'your-refresh-secret');
      
      // Generate new access token
      const newAccessToken = jwt.sign(
        { user_id: decoded.user_id, email: decoded.email },
        process.env.JWT_SECRET || 'your-secret-key',
        { expiresIn: '1h' }
      );

      res.json({
        access_token: newAccessToken,
        token_type: 'Bearer',
        expires_in: 3600
      });
    } catch (error) {
      res.status(401).json({
        error: 'Invalid refresh token',
        message: error.message
      });
    }
  }

  async getServiceStatus(req, res) {
    const services = [
      { name: 'auth', url: process.env.AUTH_SERVICE_URL || 'http://localhost:8001' },
      { name: 'farms', url: process.env.FARMS_SERVICE_URL || 'http://localhost:8002' },
      { name: 'iot', url: process.env.IOT_SERVICE_URL || 'http://localhost:8003' },
      { name: 'ai', url: process.env.AI_SERVICE_URL || 'http://localhost:8004' },
      { name: 'marketplace', url: process.env.MARKETPLACE_SERVICE_URL || 'http://localhost:8005' },
      { name: 'analytics', url: process.env.ANALYTICS_SERVICE_URL || 'http://localhost:8006' },
      { name: 'weather', url: process.env.WEATHER_SERVICE_URL || 'http://localhost:8007' },
      { name: 'notifications', url: process.env.NOTIFICATIONS_SERVICE_URL || 'http://localhost:8008' }
    ];

    const statusPromises = services.map(async (service) => {
      try {
        const response = await fetch(`${service.url}/health`, {
          method: 'GET',
          timeout: 5000
        });
        
        return {
          name: service.name,
          status: response.ok ? 'healthy' : 'unhealthy',
          response_time: response.headers.get('X-Response-Time') || 'unknown'
        };
      } catch (error) {
        return {
          name: service.name,
          status: 'down',
          error: error.message
        };
      }
    });

    try {
      const results = await Promise.all(statusPromises);
      res.json({
        gateway_status: 'healthy',
        services: results,
        timestamp: new Date().toISOString()
      });
    } catch (error) {
      res.status(500).json({
        gateway_status: 'error',
        error: error.message,
        timestamp: new Date().toISOString()
      });
    }
  }

  setupErrorHandling() {
    // 404 handler
    this.app.use('*', (req, res) => {
      res.status(404).json({
        error: 'Endpoint not found',
        message: `The endpoint ${req.originalUrl} does not exist`,
        available_endpoints: [
          'GET /health',
          'POST /auth/verify',
          'POST /auth/refresh',
          'GET /docs',
          'GET /status'
        ]
      });
    });

    // Global error handler
    this.app.use((error, req, res, next) => {
      console.error('API Gateway Error:', error);
      
      res.status(error.status || 500).json({
        error: 'Internal Server Error',
        message: process.env.NODE_ENV === 'development' ? error.message : 'Something went wrong',
        timestamp: new Date().toISOString()
      });
    });
  }

  start(port = process.env.PORT || 8080) {
    return new Promise((resolve, reject) => {
      const server = this.app.listen(port, (error) => {
        if (error) {
          reject(error);
        } else {
          console.log(`🚀 API Gateway running on port ${port}`);
          console.log(`📚 Documentation available at http://localhost:${port}/docs`);
          console.log(`🔍 Health check at http://localhost:${port}/health`);
          resolve(server);
        }
      });
    });
  }
}

// Export the class and create instance
module.exports = ApiGateway;

// If run directly, start the server
if (require.main === module) {
  const gateway = new ApiGateway();
  gateway.start().catch(console.error);
}