const express = require('express');
const bcrypt = require('bcrypt');
const jwt = require('jsonwebtoken');
const { Pool } = require('pg');
const Redis = require('ioredis');
const multer = require('multer');
const path = require('path');
const winston = require('winston');

// Configure logging
const logger = winston.createLogger({
  level: 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.json()
  ),
  transports: [
    new winston.transports.File({ filename: 'user-service.log' }),
    new winston.transports.Console()
  ]
});

class UserService {
  constructor() {
    this.app = express();
    this.port = process.env.PORT || 3002;
    
    // Database connections
    this.db = new Pool({
      host: process.env.DB_HOST || 'localhost',
      port: process.env.DB_PORT || 5432,
      database: process.env.DB_NAME || 'geofarm_users',
      user: process.env.DB_USER || 'postgres',
      password: process.env.DB_PASSWORD || 'password',
      ssl: false
    });
    
    this.redis = new Redis({
      host: process.env.REDIS_HOST || 'localhost',
      port: process.env.REDIS_PORT || 6379,
      password: process.env.REDIS_PASSWORD || undefined
    });
    
    // File upload configuration
    this.upload = multer({
      storage: multer.diskStorage({
        destination: './uploads/profiles/',
        filename: (req, file, cb) => {
          cb(null, `${Date.now()}-${file.originalname}`);
        }
      }),
      limits: { fileSize: 5 * 1024 * 1024 }, // 5MB limit
      fileFilter: (req, file, cb) => {
        const allowedTypes = /jpeg|jpg|png|gif/;
        const extname = allowedTypes.test(path.extname(file.originalname).toLowerCase());
        const mimetype = allowedTypes.test(file.mimetype);
        
        if (mimetype && extname) {
          return cb(null, true);
        } else {
          cb(new Error('Only image files are allowed'));
        }
      }
    });
    
    this.setupMiddleware();
    this.setupRoutes();
    this.setupErrorHandling();
    this.initializeDatabase();
  }
  
  setupMiddleware() {
    this.app.use(express.json({ limit: '10mb' }));
    this.app.use(express.urlencoded({ extended: true }));
    this.app.use('/uploads', express.static('uploads'));
  }
  
  setupRoutes() {
    // Authentication routes
    this.app.post('/register', this.register.bind(this));
    this.app.post('/login', this.login.bind(this));
    this.app.post('/logout', this.authenticateToken, this.logout.bind(this));
    this.app.post('/refresh-token', this.refreshToken.bind(this));
    
    // User management routes
    this.app.get('/profile', this.authenticateToken, this.getProfile.bind(this));
    this.app.put('/profile', this.authenticateToken, this.updateProfile.bind(this));
    this.app.post('/profile/avatar', this.authenticateToken, this.upload.single('avatar'), this.uploadAvatar.bind(this));
    
    // User roles and permissions
    this.app.get('/roles', this.authenticateToken, this.getRoles.bind(this));
    this.app.put('/users/:id/role', this.authenticateToken, this.authorizeRole('admin'), this.updateUserRole.bind(this));
    
    // User search and management
    this.app.get('/users', this.authenticateToken, this.authorizeRole('admin'), this.getUsers.bind(this));
    this.app.get('/users/:id', this.authenticateToken, this.getUserById.bind(this));
    this.app.delete('/users/:id', this.authenticateToken, this.authorizeRole('admin'), this.deleteUser.bind(this));
    
    // Password management
    this.app.post('/forgot-password', this.forgotPassword.bind(this));
    this.app.post('/reset-password', this.resetPassword.bind(this));
    this.app.put('/change-password', this.authenticateToken, this.changePassword.bind(this));
    
    // Health check
    this.app.get('/health', (req, res) => {
      res.json({ status: 'healthy', service: 'user-service', timestamp: new Date().toISOString() });
    });
  }
  
  setupErrorHandling() {
    this.app.use((error, req, res, next) => {
      logger.error('Error in user service:', error);
      
      if (error.code === 'LIMIT_FILE_SIZE') {
        return res.status(400).json({ error: 'File size too large' });
      }
      
      if (error.message === 'Only image files are allowed') {
        return res.status(400).json({ error: error.message });
      }
      
      res.status(500).json({ 
        error: 'Internal server error',
        message: process.env.NODE_ENV === 'development' ? error.message : undefined
      });
    });
  }
  
