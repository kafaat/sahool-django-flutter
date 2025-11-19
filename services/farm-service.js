const express = require('express');
const { Pool } = require('pg');
const Redis = require('ioredis');
const winston = require('winston');

// Configure logging
const logger = winston.createLogger({
  level: 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.json()
  ),
  transports: [
    new winston.transports.File({ filename: 'farm-service.log' }),
    new winston.transports.Console()
  ]
});

class FarmService {
  constructor() {
    this.app = express();
    this.port = process.env.PORT || 3008;
    
    // Database connections
    this.db = new Pool({
      host: process.env.DB_HOST || 'localhost',
      port: process.env.DB_PORT || 5432,
      database: process.env.DB_NAME || 'geofarm_farms',
      user: process.env.DB_USER || 'postgres',
      password: process.env.DB_PASSWORD || 'password',
      ssl: false
    });
    
    this.redis = new Redis({
      host: process.env.REDIS_HOST || 'localhost',
      port: process.env.REDIS_PORT || 6379,
      password: process.env.REDIS_PASSWORD || undefined
    });
    
    this.setupMiddleware();
    this.setupRoutes();
    this.setupErrorHandling();
    this.initializeDatabase();
  }
  
  setupMiddleware() {
    this.app.use(express.json({ limit: '10mb' }));
    this.app.use(express.urlencoded({ extended: true }));
  }
  
  setupRoutes() {
    // Farm management
    this.app.get('/farms', this.getFarms.bind(this));
    this.app.post('/farms', this.createFarm.bind(this));
    this.app.get('/farms/:id', this.getFarmById.bind(this));
    this.app.put('/farms/:id', this.updateFarm.bind(this));
    this.app.delete('/farms/:id', this.deleteFarm.bind(this));
    
    // Field management
    this.app.get('/fields', this.getFields.bind(this));
    this.app.post('/fields', this.createField.bind(this));
    this.app.get('/fields/:id', this.getFieldById.bind(this));
    this.app.put('/fields/:id', this.updateField.bind(this));
    this.app.delete('/fields/:id', this.deleteField.bind(this));
    
    // Crop management
    this.app.get('/crops', this.getCrops.bind(this));
    this.app.post('/crops', this.createCrop.bind(this));
    this.app.get('/crops/:id', this.getCropById.bind(this));
    this.app.put('/crops/:id', this.updateCrop.bind(this));
    this.app.delete('/crops/:id', this.deleteCrop.bind(this));
    
    // Analytics
    this.app.get('/analytics', this.getFarmAnalytics.bind(this));
    this.app.get('/summary', this.getFarmSummary.bind(this));
    
    // Health check
    this.app.get('/health', (req, res) => {
      res.json({ 
        status: 'healthy', 
        service: 'farm-service', 
        timestamp: new Date().toISOString()
      });
    });
  }
  
  setupErrorHandling() {
    this.app.use((error, req, res, next) => {
      logger.error('Error in farm service:', error);
      res.status(500).json({ 
        error: 'Internal server error',
        message: process.env.NODE_ENV === 'development' ? error.message : undefined
      });
    });
  }
  
