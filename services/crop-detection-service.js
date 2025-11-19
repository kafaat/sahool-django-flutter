const express = require('express');
const { Pool } = require('pg');
const Redis = require('ioredis');
const multer = require('multer');
const axios = require('axios');
const winston = require('winston');
const sharp = require('sharp');
const path = require('path');

// Configure logging
const logger = winston.createLogger({
  level: 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.json()
  ),
  transports: [
    new winston.transports.File({ filename: 'crop-detection-service.log' }),
    new winston.transports.Console()
  ]
});

class CropDetectionService {
  constructor() {
    this.app = express();
    this.port = process.env.PORT || 3006;
    
    // Database connections
    this.db = new Pool({
      host: process.env.DB_HOST || 'localhost',
      port: process.env.DB_PORT || 5432,
      database: process.env.DB_NAME || 'geofarm_crops',
      user: process.env.DB_USER || 'postgres',
      password: process.env.DB_PASSWORD || 'password',
      ssl: false
    });
    
    this.redis = new Redis({
      host: process.env.REDIS_HOST || 'localhost',
      port: process.env.REDIS_PORT || 6379,
      password: process.env.REDIS_PASSWORD || undefined
    });
    
    // AI Model API configuration
    this.aiModelUrl = process.env.AI_MODEL_URL || 'http://ai-model-service:5000';
    
    // File upload configuration
    this.upload = multer({
      storage: multer.diskStorage({
        destination: './uploads/crops/',
        filename: (req, file, cb) => {
          cb(null, `${Date.now()}-${file.originalname}`);
        }
      }),
      limits: { fileSize: 10 * 1024 * 1024 }, // 10MB limit
      fileFilter: (req, file, cb) => {
        const allowedTypes = /jpeg|jpg|png|gif|bmp|tiff|webp/;
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
    // Crop detection
    this.app.post('/detect', this.upload.single('image'), this.detectCrops.bind(this));
    this.app.post('/detect/batch', this.upload.array('images', 10), this.detectBatchCrops.bind(this));
    
    // Crop health analysis
    this.app.post('/health-analysis', this.upload.single('image'), this.analyzeCropHealth.bind(this));
    this.app.post('/disease-detection', this.upload.single('image'), this.detectDisease.bind(this));
    
    // Crop counting and measurement
    this.app.post('/count', this.upload.single('image'), this.countCrops.bind(this));
    this.app.post('/measure', this.upload.single('image'), this.measureCrops.bind(this));
    
    // Growth stage detection
    this.app.post('/growth-stage', this.upload.single('image'), this.detectGrowthStage.bind(this));
    this.app.get('/growth-stages', this.getGrowthStages.bind(this));
    
    // Field analysis
    this.app.post('/field-analysis', this.upload.single('image'), this.analyzeField.bind(this));
    this.app.post('/field-monitoring', this.upload.array('images', 20), this.monitorField.bind(this));
    
    // Historical analysis
    this.app.get('/analysis-history', this.getAnalysisHistory.bind(this));
    this.app.get('/analysis/:id', this.getAnalysisResult.bind(this));
    
    // Crop database
    this.app.get('/crops', this.getCrops.bind(this));
    this.app.post('/crops', this.addCrop.bind(this));
    this.app.get('/crops/:id', this.getCropDetails.bind(this));
    
    // Analytics and reports
    this.app.get('/analytics', this.getAnalytics.bind(this));
    this.app.get('/reports/health-trends', this.getHealthTrends.bind(this));
    this.app.get('/reports/yield-prediction', this.getYieldPredictions.bind(this));
    
    // Health check
    this.app.get('/health', (req, res) => {
      res.json({ 
        status: 'healthy', 
        service: 'crop-detection-service', 
        timestamp: new Date().toISOString(),
        modelsLoaded: this.modelsLoaded || false
      });
    });
  }
  
  setupErrorHandling() {
    this.app.use((error, req, res, next) => {
      logger.error('Error in crop detection service:', error);
      
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
        CREATE TABLE IF NOT EXISTS crops (
          id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          name VARCHAR(100) NOT NULL,
          scientific_name VARCHAR(200),
          category VARCHAR(50),
          optimal_conditions JSONB DEFAULT '{}',
          growth_stages JSONB DEFAULT '[]',
          common_diseases JSONB DEFAULT '[]',
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
      `);
      
      await this.db.query(`
        CREATE TABLE IF NOT EXISTS crop_analysis (
          id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          farm_id UUID NOT NULL,
          field_id UUID,
          crop_id UUID REFERENCES crops(id),
          analysis_type VARCHAR(50) NOT NULL,
          image_url VARCHAR(500) NOT NULL,
          results JSONB NOT NULL,
          confidence_score DECIMAL(5, 4),
          processing_time INTEGER,
          status VARCHAR(20) DEFAULT 'pending',
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          processed_at TIMESTAMP
        );
      `);
      
      await this.db.query(`
        CREATE TABLE IF NOT EXISTS crop_health_records (
          id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          analysis_id UUID REFERENCES crop_analysis(id) ON DELETE CASCADE,
          health_score DECIMAL(5, 2),
          disease_detected BOOLEAN DEFAULT false,
          disease_type VARCHAR(100),
          severity VARCHAR(20),
          recommendations JSONB DEFAULT '[]',
          location JSONB DEFAULT '{}',
          recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
      `);
      
      await this.db.query(`
        CREATE TABLE IF NOT EXISTS field_monitoring (
          id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          farm_id UUID NOT NULL,
          field_id UUID NOT NULL,
          monitoring_date DATE NOT NULL,
          images_count INTEGER DEFAULT 0,
          coverage_area DECIMAL(10, 2),
          overall_health DECIMAL(5, 2),
          issues_detected JSONB DEFAULT '[]',
          recommendations JSONB DEFAULT '[]',
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
      `);
      
      await this.db.query(`
        CREATE INDEX IF NOT EXISTS idx_crops_category ON crops(category);
        CREATE INDEX IF NOT EXISTS idx_analysis_farm_crop ON crop_analysis(farm_id, crop_id);
        CREATE INDEX IF NOT EXISTS idx_analysis_created_at ON crop_analysis(created_at DESC);
        CREATE INDEX IF NOT EXISTS idx_health_records_analysis_id ON crop_health_records(analysis_id);
        CREATE INDEX IF NOT EXISTS idx_field_monitoring_farm_field ON field_monitoring(farm_id, field_id);
      `);
      
      // Insert default crop data
      await this.insertDefaultCrops();
      
      logger.info('Crop detection service database initialized successfully');
    } catch (error) {
      logger.error('Database initialization error:', error);
      throw error;
    }
  }
  
  async insertDefaultCrops() {
    const defaultCrops = [
      {
        name: 'Wheat',
        scientific_name: 'Triticum aestivum',
        category: 'Cereal',
        optimal_conditions: {
          temperature: { min: 15, max: 25, optimal: 20 },
          humidity: { min: 40, max: 70, optimal: 60 },
          soil_ph: { min: 6.0, max: 7.5, optimal: 6.5 },
          water_requirement: 'Moderate'
        },
        growth_stages: [
          { stage: 'Germination', days: 7, characteristics: ['Seed sprouting', 'Root development'] },
          { stage: 'Tillering', days: 30, characteristics: ['Multiple shoots', 'Leaf development'] },
          { stage: 'Stem Extension', days: 30, characteristics: ['Rapid stem growth', 'Node formation'] },
          { stage: 'Heading', days: 15, characteristics: ['Ear emergence', 'Flowering'] },
          { stage: 'Grain Filling', days: 35, characteristics: ['Kernel development', 'Starch accumulation'] },
          { stage: 'Maturity', days: 15, characteristics: ['Grain hardening', 'Plant senescence'] }
        ],
        common_diseases: [
          { name: 'Rust', symptoms: ['Orange-brown pustules', 'Leaf yellowing'], treatment: 'Fungicide application' },
          { name: 'Powdery Mildew', symptoms: ['White powdery coating', 'Stunted growth'], treatment: 'Improve air circulation' },
          { name: 'Fusarium Head Blight', symptoms: ['Pinkish discoloration', 'Shriveled grains'], treatment: 'Crop rotation' }
        ]
      },
      {
        name: 'Corn',
        scientific_name: 'Zea mays',
        category: 'Cereal',
        optimal_conditions: {
          temperature: { min: 18, max: 32, optimal: 25 },
          humidity: { min: 50, max: 80, optimal: 70 },
          soil_ph: { min: 5.8, max: 7.0, optimal: 6.2 },
          water_requirement: 'High'
        },
        growth_stages: [
          { stage: 'Germination', days: 10, characteristics: ['Seed sprouting', 'Root establishment'] },
          { stage: 'Vegetative', days: 40, characteristics: ['Leaf development', 'Stem elongation'] },
          { stage: 'Reproductive', days: 20, characteristics: ['Tassel emergence', 'Silking'] },
          { stage: 'Grain Filling', days: 60, characteristics: ['Kernel development', 'Starch accumulation'] },
          { stage: 'Maturity', days: 20, characteristics: ['Grain hardening', 'Plant drying'] }
        ],
        common_diseases: [
          { name: 'Northern Corn Leaf Blight', symptoms: ['Long lesions', 'Gray-green spots'], treatment: 'Fungicide application' },
          { name: 'Gray Leaf Spot', symptoms: ['Small brown spots', 'Leaf necrosis'], treatment: 'Crop rotation' },
          { name: 'Common Rust', symptoms: ['Reddish-brown pustules', 'Leaf damage'], treatment: 'Resistant varieties' }
        ]
      },
      {
        name: 'Tomato',
        scientific_name: 'Solanum lycopersicum',
        category: 'Vegetable',
        optimal_conditions: {
          temperature: { min: 18, max: 27, optimal: 22 },
          humidity: { min: 60, max: 80, optimal: 70 },
          soil_ph: { min: 6.0, max: 6.8, optimal: 6.4 },
          water_requirement: 'Moderate to High'
        },
        growth_stages: [
          { stage: 'Germination', days: 7, characteristics: ['Seed sprouting', 'Cotyledon emergence'] },
          { stage: 'Seedling', days: 20, characteristics: ['True leaf development', 'Root growth'] },
          { stage: 'Vegetative', days: 30, characteristics: ['Rapid growth', 'Branching'] },
          { stage: 'Flowering', days: 15, characteristics: ['Flower cluster formation', 'Pollination'] },
          { stage: 'Fruiting', days: 60, characteristics: ['Fruit development', 'Color change'] },
          { stage: 'Harvest', days: 30, characteristics: ['Fruit ripening', 'Continuous harvest'] }
        ],
        common_diseases: [
          { name: 'Early Blight', symptoms: ['Dark concentric rings', 'Leaf yellowing'], treatment: 'Fungicide application' },
          { name: 'Late Blight', symptoms: ['Water-soaked lesions', 'White mold'], treatment: 'Copper-based fungicides' },
          { name: 'Bacterial Spot', symptoms: ['Small dark spots', 'Leaf holes'], treatment: 'Copper sprays' }
        ]
      }
    ];
    
    for (const crop of defaultCrops) {
      const exists = await this.db.query('SELECT id FROM crops WHERE name = $1', [crop.name]);
      
      if (exists.rows.length === 0) {
        await this.db.query(
          'INSERT INTO crops (name, scientific_name, category, optimal_conditions, growth_stages, common_diseases) VALUES ($1, $2, $3, $4, $5, $6)',
          [
            crop.name,
            crop.scientific_name,
            crop.category,
            JSON.stringify(crop.optimal_conditions),
            JSON.stringify(crop.growth_stages),
            JSON.stringify(crop.common_diseases)
          ]
        );
      }
    }
  }
  
  async detectCrops(req, res) {
    try {
      if (!req.file) {
        return res.status(400).json({ error: 'No image file provided' });
      }
      
      const { farmId, fieldId, cropId } = req.body;
      
      if (!farmId) {
        return res.status(400).json({ error: 'Farm ID is required' });
      }
      
      const imagePath = req.file.path;
      
      // Create analysis record
      const analysisResult = await this.db.query(
        'INSERT INTO crop_analysis (farm_id, field_id, crop_id, analysis_type, image_url, status) VALUES ($1, $2, $3, $4, $5, $6) RETURNING *',
        [farmId, fieldId, cropId, 'crop_detection', `/uploads/crops/${req.file.filename}`, 'pending']
      );
      
      const analysisId = analysisResult.rows[0].id;
      
      // Process image with AI model
      const startTime = Date.now();
      
      try {
        // Preprocess image
        const processedImage = await this.preprocessImage(imagePath);
        
        // Send to AI model
        const aiResponse = await axios.post(`${this.aiModelUrl}/detect-crops`, {
          image: processedImage,
          confidence_threshold: 0.7
        });
        
        const processingTime = Date.now() - startTime;
        const results = aiResponse.data;
        
        // Update analysis record
        await this.db.query(
          'UPDATE crop_analysis SET results = $1, confidence_score = $2, processing_time = $3, status = $4, processed_at = CURRENT_TIMESTAMP WHERE id = $5',
          [
            JSON.stringify(results),
            results.confidence || 0.85,
            processingTime,
            'completed',
            analysisId
          ]
        );
        
        logger.info(`Crop detection completed for analysis ${analysisId}`);
        
        res.json({
          message: 'Crop detection completed successfully',
          analysisId,
          results,
          processingTime
        });
        
      } catch (aiError) {
        // Update analysis as failed
        await this.db.query(
          'UPDATE crop_analysis SET status = $1, processed_at = CURRENT_TIMESTAMP WHERE id = $2',
          ['failed', analysisId]
        );
        
        logger.error('AI model processing error:', aiError);
        res.status(500).json({ error: 'AI processing failed' });
      }
    } catch (error) {
      logger.error('Crop detection error:', error);
      res.status(500).json({ error: 'Crop detection failed' });
    }
  }
  
  async detectBatchCrops(req, res) {
    try {
      if (!req.files || req.files.length === 0) {
        return res.status(400).json({ error: 'No image files provided' });
      }
      
      const { farmId, fieldId, cropId } = req.body;
      const results = [];
      
      for (const file of req.files) {
        const result = await this.processSingleImage(file, farmId, fieldId, cropId, 'crop_detection');
        results.push(result);
      }
      
      res.json({
        message: `Batch processing completed for ${results.length} images`,
        results
      });
    } catch (error) {
      logger.error('Batch crop detection error:', error);
      res.status(500).json({ error: 'Batch processing failed' });
    }
  }
  
  async analyzeCropHealth(req, res) {
    try {
      if (!req.file) {
        return res.status(400).json({ error: 'No image file provided' });
      }
      
      const { farmId, fieldId, cropId, location } = req.body;
      const imagePath = req.file.path;
      
      // Create analysis record
      const analysisResult = await this.db.query(
        'INSERT INTO crop_analysis (farm_id, field_id, crop_id, analysis_type, image_url, status) VALUES ($1, $2, $3, $4, $5, $6) RETURNING *',
        [farmId, fieldId, cropId, 'health_analysis', `/uploads/crops/${req.file.filename}`, 'pending']
      );
      
      const analysisId = analysisResult.rows[0].id;
      
      try {
        // Preprocess image
        const processedImage = await this.preprocessImage(imagePath);
        
        // Send to AI model for health analysis
        const aiResponse = await axios.post(`${this.aiModelUrl}/analyze-health`, {
          image: processedImage,
          analysis_type: 'comprehensive'
        });
        
        const results = aiResponse.data;
        
        // Create health record
        const healthScore = results.health_score || 0;
        const diseaseDetected = results.disease_detected || false;
        const diseaseType = results.disease_type || null;
        const severity = results.severity || 'none';
        
        await this.db.query(
          'INSERT INTO crop_health_records (analysis_id, health_score, disease_detected, disease_type, severity, recommendations, location) VALUES ($1, $2, $3, $4, $5, $6, $7)',
          [
            analysisId,
            healthScore,
            diseaseDetected,
            diseaseType,
            severity,
            JSON.stringify(results.recommendations || []),
            JSON.stringify(location ? JSON.parse(location) : {})
          ]
        );
        
        // Update analysis record
        await this.db.query(
          'UPDATE crop_analysis SET results = $1, confidence_score = $2, status = $3, processed_at = CURRENT_TIMESTAMP WHERE id = $4',
          [JSON.stringify(results), results.confidence || 0.85, 'completed', analysisId]
        );
        
        logger.info(`Health analysis completed for analysis ${analysisId}`);
        
        res.json({
          message: 'Health analysis completed successfully',
          analysisId,
          healthScore,
          diseaseDetected,
          diseaseType,
          severity,
          recommendations: results.recommendations || []
        });
        
      } catch (aiError) {
        await this.db.query(
          'UPDATE crop_analysis SET status = $1, processed_at = CURRENT_TIMESTAMP WHERE id = $2',
          ['failed', analysisId]
        );
        
        logger.error('Health analysis AI error:', aiError);
        res.status(500).json({ error: 'Health analysis failed' });
      }
    } catch (error) {
      logger.error('Health analysis error:', error);
      res.status(500).json({ error: 'Health analysis failed' });
    }
  }
  
  async detectDisease(req, res) {
    try {
      if (!req.file) {
        return res.status(400).json({ error: 'No image file provided' });
      }
      
      const { farmId, fieldId, cropId } = req.body;
      const imagePath = req.file.path;
      
      // Create analysis record
      const analysisResult = await this.db.query(
        'INSERT INTO crop_analysis (farm_id, field_id, crop_id, analysis_type, image_url, status) VALUES ($1, $2, $3, $4, $5, $6) RETURNING *',
        [farmId, fieldId, cropId, 'disease_detection', `/uploads/crops/${req.file.filename}`, 'pending']
      );
      
      const analysisId = analysisResult.rows[0].id;
      
      try {
        // Preprocess image
        const processedImage = await this.preprocessImage(imagePath);
        
        // Send to AI model for disease detection
        const aiResponse = await axios.post(`${this.aiModelUrl}/detect-disease`, {
          image: processedImage,
          crop_type: cropId
        });
        
        const results = aiResponse.data;
        
        // Update analysis record
        await this.db.query(
          'UPDATE crop_analysis SET results = $1, confidence_score = $2, status = $3, processed_at = CURRENT_TIMESTAMP WHERE id = $4',
          [JSON.stringify(results), results.confidence || 0.85, 'completed', analysisId]
        );
        
        logger.info(`Disease detection completed for analysis ${analysisId}`);
        
        res.json({
          message: 'Disease detection completed successfully',
          analysisId,
          results
        });
        
      } catch (aiError) {
        await this.db.query(
          'UPDATE crop_analysis SET status = $1, processed_at = CURRENT_TIMESTAMP WHERE id = $2',
          ['failed', analysisId]
        );
        
        logger.error('Disease detection AI error:', aiError);
        res.status(500).json({ error: 'Disease detection failed' });
      }
    } catch (error) {
      logger.error('Disease detection error:', error);
      res.status(500).json({ error: 'Disease detection failed' });
    }
  }
  
  async countCrops(req, res) {
    try {
      if (!req.file) {
        return res.status(400).json({ error: 'No image file provided' });
      }
      
      const { farmId, fieldId, cropId } = req.body;
      const imagePath = req.file.path;
      
      // Create analysis record
      const analysisResult = await this.db.query(
        'INSERT INTO crop_analysis (farm_id, field_id, crop_id, analysis_type, image_url, status) VALUES ($1, $2, $3, $4, $5, $6) RETURNING *',
        [farmId, fieldId, cropId, 'crop_counting', `/uploads/crops/${req.file.filename}`, 'pending']
      );
      
      const analysisId = analysisResult.rows[0].id;
      
      try {
        // Preprocess image
        const processedImage = await this.preprocessImage(imagePath);
        
        // Send to AI model for crop counting
        const aiResponse = await axios.post(`${this.aiModelUrl}/count-crops`, {
          image: processedImage,
          crop_type: cropId
        });
        
        const results = aiResponse.data;
        
        // Update analysis record
        await this.db.query(
          'UPDATE crop_analysis SET results = $1, confidence_score = $2, status = $3, processed_at = CURRENT_TIMESTAMP WHERE id = $4',
          [JSON.stringify(results), results.confidence || 0.85, 'completed', analysisId]
        );
        
        logger.info(`Crop counting completed for analysis ${analysisId}`);
        
        res.json({
          message: 'Crop counting completed successfully',
          analysisId,
          count: results.count || 0,
          density: results.density || 0,
          area: results.area || 0
        });
        
      } catch (aiError) {
        await this.db.query(
          'UPDATE crop_analysis SET status = $1, processed_at = CURRENT_TIMESTAMP WHERE id = $2',
          ['failed', analysisId]
        );
        
        logger.error('Crop counting AI error:', aiError);
        res.status(500).json({ error: 'Crop counting failed' });
      }
    } catch (error) {
      logger.error('Crop counting error:', error);
      res.status(500).json({ error: 'Crop counting failed' });
    }
  }
  
  async measureCrops(req, res) {
    try {
      if (!req.file) {
        return res.status(400).json({ error: 'No image file provided' });
      }
      
      const { farmId, fieldId, cropId } = req.body;
      const imagePath = req.file.path;
      
      // Create analysis record
      const analysisResult = await this.db.query(
        'INSERT INTO crop_analysis (farm_id, field_id, crop_id, analysis_type, image_url, status) VALUES ($1, $2, $3, $4, $5, $6) RETURNING *',
        [farmId, fieldId, cropId, 'crop_measurement', `/uploads/crops/${req.file.filename}`, 'pending']
      );
      
      const analysisId = analysisResult.rows[0].id;
      
      try {
        // Preprocess image
        const processedImage = await this.preprocessImage(imagePath);
        
        // Send to AI model for crop measurement
        const aiResponse = await axios.post(`${this.aiModelUrl}/measure-crops`, {
          image: processedImage,
          crop_type: cropId
        });
        
        const results = aiResponse.data;
        
        // Update analysis record
        await this.db.query(
          'UPDATE crop_analysis SET results = $1, confidence_score = $2, status = $3, processed_at = CURRENT_TIMESTAMP WHERE id = $4',
          [JSON.stringify(results), results.confidence || 0.85, 'completed', analysisId]
        );
        
        logger.info(`Crop measurement completed for analysis ${analysisId}`);
        
        res.json({
          message: 'Crop measurement completed successfully',
          analysisId,
          measurements: results.measurements || []
        });
        
      } catch (aiError) {
        await this.db.query(
          'UPDATE crop_analysis SET status = $1, processed_at = CURRENT_TIMESTAMP WHERE id = $2',
          ['failed', analysisId]
        );
        
        logger.error('Crop measurement AI error:', aiError);
        res.status(500).json({ error: 'Crop measurement failed' });
      }
    } catch (error) {
      logger.error('Crop measurement error:', error);
      res.status(500).json({ error: 'Crop measurement failed' });
    }
  }
  
  async detectGrowthStage(req, res) {
    try {
      if (!req.file) {
        return res.status(400).json({ error: 'No image file provided' });
      }
      
      const { farmId, fieldId, cropId } = req.body;
      const imagePath = req.file.path;
      
      // Get crop growth stages
      const cropResult = await this.db.query('SELECT growth_stages FROM crops WHERE id = $1', [cropId]);
      
      if (cropResult.rows.length === 0) {
        return res.status(404).json({ error: 'Crop not found' });
      }
      
      const growthStages = cropResult.rows[0].growth_stages;
      
      // Create analysis record
      const analysisResult = await this.db.query(
        'INSERT INTO crop_analysis (farm_id, field_id, crop_id, analysis_type, image_url, status) VALUES ($1, $2, $3, $4, $5, $6) RETURNING *',
        [farmId, fieldId, cropId, 'growth_stage_detection', `/uploads/crops/${req.file.filename}`, 'pending']
      );
      
      const analysisId = analysisResult.rows[0].id;
      
      try {
        // Preprocess image
        const processedImage = await this.preprocessImage(imagePath);
        
        // Send to AI model for growth stage detection
        const aiResponse = await axios.post(`${this.aiModelUrl}/detect-growth-stage`, {
          image: processedImage,
          crop_type: cropId,
          growth_stages: growthStages
        });
        
        const results = aiResponse.data;
        
        // Update analysis record
        await this.db.query(
          'UPDATE crop_analysis SET results = $1, confidence_score = $2, status = $3, processed_at = CURRENT_TIMESTAMP WHERE id = $4',
          [JSON.stringify(results), results.confidence || 0.85, 'completed', analysisId]
        );
        
        logger.info(`Growth stage detection completed for analysis ${analysisId}`);
        
        res.json({
          message: 'Growth stage detection completed successfully',
          analysisId,
          currentStage: results.current_stage,
          stageConfidence: results.stage_confidence,
          nextStage: results.next_stage,
          daysToNextStage: results.days_to_next_stage
        });
        
      } catch (aiError) {
        await this.db.query(
          'UPDATE crop_analysis SET status = $1, processed_at = CURRENT_TIMESTAMP WHERE id = $2',
          ['failed', analysisId]
        );
        
        logger.error('Growth stage detection AI error:', aiError);
        res.status(500).json({ error: 'Growth stage detection failed' });
      }
    } catch (error) {
      logger.error('Growth stage detection error:', error);
      res.status(500).json({ error: 'Growth stage detection failed' });
    }
  }
  
  async getGrowthStages(req, res) {
    try {
      const { cropId } = req.query;
      
      if (!cropId) {
        return res.status(400).json({ error: 'Crop ID is required' });
      }
      
      const result = await this.db.query('SELECT growth_stages FROM crops WHERE id = $1', [cropId]);
      
      if (result.rows.length === 0) {
        return res.status(404).json({ error: 'Crop not found' });
      }
      
      res.json({
        growthStages: result.rows[0].growth_stages
      });
    } catch (error) {
      logger.error('Get growth stages error:', error);
      res.status(500).json({ error: 'Failed to get growth stages' });
    }
  }
  
  async analyzeField(req, res) {
    try {
      if (!req.file) {
        return res.status(400).json({ error: 'No image file provided' });
      }
      
      const { farmId, fieldId, cropId } = req.body;
      const imagePath = req.file.path;
      
      // Create analysis record
      const analysisResult = await this.db.query(
        'INSERT INTO crop_analysis (farm_id, field_id, crop_id, analysis_type, image_url, status) VALUES ($1, $2, $3, $4, $5, $6) RETURNING *',
        [farmId, fieldId, cropId, 'field_analysis', `/uploads/crops/${req.file.filename}`, 'pending']
      );
      
      const analysisId = analysisResult.rows[0].id;
      
      try {
        // Preprocess image
        const processedImage = await this.preprocessImage(imagePath);
        
        // Send to AI model for field analysis
        const aiResponse = await axios.post(`${this.aiModelUrl}/analyze-field`, {
          image: processedImage,
          analysis_type: 'comprehensive'
        });
        
        const results = aiResponse.data;
        
        // Update analysis record
        await this.db.query(
          'UPDATE crop_analysis SET results = $1, confidence_score = $2, status = $3, processed_at = CURRENT_TIMESTAMP WHERE id = $4',
          [JSON.stringify(results), results.confidence || 0.85, 'completed', analysisId]
        );
        
        logger.info(`Field analysis completed for analysis ${analysisId}`);
        
        res.json({
          message: 'Field analysis completed successfully',
          analysisId,
          results
        });
        
      } catch (aiError) {
        await this.db.query(
          'UPDATE crop_analysis SET status = $1, processed_at = CURRENT_TIMESTAMP WHERE id = $2',
          ['failed', analysisId]
        );
        
        logger.error('Field analysis AI error:', aiError);
        res.status(500).json({ error: 'Field analysis failed' });
      }
    } catch (error) {
      logger.error('Field analysis error:', error);
      res.status(500).json({ error: 'Field analysis failed' });
    }
  }
  
  async monitorField(req, res) {
    try {
      if (!req.files || req.files.length === 0) {
        return res.status(400).json({ error: 'No image files provided' });
      }
      
      const { farmId, fieldId, monitoringDate, coverageArea } = req.body;
      
      if (!farmId || !fieldId || !monitoringDate) {
        return res.status(400).json({ error: 'Missing required monitoring fields' });
      }
      
      const analysisIds = [];
      const results = [];
      
      // Process each image
      for (const file of req.files) {
        const result = await this.processSingleImage(file, farmId, fieldId, null, 'field_monitoring');
        analysisIds.push(result.analysisId);
        results.push(result);
      }
      
      // Create field monitoring record
      const monitoringResult = await this.db.query(
        'INSERT INTO field_monitoring (farm_id, field_id, monitoring_date, images_count, coverage_area, overall_health, issues_detected, recommendations) VALUES ($1, $2, $3, $4, $5, $6, $7, $8) RETURNING *',
        [
          farmId,
          fieldId,
          monitoringDate,
          req.files.length,
          coverageArea,
          this.calculateOverallHealth(results),
          JSON.stringify(this.aggregateIssues(results)),
          JSON.stringify(this.generateRecommendations(results))
        ]
      );
      
      logger.info(`Field monitoring completed: ${monitoringResult.rows[0].id}`);
      
      res.json({
        message: 'Field monitoring completed successfully',
        monitoringId: monitoringResult.rows[0].id,
        analysisIds,
        results
      });
    } catch (error) {
      logger.error('Field monitoring error:', error);
      res.status(500).json({ error: 'Field monitoring failed' });
    }
  }
  
  async getAnalysisHistory(req, res) {
    try {
      const { farmId, fieldId, cropId, analysisType, limit = 20, offset = 0 } = req.query;
      
      let query = `
        SELECT ca.*, c.name as crop_name
        FROM crop_analysis ca
        LEFT JOIN crops c ON ca.crop_id = c.id
        WHERE 1=1
      `;
      let params = [];
      let paramCount = 0;
      
      if (farmId) {
        paramCount++;
        query += ` AND ca.farm_id = $${paramCount}`;
        params.push(farmId);
      }
      
      if (fieldId) {
        paramCount++;
        query += ` AND ca.field_id = $${paramCount}`;
        params.push(fieldId);
      }
      
      if (cropId) {
        paramCount++;
        query += ` AND ca.crop_id = $${paramCount}`;
        params.push(cropId);
      }
      
      if (analysisType) {
        paramCount++;
        query += ` AND ca.analysis_type = $${paramCount}`;
        params.push(analysisType);
      }
      
      paramCount++;
      query += ` ORDER BY ca.created_at DESC LIMIT $${paramCount}`;
      params.push(limit);
      
      paramCount++;
      query += ` OFFSET $${paramCount}`;
      params.push(offset);
      
      const result = await this.db.query(query, params);
      
      const analyses = result.rows.map(analysis => ({
        id: analysis.id,
        farmId: analysis.farm_id,
        fieldId: analysis.field_id,
        cropId: analysis.crop_id,
        cropName: analysis.crop_name,
        analysisType: analysis.analysis_type,
        imageUrl: analysis.image_url,
        status: analysis.status,
        confidenceScore: analysis.confidence_score,
        processingTime: analysis.processing_time,
        createdAt: analysis.created_at,
        processedAt: analysis.processed_at
      }));
      
      res.json({ analyses });
    } catch (error) {
      logger.error('Get analysis history error:', error);
      res.status(500).json({ error: 'Failed to get analysis history' });
    }
  }
  
  async getAnalysisResult(req, res) {
    try {
      const analysisId = req.params.id;
      
      const result = await this.db.query(`
        SELECT ca.*, c.name as crop_name, chr.health_score, chr.disease_detected, 
               chr.disease_type, chr.severity, chr.recommendations
        FROM crop_analysis ca
        LEFT JOIN crops c ON ca.crop_id = c.id
        LEFT JOIN crop_health_records chr ON ca.id = chr.analysis_id
        WHERE ca.id = $1
      `, [analysisId]);
      
      if (result.rows.length === 0) {
        return res.status(404).json({ error: 'Analysis not found' });
      }
      
      const analysis = result.rows[0];
      
      res.json({
        analysis: {
          id: analysis.id,
          farmId: analysis.farm_id,
          fieldId: analysis.field_id,
          cropId: analysis.crop_id,
          cropName: analysis.crop_name,
          analysisType: analysis.analysis_type,
          imageUrl: analysis.image_url,
          results: analysis.results,
          status: analysis.status,
          confidenceScore: analysis.confidence_score,
          processingTime: analysis.processing_time,
          createdAt: analysis.created_at,
          processedAt: analysis.processed_at,
          healthScore: analysis.health_score,
          diseaseDetected: analysis.disease_detected,
          diseaseType: analysis.disease_type,
          severity: analysis.severity,
          recommendations: analysis.recommendations
        }
      });
    } catch (error) {
      logger.error('Get analysis result error:', error);
      res.status(500).json({ error: 'Failed to get analysis result' });
    }
  }
  
  async getCrops(req, res) {
    try {
      const { category, search } = req.query;
      
      let query = 'SELECT id, name, scientific_name, category FROM crops WHERE 1=1';
      let params = [];
      let paramCount = 0;
      
      if (category) {
        paramCount++;
        query += ` AND category = $${paramCount}`;
        params.push(category);
      }
      
      if (search) {
        paramCount++;
        query += ` AND (name ILIKE $${paramCount} OR scientific_name ILIKE $${paramCount})`;
        params.push(`%${search}%`);
      }
      
      query += ` ORDER BY name`;
      
      const result = await this.db.query(query, params);
      
      const crops = result.rows.map(crop => ({
        id: crop.id,
        name: crop.name,
        scientificName: crop.scientific_name,
        category: crop.category
      }));
      
      res.json({ crops });
    } catch (error) {
      logger.error('Get crops error:', error);
      res.status(500).json({ error: 'Failed to get crops' });
    }
  }
  
  async addCrop(req, res) {
    try {
      const { name, scientificName, category, optimalConditions, growthStages, commonDiseases } = req.body;
      
      if (!name || !scientificName || !category) {
        return res.status(400).json({ error: 'Missing required crop fields' });
      }
      
      const result = await this.db.query(
        'INSERT INTO crops (name, scientific_name, category, optimal_conditions, growth_stages, common_diseases) VALUES ($1, $2, $3, $4, $5, $6) RETURNING *',
        [
          name,
          scientificName,
          category,
          JSON.stringify(optimalConditions || {}),
          JSON.stringify(growthStages || []),
          JSON.stringify(commonDiseases || [])
        ]
      );
      
      logger.info(`New crop added: ${name}`);
      
      res.status(201).json({
        message: 'Crop added successfully',
        crop: result.rows[0]
      });
    } catch (error) {
      logger.error('Add crop error:', error);
      res.status(500).json({ error: 'Failed to add crop' });
    }
  }
  
  async getCropDetails(req, res) {
    try {
      const cropId = req.params.id;
      
      const result = await this.db.query('SELECT * FROM crops WHERE id = $1', [cropId]);
      
      if (result.rows.length === 0) {
        return res.status(404).json({ error: 'Crop not found' });
      }
      
      const crop = result.rows[0];
      
      res.json({
        crop: {
          id: crop.id,
          name: crop.name,
          scientificName: crop.scientific_name,
          category: crop.category,
          optimalConditions: crop.optimal_conditions,
          growthStages: crop.growth_stages,
          commonDiseases: crop.common_diseases,
          createdAt: crop.created_at,
          updatedAt: crop.updated_at
        }
      });
    } catch (error) {
      logger.error('Get crop details error:', error);
      res.status(500).json({ error: 'Failed to get crop details' });
    }
  }
  
  async getAnalytics(req, res) {
    try {
      const { farmId, period = '30days' } = req.query;
      
      let days = 30;
      if (period === '7days') days = 7;
      else if (period === '90days') days = 90;
      
      // Analysis statistics
      const analysisStats = await this.db.query(`
        SELECT 
          COUNT(*) as total_analyses,
          analysis_type,
          COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_analyses,
          AVG(confidence_score) as avg_confidence
        FROM crop_analysis
        WHERE farm_id = $1 AND created_at >= NOW() - INTERVAL '${days} days'
        GROUP BY analysis_type
      `, [farmId]);
      
      // Health statistics
      const healthStats = await this.db.query(`
        SELECT 
          AVG(health_score) as avg_health_score,
          COUNT(CASE WHEN disease_detected = true THEN 1 END) as disease_cases,
          COUNT(CASE WHEN severity = 'high' THEN 1 END) as high_severity_cases
        FROM crop_health_records chr
        JOIN crop_analysis ca ON chr.analysis_id = ca.id
        WHERE ca.farm_id = $1 AND chr.recorded_at >= NOW() - INTERVAL '${days} days'
      `, [farmId]);
      
      res.json({
        period,
        analysisStats: analysisStats.rows,
        healthStats: healthStats.rows[0]
      });
    } catch (error) {
      logger.error('Get analytics error:', error);
      res.status(500).json({ error: 'Failed to get analytics' });
    }
  }
  
  async getHealthTrends(req, res) {
    try {
      const { farmId, fieldId, days = 30 } = req.query;
      
      let query = `
        SELECT 
          DATE(chr.recorded_at) as date,
          AVG(chr.health_score) as avg_health_score,
          COUNT(CASE WHEN chr.disease_detected = true THEN 1 END) as disease_count
        FROM crop_health_records chr
        JOIN crop_analysis ca ON chr.analysis_id = ca.id
        WHERE ca.farm_id = $1 AND chr.recorded_at >= NOW() - INTERVAL '${days} days'
      `;
      let params = [farmId];
      
      if (fieldId) {
        query += ` AND ca.field_id = $2`;
        params.push(fieldId);
      }
      
      query += ` GROUP BY DATE(chr.recorded_at) ORDER BY date`;
      
      const result = await this.db.query(query, params);
      
      const trends = result.rows.map(row => ({
        date: row.date,
        healthScore: parseFloat(row.avg_health_score) || 0,
        diseaseCount: parseInt(row.disease_count) || 0
      }));
      
      res.json({ trends });
    } catch (error) {
      logger.error('Get health trends error:', error);
      res.status(500).json({ error: 'Failed to get health trends' });
    }
  }
  
  async getYieldPredictions(req, res) {
    try {
      const { farmId, fieldId, cropId } = req.query;
      
      // This would integrate with yield prediction models
      // For now, return sample predictions based on health data
      const healthData = await this.db.query(`
        SELECT AVG(health_score) as avg_health, COUNT(*) as sample_count
        FROM crop_health_records chr
        JOIN crop_analysis ca ON chr.analysis_id = ca.id
        WHERE ca.farm_id = $1 AND chr.recorded_at >= NOW() - INTERVAL '30 days'
      `, [farmId]);
      
      const avgHealth = healthData.rows[0].avg_health || 75;
      const sampleCount = healthData.rows[0].sample_count || 1;
      
      // Simple yield prediction based on health score
      const baseYield = 1000; // kg per hectare
      const healthFactor = avgHealth / 100;
      const predictedYield = baseYield * healthFactor * (1 + Math.min(sampleCount * 0.01, 0.2));
      
      res.json({
        predictedYield: Math.round(predictedYield),
        confidence: Math.min(0.7 + (sampleCount * 0.01), 0.95),
        factors: {
          healthScore: Math.round(avgHealth),
          sampleSize: sampleCount
        }
      });
    } catch (error) {
      logger.error('Get yield predictions error:', error);
      res.status(500).json({ error: 'Failed to get yield predictions' });
    }
  }
  
  async processSingleImage(file, farmId, fieldId, cropId, analysisType) {
    const analysisResult = await this.db.query(
      'INSERT INTO crop_analysis (farm_id, field_id, crop_id, analysis_type, image_url, status) VALUES ($1, $2, $3, $4, $5, $6) RETURNING *',
      [farmId, fieldId, cropId, analysisType, `/uploads/crops/${file.filename}`, 'pending']
    );
    
    const analysisId = analysisResult.rows[0].id;
    
    try {
      const processedImage = await this.preprocessImage(file.path);
      
      const aiResponse = await axios.post(`${this.aiModelUrl}/process-image`, {
        image: processedImage,
        analysis_type: analysisType
      });
      
      const results = aiResponse.data;
      
      await this.db.query(
        'UPDATE crop_analysis SET results = $1, confidence_score = $2, status = $3, processed_at = CURRENT_TIMESTAMP WHERE id = $4',
        [JSON.stringify(results), results.confidence || 0.85, 'completed', analysisId]
      );
      
      return {
        analysisId,
        results,
        status: 'completed'
      };
      
    } catch (error) {
      await this.db.query(
        'UPDATE crop_analysis SET status = $1, processed_at = CURRENT_TIMESTAMP WHERE id = $2',
        ['failed', analysisId]
      );
      
      return {
        analysisId,
        error: error.message,
        status: 'failed'
      };
    }
  }
  
  async preprocessImage(imagePath) {
    try {
      // Resize image to optimal size for AI processing
      const resizedImage = await sharp(imagePath)
        .resize(1024, 1024, { fit: 'inside', withoutEnlargement: true })
        .jpeg({ quality: 85 })
        .toBuffer();
      
      // Convert to base64
      return resizedImage.toString('base64');
    } catch (error) {
      logger.error('Image preprocessing error:', error);
      throw error;
    }
  }
  
  calculateOverallHealth(results) {
    const completedResults = results.filter(r => r.status === 'completed');
    if (completedResults.length === 0) return 0;
    
    const totalHealth = completedResults.reduce((sum, result) => {
      return sum + (result.results.health_score || 50);
    }, 0);
    
    return Math.round(totalHealth / completedResults.length);
  }
  
  aggregateIssues(results) {
    const issues = [];
    
    results.forEach(result => {
      if (result.status === 'completed' && result.results.issues) {
        issues.push(...result.results.issues);
      }
    });
    
    return issues;
  }
  
  generateRecommendations(results) {
    const recommendations = [];
    
    results.forEach(result => {
      if (result.status === 'completed' && result.results.recommendations) {
        recommendations.push(...result.results.recommendations);
      }
    });
    
    return [...new Set(recommendations)]; // Remove duplicates
  }
  
  start() {
    this.app.listen(this.port, () => {
      logger.info(`Crop detection service running on port ${this.port}`);
    });
  }
}

// Start the service
if (require.main === module) {
  const cropDetectionService = new CropDetectionService();
  cropDetectionService.start();
}

module.exports = CropDetectionService;