  async initializeDatabase() {
    try {
      await this.db.query(`
        CREATE TABLE IF NOT EXISTS users (
          id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          email VARCHAR(255) UNIQUE NOT NULL,
          password_hash VARCHAR(255) NOT NULL,
          first_name VARCHAR(100) NOT NULL,
          last_name VARCHAR(100) NOT NULL,
          phone VARCHAR(20),
          avatar_url VARCHAR(500),
          role VARCHAR(50) DEFAULT 'farmer',
          is_active BOOLEAN DEFAULT true,
          email_verified BOOLEAN DEFAULT false,
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
      `);
      
      await this.db.query(`
        CREATE TABLE IF NOT EXISTS user_sessions (
          id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          user_id UUID REFERENCES users(id) ON DELETE CASCADE,
          refresh_token VARCHAR(500) NOT NULL,
          expires_at TIMESTAMP NOT NULL,
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          ip_address INET,
          user_agent TEXT
        );
      `);
      
      await this.db.query(`
        CREATE TABLE IF NOT EXISTS password_resets (
          id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          user_id UUID REFERENCES users(id) ON DELETE CASCADE,
          token VARCHAR(500) UNIQUE NOT NULL,
          expires_at TIMESTAMP NOT NULL,
          used BOOLEAN DEFAULT false,
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
      `);
      
      await this.db.query(`
        CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
        CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
        CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON user_sessions(user_id);
        CREATE INDEX IF NOT EXISTS idx_password_resets_token ON password_resets(token);
      `);
      
      logger.info('User service database initialized successfully');
    } catch (error) {
      logger.error('Database initialization error:', error);
      throw error;
    }
  }
  
  authenticateToken(req, res, next) {
    const authHeader = req.headers['authorization'];
    const token = authHeader && authHeader.split(' ')[1];
    
    if (!token) {
      return res.status(401).json({ error: 'Access token required' });
    }
    
    jwt.verify(token, process.env.JWT_SECRET || 'your-secret-key', (error, user) => {
      if (error) {
        return res.status(403).json({ error: 'Invalid or expired token' });
      }
      req.user = user;
      next();
    });
  }
  
  authorizeRole(requiredRole) {
    return (req, res, next) => {
      if (req.user.role !== requiredRole && req.user.role !== 'admin') {
        return res.status(403).json({ error: 'Insufficient permissions' });
      }
      next();
    };
  }
  
  async register(req, res) {
    try {
      const { email, password, firstName, lastName, phone, role = 'farmer' } = req.body;
      
      // Validation
      if (!email || !password || !firstName || !lastName) {
        return res.status(400).json({ error: 'Missing required fields' });
      }
      
      if (password.length < 8) {
        return res.status(400).json({ error: 'Password must be at least 8 characters' });
      }
      
      // Check if user exists
      const existingUser = await this.db.query(
        'SELECT id FROM users WHERE email = $1',
        [email]
      );
      
      if (existingUser.rows.length > 0) {
        return res.status(409).json({ error: 'User already exists' });
      }
      
      // Hash password
      const passwordHash = await bcrypt.hash(password, 12);
      
      // Create user
      const result = await this.db.query(
        `INSERT INTO users (email, password_hash, first_name, last_name, phone, role) 
         VALUES ($1, $2, $3, $4, $5, $6) 
         RETURNING id, email, first_name, last_name, phone, role, created_at`,
        [email, passwordHash, firstName, lastName, phone, role]
      );
      
      const user = result.rows[0];
      
      // Generate tokens
      const accessToken = jwt.sign(
        { userId: user.id, email: user.email, role: user.role },
        process.env.JWT_SECRET || 'your-secret-key',
        { expiresIn: '15m' }
      );
      
      const refreshToken = jwt.sign(
        { userId: user.id },
        process.env.JWT_REFRESH_SECRET || 'your-refresh-secret',
        { expiresIn: '7d' }
      );
      
      // Store refresh token
      await this.db.query(
        'INSERT INTO user_sessions (user_id, refresh_token, expires_at, ip_address, user_agent) VALUES ($1, $2, $3, $4, $5)',
        [
          user.id,
          refreshToken,
          new Date(Date.now() + 7 * 24 * 60 * 60 * 1000),
          req.ip,
          req.headers['user-agent']
        ]
      );
      
      logger.info(`New user registered: ${email}`);
      
      res.status(201).json({
        message: 'User registered successfully',
        user: {
          id: user.id,
          email: user.email,
          firstName: user.first_name,
          lastName: user.last_name,
          phone: user.phone,
          role: user.role,
          createdAt: user.created_at
        },
        accessToken,
        refreshToken
      });
    } catch (error) {
      logger.error('Registration error:', error);
      res.status(500).json({ error: 'Registration failed' });
    }
  }
  