  async initializeDatabase() {
    try {
      await this.db.query(`
        CREATE TABLE IF NOT EXISTS farms (
          id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          name VARCHAR(200) NOT NULL,
          owner_id UUID NOT NULL,
          location JSONB NOT NULL,
          total_area DECIMAL(10, 2) NOT NULL,
          address TEXT,
          timezone VARCHAR(50) DEFAULT 'UTC',
          soil_type VARCHAR(50),
          climate_zone VARCHAR(50),
          is_active BOOLEAN DEFAULT true,
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
      `);
      
      await this.db.query(`
        CREATE TABLE IF NOT EXISTS fields (
          id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          farm_id UUID REFERENCES farms(id) ON DELETE CASCADE,
          name VARCHAR(100) NOT NULL,
          area DECIMAL(8, 2) NOT NULL,
          coordinates JSONB DEFAULT '{}',
          soil_type VARCHAR(50),
          irrigation_type VARCHAR(50),
          drainage_quality VARCHAR(20),
          is_active BOOLEAN DEFAULT true,
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
      `);
      
      await this.db.query(`
        CREATE TABLE IF NOT EXISTS field_crops (
          id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          field_id UUID REFERENCES fields(id) ON DELETE CASCADE,
          crop_id UUID NOT NULL,
          variety VARCHAR(100),
          planting_date DATE,
          expected_harvest_date DATE,
          planting_method VARCHAR(50),
          seed_rate DECIMAL(8, 2),
          spacing_row DECIMAL(5, 2),
          spacing_plant DECIMAL(5, 2),
          current_stage VARCHAR(50),
          health_status VARCHAR(20) DEFAULT 'healthy',
          estimated_yield DECIMAL(10, 2),
          status VARCHAR(20) DEFAULT 'active',
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
      `);
      
      await this.db.query(`
        CREATE INDEX IF NOT EXISTS idx_farms_owner ON farms(owner_id);
        CREATE INDEX IF NOT EXISTS idx_farms_location ON farms USING GIN(location);
        CREATE INDEX IF NOT EXISTS idx_fields_farm ON fields(farm_id);
        CREATE INDEX IF NOT EXISTS idx_field_crops_field ON field_crops(field_id);
        CREATE INDEX IF NOT EXISTS idx_field_crops_crop ON field_crops(crop_id);
      `);
      
      logger.info('Farm service database initialized successfully');
    } catch (error) {
      logger.error('Database initialization error:', error);
      throw error;
    }
  }
  
  async getFarms(req, res) {
    try {
      const { ownerId, limit = 20, offset = 0 } = req.query;
      
      let query = 'SELECT * FROM farms WHERE 1=1';
      let params = [];
      
      if (ownerId) {
        query += ' AND owner_id = $1';
        params.push(ownerId);
      }
      
      query += ' ORDER BY created_at DESC LIMIT $' + (params.length + 1) + ' OFFSET $' + (params.length + 2);
      params.push(limit, offset);
      
      const result = await this.db.query(query, params);
      
      const farms = result.rows.map(farm => ({
        id: farm.id,
        name: farm.name,
        ownerId: farm.owner_id,
        location: farm.location,
        totalArea: farm.total_area,
        address: farm.address,
        timezone: farm.timezone,
        soilType: farm.soil_type,
        climateZone: farm.climate_zone,
        isActive: farm.is_active,
        createdAt: farm.created_at,
        updatedAt: farm.updated_at
      }));
      
      res.json({ farms });
    } catch (error) {
      logger.error('Get farms error:', error);
      res.status(500).json({ error: 'Failed to get farms' });
    }
  }
  
  async createFarm(req, res) {
    try {
      const { name, ownerId, location, totalArea, address, timezone, soilType, climateZone } = req.body;
      
      if (!name || !ownerId || !location || !totalArea) {
        return res.status(400).json({ error: 'Missing required farm fields' });
      }
      
      const result = await this.db.query(
        'INSERT INTO farms (name, owner_id, location, total_area, address, timezone, soil_type, climate_zone) VALUES ($1, $2, $3, $4, $5, $6, $7, $8) RETURNING *',
        [name, ownerId, JSON.stringify(location), totalArea, address, timezone, soilType, climateZone]
      );
      
      logger.info(`New farm created: ${name} by owner ${ownerId}`);
      
      res.status(201).json({
        message: 'Farm created successfully',
        farm: result.rows[0]
      });
    } catch (error) {
      logger.error('Create farm error:', error);
      res.status(500).json({ error: 'Failed to create farm' });
    }
  }
  