  async login(req, res) {
    try {
      const { email, password } = req.body;
      
      if (!email || !password) {
        return res.status(400).json({ error: 'Email and password required' });
      }
      
      // Find user
      const result = await this.db.query(
        'SELECT id, email, password_hash, first_name, last_name, phone, role, is_active FROM users WHERE email = $1',
        [email]
      );
      
      if (result.rows.length === 0) {
        return res.status(401).json({ error: 'Invalid credentials' });
      }
      
      const user = result.rows[0];
      
      if (!user.is_active) {
        return res.status(401).json({ error: 'Account is deactivated' });
      }
      
      // Verify password
      const isValidPassword = await bcrypt.compare(password, user.password_hash);
      
      if (!isValidPassword) {
        return res.status(401).json({ error: 'Invalid credentials' });
      }
      
      // Generate tokens
      const accessToken = jwt.sign(
        { userId: user.id, email: user.email, role: user.role },
        process.env.JWT_SECRET || 'your-secret-key',
        { expiresIn: '15m' }
      );
      
      const refreshToken = jwt.sign(
        { userId: user.id },
        process.env.JWT_REFRESH_SECRET || 'your-refresh-secret',
        { expiresIn: '7d' }
      );
      
      // Store refresh token
      await this.db.query(
        'INSERT INTO user_sessions (user_id, refresh_token, expires_at, ip_address, user_agent) VALUES ($1, $2, $3, $4, $5)',
        [
          user.id,
          refreshToken,
          new Date(Date.now() + 7 * 24 * 60 * 60 * 1000),
          req.ip,
          req.headers['user-agent']
        ]
      );
      
      // Cache user data in Redis
      await this.redis.setex(
        `user:${user.id}`,
        3600, // 1 hour
        JSON.stringify({
          id: user.id,
          email: user.email,
          firstName: user.first_name,
          lastName: user.last_name,
          phone: user.phone,
          role: user.role
        })
      );
      
      logger.info(`User logged in: ${email}`);
      
      res.json({
        message: 'Login successful',
        user: {
          id: user.id,
          email: user.email,
          firstName: user.first_name,
          lastName: user.last_name,
          phone: user.phone,
          role: user.role
        },
        accessToken,
        refreshToken
      });
    } catch (error) {
      logger.error('Login error:', error);
      res.status(500).json({ error: 'Login failed' });
    }
  }
  
  async logout(req, res) {
    try {
      const refreshToken = req.headers['x-refresh-token'];
      
      if (refreshToken) {
        await this.db.query(
          'DELETE FROM user_sessions WHERE refresh_token = $1',
          [refreshToken]
        );
      }
      
      // Clear Redis cache
      await this.redis.del(`user:${req.user.userId}`);
      
      logger.info(`User logged out: ${req.user.email}`);
      res.json({ message: 'Logged out successfully' });
    } catch (error) {
      logger.error('Logout error:', error);
      res.status(500).json({ error: 'Logout failed' });
    }
  }
  
  async refreshToken(req, res) {
    try {
      const { refreshToken } = req.body;
      
      if (!refreshToken) {
        return res.status(401).json({ error: 'Refresh token required' });
      }
      
      // Verify refresh token
      const decoded = jwt.verify(refreshToken, process.env.JWT_REFRESH_SECRET || 'your-refresh-secret');
      
      // Check if token exists in database
      const result = await this.db.query(
        'SELECT * FROM user_sessions WHERE refresh_token = $1 AND expires_at > NOW()',
        [refreshToken]
      );
      
      if (result.rows.length === 0) {
        return res.status(403).json({ error: 'Invalid refresh token' });
      }
      
      // Get user data
      const userResult = await this.db.query(
        'SELECT id, email, role FROM users WHERE id = $1 AND is_active = true',
        [decoded.userId]
      );
      
      if (userResult.rows.length === 0) {
        return res.status(403).json({ error: 'User not found' });
      }
      
      const user = userResult.rows[0];
      
      // Generate new access token
      const newAccessToken = jwt.sign(
        { userId: user.id, email: user.email, role: user.role },
        process.env.JWT_SECRET || 'your-secret-key',
        { expiresIn: '15m' }
      );
      
      res.json({ accessToken: newAccessToken });
    } catch (error) {
      logger.error('Token refresh error:', error);
      res.status(403).json({ error: 'Invalid refresh token' });
    }
  }
  
  async getProfile(req, res) {
    try {
      // Try to get from Redis cache first
      const cached = await this.redis.get(`user:${req.user.userId}`);
      
      if (cached) {
        return res.json({ profile: JSON.parse(cached) });
      }
      
      const result = await this.db.query(
        'SELECT id, email, first_name, last_name, phone, avatar_url, role, created_at, updated_at FROM users WHERE id = $1',
        [req.user.userId]
      );
      
      if (result.rows.length === 0) {
        return res.status(404).json({ error: 'User not found' });
      }
      
      const user = result.rows[0];
      const profile = {
        id: user.id,
        email: user.email,
        firstName: user.first_name,
        lastName: user.last_name,
        phone: user.phone,
        avatarUrl: user.avatar_url,
        role: user.role,
        createdAt: user.created_at,
        updatedAt: user.updated_at
      };
      
      // Cache for future requests
      await this.redis.setex(`user:${user.id}`, 3600, JSON.stringify(profile));
      
      res.json({ profile });
    } catch (error) {
      logger.error('Get profile error:', error);
      res.status(500).json({ error: 'Failed to get profile' });
    }
  }
  
  async updateProfile(req, res) {
    try {
      const { firstName, lastName, phone } = req.body;
      
      const result = await this.db.query(
        'UPDATE users SET first_name = $1, last_name = $2, phone = $3, updated_at = CURRENT_TIMESTAMP WHERE id = $4 RETURNING *',
        [firstName, lastName, phone, req.user.userId]
      );
      
      if (result.rows.length === 0) {
        return res.status(404).json({ error: 'User not found' });
      }
      
      const user = result.rows[0];
      
      // Clear Redis cache
      await this.redis.del(`user:${req.user.userId}`);
      
      res.json({
        message: 'Profile updated successfully',
        profile: {
          id: user.id,
          email: user.email,
          firstName: user.first_name,
          lastName: user.last_name,
          phone: user.phone,
          avatarUrl: user.avatar_url,
          role: user.role
        }
      });
    } catch (error) {
      logger.error('Update profile error:', error);
      res.status(500).json({ error: 'Failed to update profile' });
    }
  }
  
  async uploadAvatar(req, res) {
    try {
      if (!req.file) {
        return res.status(400).json({ error: 'No file uploaded' });
      }
      
      const avatarUrl = `/uploads/profiles/${req.file.filename}`;
      
      await this.db.query(
        'UPDATE users SET avatar_url = $1, updated_at = CURRENT_TIMESTAMP WHERE id = $2',
        [avatarUrl, req.user.userId]
      );
      
      // Clear Redis cache
      await this.redis.del(`user:${req.user.userId}`);
      
      res.json({
        message: 'Avatar uploaded successfully',
        avatarUrl
      });
    } catch (error) {
      logger.error('Avatar upload error:', error);
      res.status(500).json({ error: 'Failed to upload avatar' });
    }
  }
  
  async getRoles(req, res) {
    try {
      const roles = ['admin', 'farmer', 'agronomist', 'researcher', 'technician'];
      res.json({ roles });
    } catch (error) {
      logger.error('Get roles error:', error);
      res.status(500).json({ error: 'Failed to get roles' });
    }
  }
  
  async updateUserRole(req, res) {
    try {
      const { role } = req.body;
      const userId = req.params.id;
      
      const validRoles = ['admin', 'farmer', 'agronomist', 'researcher', 'technician'];
      
      if (!validRoles.includes(role)) {
        return res.status(400).json({ error: 'Invalid role' });
      }
      
      const result = await this.db.query(
        'UPDATE users SET role = $1, updated_at = CURRENT_TIMESTAMP WHERE id = $2 RETURNING id, email, first_name, last_name, role',
        [role, userId]
      );
      
      if (result.rows.length === 0) {
        return res.status(404).json({ error: 'User not found' });
      }
      
      const user = result.rows[0];
      
      // Clear Redis cache
      await this.redis.del(`user:${userId}`);
      
      res.json({
        message: 'User role updated successfully',
        user: {
          id: user.id,
          email: user.email,
          firstName: user.first_name,
          lastName: user.last_name,
          role: user.role
        }
      });
    } catch (error) {
      logger.error('Update user role error:', error);
      res.status(500).json({ error: 'Failed to update user role' });
    }
  }
  