  async getFarmById(req, res) {
    try {
      const farmId = req.params.id;
      
      const result = await this.db.query('SELECT * FROM farms WHERE id = $1', [farmId]);
      
      if (result.rows.length === 0) {
        return res.status(404).json({ error: 'Farm not found' });
      }
      
      const farm = result.rows[0];
      
      res.json({
        farm: {
          id: farm.id,
          name: farm.name,
          ownerId: farm.owner_id,
          location: farm.location,
          totalArea: farm.total_area,
          address: farm.address,
          timezone: farm.timezone,
          soilType: farm.soil_type,
          climateZone: farm.climate_zone,
          isActive: farm.is_active,
          createdAt: farm.created_at,
          updatedAt: farm.updated_at
        }
      });
    } catch (error) {
      logger.error('Get farm by ID error:', error);
      res.status(500).json({ error: 'Failed to get farm' });
    }
  }
  
  async updateFarm(req, res) {
    try {
      const farmId = req.params.id;
      const { name, location, totalArea, address, timezone, soilType, climateZone } = req.body;
      
      const result = await this.db.query(
        'UPDATE farms SET name = $1, location = $2, total_area = $3, address = $4, timezone = $5, soil_type = $6, climate_zone = $7, updated_at = CURRENT_TIMESTAMP WHERE id = $8 RETURNING *',
        [name, JSON.stringify(location), totalArea, address, timezone, soilType, climateZone, farmId]
      );
      
      if (result.rows.length === 0) {
        return res.status(404).json({ error: 'Farm not found' });
      }
      
      res.json({
        message: 'Farm updated successfully',
        farm: result.rows[0]
      });
    } catch (error) {
      logger.error('Update farm error:', error);
      res.status(500).json({ error: 'Failed to update farm' });
    }
  }
  
  async deleteFarm(req, res) {
    try {
      const farmId = req.params.id;
      
      const result = await this.db.query('DELETE FROM farms WHERE id = $1 RETURNING id', [farmId]);
      
      if (result.rows.length === 0) {
        return res.status(404).json({ error: 'Farm not found' });
      }
      
      res.json({ message: 'Farm deleted successfully' });
    } catch (error) {
      logger.error('Delete farm error:', error);
      res.status(500).json({ error: 'Failed to delete farm' });
    }
  }
  
  async getFields(req, res) {
    try {
      const { farmId, limit = 20, offset = 0 } = req.query;
      
      let query = 'SELECT * FROM fields WHERE 1=1';
      let params = [];
      
      if (farmId) {
        query += ' AND farm_id = $1';
        params.push(farmId);
      }
      
      query += ' ORDER BY created_at DESC LIMIT $' + (params.length + 1) + ' OFFSET $' + (params.length + 2);
      params.push(limit, offset);
      
      const result = await this.db.query(query, params);
      
      const fields = result.rows.map(field => ({
        id: field.id,
        farmId: field.farm_id,
        name: field.name,
        area: field.area,
        coordinates: field.coordinates,
        soilType: field.soil_type,
        irrigationType: field.irrigation_type,
        drainageQuality: field.drainage_quality,
        isActive: field.is_active,
        createdAt: field.created_at,
        updatedAt: field.updated_at
      }));
      
      res.json({ fields });
    } catch (error) {
      logger.error('Get fields error:', error);
      res.status(500).json({ error: 'Failed to get fields' });
    }
  }
  
  async createField(req, res) {
    try {
      const { farmId, name, area, coordinates, soilType, irrigationType, drainageQuality } = req.body;
      
      if (!farmId || !name || !area) {
        return res.status(400).json({ error: 'Missing required field fields' });
      }
      
      const result = await this.db.query(
        'INSERT INTO fields (farm_id, name, area, coordinates, soil_type, irrigation_type, drainage_quality) VALUES ($1, $2, $3, $4, $5, $6, $7) RETURNING *',
        [farmId, name, area, JSON.stringify(coordinates || {}), soilType, irrigationType, drainageQuality]
      );
      
      logger.info(`New field created: ${name} in farm ${farmId}`);
      
      res.status(201).json({
        message: 'Field created successfully',
        field: result.rows[0]
      });
    } catch (error) {
      logger.error('Create field error:', error);
      res.status(500).json({ error: 'Failed to create field' });
    }
  }
  