  async getUsers(req, res) {
    try {
      const { page = 1, limit = 10, search = '', role = '' } = req.query;
      const offset = (page - 1) * limit;
      
      let query = 'SELECT id, email, first_name, last_name, phone, role, is_active, created_at FROM users WHERE 1=1';
      let params = [];
      let paramCount = 0;
      
      if (search) {
        paramCount++;
        query += ` AND (email ILIKE $${paramCount} OR first_name ILIKE $${paramCount} OR last_name ILIKE $${paramCount})`;
        params.push(`%${search}%`);
      }
      
      if (role) {
        paramCount++;
        query += ` AND role = $${paramCount}`;
        params.push(role);
      }
      
      paramCount++;
      query += ` ORDER BY created_at DESC LIMIT $${paramCount}`;
      params.push(limit);
      
      paramCount++;
      query += ` OFFSET $${paramCount}`;
      params.push(offset);
      
      const result = await this.db.query(query, params);
      
      // Get total count
      let countQuery = 'SELECT COUNT(*) FROM users WHERE 1=1';
      let countParams = [];
      let countParamCount = 0;
      
      if (search) {
        countParamCount++;
        countQuery += ` AND (email ILIKE $${countParamCount} OR first_name ILIKE $${countParamCount} OR last_name ILIKE $${countParamCount})`;
        countParams.push(`%${search}%`);
      }
      
      if (role) {
        countParamCount++;
        countQuery += ` AND role = $${countParamCount}`;
        countParams.push(role);
      }
      
      const countResult = await this.db.query(countQuery, countParams);
      const totalUsers = parseInt(countResult.rows[0].count);
      
      const users = result.rows.map(user => ({
        id: user.id,
        email: user.email,
        firstName: user.first_name,
        lastName: user.last_name,
        phone: user.phone,
        role: user.role,
        isActive: user.is_active,
        createdAt: user.created_at
      }));
      
      res.json({
        users,
        pagination: {
          page: parseInt(page),
          limit: parseInt(limit),
          totalUsers,
          totalPages: Math.ceil(totalUsers / limit)
        }
      });
    } catch (error) {
      logger.error('Get users error:', error);
      res.status(500).json({ error: 'Failed to get users' });
    }
  }
  
  async getUserById(req, res) {
    try {
      const userId = req.params.id;
      
      // Users can only view their own profile unless they're admin
      if (req.user.role !== 'admin' && req.user.userId !== userId) {
        return res.status(403).json({ error: 'Access denied' });
      }
      
      const result = await this.db.query(
        'SELECT id, email, first_name, last_name, phone, avatar_url, role, is_active, created_at FROM users WHERE id = $1',
        [userId]
      );
      
      if (result.rows.length === 0) {
        return res.status(404).json({ error: 'User not found' });
      }
      
      const user = result.rows[0];
      
      res.json({
        user: {
          id: user.id,
          email: user.email,
          firstName: user.first_name,
          lastName: user.last_name,
          phone: user.phone,
          avatarUrl: user.avatar_url,
          role: user.role,
          isActive: user.is_active,
          createdAt: user.created_at
        }
      });
    } catch (error) {
      logger.error('Get user by ID error:', error);
      res.status(500).json({ error: 'Failed to get user' });
    }
  }
  
  async deleteUser(req, res) {
    try {
      const userId = req.params.id;
      
      const result = await this.db.query(
        'DELETE FROM users WHERE id = $1 RETURNING id',
        [userId]
      );
      
      if (result.rows.length === 0) {
        return res.status(404).json({ error: 'User not found' });
      }
      
      // Clear Redis cache
      await this.redis.del(`user:${userId}`);
      
      // Delete all sessions
      await this.db.query('DELETE FROM user_sessions WHERE user_id = $1', [userId]);
      
      res.json({ message: 'User deleted successfully' });
    } catch (error) {
      logger.error('Delete user error:', error);
      res.status(500).json({ error: 'Failed to delete user' });
    }
  }
  