  async getFieldById(req, res) {
    try {
      const fieldId = req.params.id;
      
      const result = await this.db.query('SELECT * FROM fields WHERE id = $1', [fieldId]);
      
      if (result.rows.length === 0) {
        return res.status(404).json({ error: 'Field not found' });
      }
      
      const field = result.rows[0];
      
      res.json({
        field: {
          id: field.id,
          farmId: field.farm_id,
          name: field.name,
          area: field.area,
          coordinates: field.coordinates,
          soilType: field.soil_type,
          irrigationType: field.irrigation_type,
          drainageQuality: field.drainage_quality,
          isActive: field.is_active,
          createdAt: field.created_at,
          updatedAt: field.updated_at
        }
      });
    } catch (error) {
      logger.error('Get field by ID error:', error);
      res.status(500).json({ error: 'Failed to get field' });
    }
  }
  
  async updateField(req, res) {
    try {
      const fieldId = req.params.id;
      const { name, area, coordinates, soilType, irrigationType, drainageQuality } = req.body;
      
      const result = await this.db.query(
        'UPDATE fields SET name = $1, area = $2, coordinates = $3, soil_type = $4, irrigation_type = $5, drainage_quality = $6, updated_at = CURRENT_TIMESTAMP WHERE id = $7 RETURNING *',
        [name, area, JSON.stringify(coordinates || {}), soilType, irrigationType, drainageQuality, fieldId]
      );
      
      if (result.rows.length === 0) {
        return res.status(404).json({ error: 'Field not found' });
      }
      
      res.json({
        message: 'Field updated successfully',
        field: result.rows[0]
      });
    } catch (error) {
      logger.error('Update field error:', error);
      res.status(500).json({ error: 'Failed to update field' });
    }
  }
  
  async deleteField(req, res) {
    try {
      const fieldId = req.params.id;
      
      const result = await this.db.query('DELETE FROM fields WHERE id = $1 RETURNING id', [fieldId]);
      
      if (result.rows.length === 0) {
        return res.status(404).json({ error: 'Field not found' });
      }
      
      res.json({ message: 'Field deleted successfully' });
    } catch (error) {
      logger.error('Delete field error:', error);
      res.status(500).json({ error: 'Failed to delete field' });
    }
  }
  
  async getCrops(req, res) {
    try {
      const { fieldId, status = 'active', limit = 20, offset = 0 } = req.query;
      
      let query = `
        SELECT fc.*, c.name as crop_name, c.scientific_name
        FROM field_crops fc
        JOIN crops c ON fc.crop_id = c.id
        WHERE 1=1
      `;
      let params = [];
      let paramCount = 0;
      
      if (fieldId) {
        paramCount++;
        query += ` AND fc.field_id = $${paramCount}`;
        params.push(fieldId);
      }
      
      if (status) {
        paramCount++;
        query += ` AND fc.status = $${paramCount}`;
        params.push(status);
      }
      
      paramCount++;
      query += ` ORDER BY fc.created_at DESC LIMIT $${paramCount}`;
      params.push(limit);
      
      paramCount++;
      query += ` OFFSET $${paramCount}`;
      params.push(offset);
      
      const result = await this.db.query(query, params);
      
      const crops = result.rows.map(crop => ({
        id: crop.id,
        fieldId: crop.field_id,
        cropId: crop.crop_id,
        cropName: crop.crop_name,
        scientificName: crop.scientific_name,
        variety: crop.variety,
        plantingDate: crop.planting_date,
        expectedHarvestDate: crop.expected_harvest_date,
        plantingMethod: crop.planting_method,
        seedRate: crop.seed_rate,
        spacingRow: crop.spacing_row,
        spacingPlant: crop.spacing_plant,
        currentStage: crop.current_stage,
        healthStatus: crop.health_status,
        estimatedYield: crop.estimated_yield,
        status: crop.status,
        createdAt: crop.created_at,
        updatedAt: crop.updated_at
      }));
      
      res.json({ crops });
    } catch (error) {
      logger.error('Get crops error:', error);
      res.status(500).json({ error: 'Failed to get crops' });
    }
  }
  
  async createCrop(req, res) {
    try {
      const { fieldId, cropId, variety, plantingDate, expectedHarvestDate, plantingMethod, seedRate, spacingRow, spacingPlant, currentStage, estimatedYield } = req.body;
      
      if (!fieldId || !cropId) {
        return res.status(400).json({ error: 'Field ID and Crop ID are required' });
      }
      
      const result = await this.db.query(
        'INSERT INTO field_crops (field_id, crop_id, variety, planting_date, expected_harvest_date, planting_method, seed_rate, spacing_row, spacing_plant, current_stage, estimated_yield) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11) RETURNING *',
        [fieldId, cropId, variety, plantingDate, expectedHarvestDate, plantingMethod, seedRate, spacingRow, spacingPlant, currentStage, estimatedYield]
      );
      
      logger.info(`New crop created in field ${fieldId}: ${cropId}`);
      
      res.status(201).json({
        message: 'Crop created successfully',
        crop: result.rows[0]
      });
    } catch (error) {
      logger.error('Create crop error:', error);
      res.status(500).json({ error: 'Failed to create crop' });
    }
  }
  
  async getCropById(req, res) {
    try {
      const cropId = req.params.id;
      
      const result = await this.db.query(`
        SELECT fc.*, c.name as crop_name, c.scientific_name
        FROM field_crops fc
        JOIN crops c ON fc.crop_id = c.id
        WHERE fc.id = $1
      `, [cropId]);
      
      if (result.rows.length === 0) {
        return res.status(404).json({ error: 'Crop not found' });
      }
      
      const crop = result.rows[0];
      
      res.json({
        crop: {
          id: crop.id,
          fieldId: crop.field_id,
          cropId: crop.crop_id,
          cropName: crop.crop_name,
          scientificName: crop.scientific_name,
          variety: crop.variety,
          plantingDate: crop.planting_date,
          expectedHarvestDate: crop.expected_harvest_date,
          plantingMethod: crop.planting_method,
          seedRate: crop.seed_rate,
          spacingRow: crop.spacing_row,
          spacingPlant: crop.spacing_plant,
          currentStage: crop.current_stage,
          healthStatus: crop.health_status,
          estimatedYield: crop.estimated_yield,
          status: crop.status,
          createdAt: crop.created_at,
          updatedAt: crop.updated_at
        }
      });
    } catch (error) {
      logger.error('Get crop by ID error:', error);
      res.status(500).json({ error: 'Failed to get crop' });
    }
  }
  
  async updateCrop(req, res) {
    try {
      const cropId = req.params.id;
      const { variety, plantingDate, expectedHarvestDate, plantingMethod, seedRate, spacingRow, spacingPlant, currentStage, healthStatus, estimatedYield, status } = req.body;
      
      const result = await this.db.query(
        'UPDATE field_crops SET variety = $1, planting_date = $2, expected_harvest_date = $3, planting_method = $4, seed_rate = $5, spacing_row = $6, spacing_plant = $7, current_stage = $8, health_status = $9, estimated_yield = $10, status = $11, updated_at = CURRENT_TIMESTAMP WHERE id = $12 RETURNING *',
        [variety, plantingDate, expectedHarvestDate, plantingMethod, seedRate, spacingRow, spacingPlant, currentStage, healthStatus, estimatedYield, status, cropId]
      );
      
      if (result.rows.length === 0) {
        return res.status(404).json({ error: 'Crop not found' });
      }
      
      res.json({
        message: 'Crop updated successfully',
        crop: result.rows[0]
      });
    } catch (error) {
      logger.error('Update crop error:', error);
      res.status(500).json({ error: 'Failed to update crop' });
    }
  }
  
  async deleteCrop(req, res) {
    try {
      const cropId = req.params.id;
      
      const result = await this.db.query('DELETE FROM field_crops WHERE id = $1 RETURNING id', [cropId]);
      
      if (result.rows.length === 0) {
        return res.status(404).json({ error: 'Crop not found' });
      }
      
      res.json({ message: 'Crop deleted successfully' });
    } catch (error) {
      logger.error('Delete crop error:', error);
      res.status(500).json({ error: 'Failed to delete crop' });
    }
  }
  