  async forgotPassword(req, res) {
    try {
      const { email } = req.body;
      
      const result = await this.db.query(
        'SELECT id, email FROM users WHERE email = $1 AND is_active = true',
        [email]
      );
      
      if (result.rows.length === 0) {
        // Don't reveal if email exists
        return res.json({ message: 'If the email exists, a reset link has been sent' });
      }
      
      const user = result.rows[0];
      
      // Generate reset token
      const resetToken = jwt.sign(
        { userId: user.id },
        process.env.JWT_RESET_SECRET || 'your-reset-secret',
        { expiresIn: '1h' }
      );
      
      // Store reset token
      await this.db.query(
        'INSERT INTO password_resets (user_id, token, expires_at) VALUES ($1, $2, $3)',
        [user.id, resetToken, new Date(Date.now() + 60 * 60 * 1000)]
      );
      
      // In a real implementation, send email with reset link
      logger.info(`Password reset requested for: ${email}, token: ${resetToken}`);
      
      res.json({ message: 'If the email exists, a reset link has been sent' });
    } catch (error) {
      logger.error('Forgot password error:', error);
      res.status(500).json({ error: 'Failed to process password reset' });
    }
  }
  
  async resetPassword(req, res) {
    try {
      const { token, newPassword } = req.body;
      
      if (!token || !newPassword) {
        return res.status(400).json({ error: 'Token and new password required' });
      }
      
      if (newPassword.length < 8) {
        return res.status(400).json({ error: 'Password must be at least 8 characters' });
      }
      
      // Verify token
      const decoded = jwt.verify(token, process.env.JWT_RESET_SECRET || 'your-reset-secret');
      
      // Check if token exists and is valid
      const result = await this.db.query(
        'SELECT * FROM password_resets WHERE token = $1 AND expires_at > NOW() AND used = false',
        [token]
      );
      
      if (result.rows.length === 0) {
        return res.status(400).json({ error: 'Invalid or expired reset token' });
      }
      
      const resetRecord = result.rows[0];
      
      // Hash new password
      const passwordHash = await bcrypt.hash(newPassword, 12);
      
      // Update password
      await this.db.query(
        'UPDATE users SET password_hash = $1, updated_at = CURRENT_TIMESTAMP WHERE id = $2',
        [passwordHash, decoded.userId]
      );
      
      // Mark token as used
      await this.db.query(
        'UPDATE password_resets SET used = true WHERE id = $1',
        [resetRecord.id]
      );
      
      // Clear all sessions for security
      await this.db.query('DELETE FROM user_sessions WHERE user_id = $1', [decoded.userId]);
      
      logger.info(`Password reset completed for user: ${decoded.userId}`);
      
      res.json({ message: 'Password reset successfully' });
    } catch (error) {
      logger.error('Reset password error:', error);
      res.status(500).json({ error: 'Failed to reset password' });
    }
  }
  
  async changePassword(req, res) {
    try {
      const { currentPassword, newPassword } = req.body;
      
      if (!currentPassword || !newPassword) {
        return res.status(400).json({ error: 'Current and new password required' });
      }
      
      if (newPassword.length < 8) {
        return res.status(400).json({ error: 'New password must be at least 8 characters' });
      }
      
      // Get current password hash
      const result = await this.db.query(
        'SELECT password_hash FROM users WHERE id = $1',
        [req.user.userId]
      );
      
      if (result.rows.length === 0) {
        return res.status(404).json({ error: 'User not found' });
      }
      
      const currentHash = result.rows[0].password_hash;
      
      // Verify current password
      const isValidPassword = await bcrypt.compare(currentPassword, currentHash);
      
      if (!isValidPassword) {
        return res.status(400).json({ error: 'Current password is incorrect' });
      }
      
      // Hash new password
      const newPasswordHash = await bcrypt.hash(newPassword, 12);
      
      // Update password
      await this.db.query(
        'UPDATE users SET password_hash = $1, updated_at = CURRENT_TIMESTAMP WHERE id = $2',
        [newPasswordHash, req.user.userId]
      );
      
      // Clear all sessions for security (force re-login)
      await this.db.query('DELETE FROM user_sessions WHERE user_id = $1', [req.user.userId]);
      
      // Clear Redis cache
      await this.redis.del(`user:${req.user.userId}`);
      
      logger.info(`Password changed for user: ${req.user.userId}`);
      
      res.json({ message: 'Password changed successfully' });
    } catch (error) {
      logger.error('Change password error:', error);
      res.status(500).json({ error: 'Failed to change password' });
    }
  }
  
  start() {
    this.app.listen(this.port, () => {
      logger.info(`User service running on port ${this.port}`);
    });
  }
}

// Start the service
if (require.main === module) {
  const userService = new UserService();
  userService.start();
}

module.exports = UserService;