  async getFarmAnalytics(req, res) {
    try {
      const { farmId, period = '30days' } = req.query;
      
      let days = 30;
      if (period === '7days') days = 7;
      else if (period === '90days') days = 90;
      else if (period === '365days') days = 365;
      
      // Farm statistics
      const farmStats = await this.db.query(`
        SELECT 
          COUNT(DISTINCT f.id) as total_farms,
          SUM(f.total_area) as total_area,
          COUNT(DISTINCT fi.id) as total_fields,
          COUNT(DISTINCT fc.id) as active_crops
        FROM farms f
        LEFT JOIN fields fi ON f.id = fi.farm_id
        LEFT JOIN field_crops fc ON fi.id = fc.field_id AND fc.status = 'active'
        WHERE f.created_at >= NOW() - INTERVAL '${days} days'
        ${farmId ? 'AND f.id = $1' : ''}
      `, farmId ? [farmId] : []);
      
      // Crop distribution
      const cropDistribution = await this.db.query(`
        SELECT c.name, COUNT(fc.id) as count
        FROM field_crops fc
        JOIN crops c ON fc.crop_id = c.id
        WHERE fc.created_at >= NOW() - INTERVAL '${days} days'
        ${farmId ? 'AND fc.field_id IN (SELECT id FROM fields WHERE farm_id = $1)' : ''}
        GROUP BY c.name
      `, farmId ? [farmId] : []);
      
      res.json({
        period,
        farmStats: farmStats.rows[0],
        cropDistribution: cropDistribution.rows
      });
    } catch (error) {
      logger.error('Get farm analytics error:', error);
      res.status(500).json({ error: 'Failed to get farm analytics' });
    }
  }
  
  async getFarmSummary(req, res) {
    try {
      const { farmId } = req.query;
      
      // Total counts
      const totalCounts = await this.db.query(`
        SELECT 
          COUNT(DISTINCT f.id) as total_farms,
          COUNT(DISTINCT fi.id) as total_fields,
          COUNT(DISTINCT fc.id) as total_crops,
          SUM(f.total_area) as total_area
        FROM farms f
        LEFT JOIN fields fi ON f.id = fi.farm_id
        LEFT JOIN field_crops fc ON fi.id = fc.field_id
        WHERE 1=1
        ${farmId ? 'AND f.id = $1' : ''}
      `, farmId ? [farmId] : []);
      
      // Recent activity
      const recentActivity = await this.db.query(`
        SELECT 'farm' as type, id, name, created_at FROM farms
        WHERE created_at >= NOW() - INTERVAL '7 days'
        ${farmId ? 'AND id = $1' : ''}
        UNION ALL
        SELECT 'field' as type, id, name, created_at FROM fields
        WHERE created_at >= NOW() - INTERVAL '7 days'
        ${farmId ? 'AND farm_id = $1' : ''}
        UNION ALL
        SELECT 'crop' as type, fc.id, c.name, fc.created_at FROM field_crops fc
        JOIN crops c ON fc.crop_id = c.id
        WHERE fc.created_at >= NOW() - INTERVAL '7 days'
        ${farmId ? 'AND fc.field_id IN (SELECT id FROM fields WHERE farm_id = $1)' : ''}
        ORDER BY created_at DESC
        LIMIT 10
      `, farmId ? [farmId] : []);
      
      res.json({
        summary: totalCounts.rows[0],
        recentActivity: recentActivity.rows
      });
    } catch (error) {
      logger.error('Get farm summary error:', error);
      res.status(500).json({ error: 'Failed to get farm summary' });
    }
  }
  
  start() {
    this.app.listen(this.port, () => {
      logger.info(`Farm service running on port ${this.port}`);
    });
  }
}

// Start the service
if (require.main === module) {
  const farmService = new FarmService();
  farmService.start();
}

module.exports = FarmService;