const express = require('express');
const { Pool } = require('pg');
const Redis = require('ioredis');
const winston = require('winston');
const axios = require('axios');

// Configure logging
const logger = winston.createLogger({
  level: 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.json()
  ),
  transports: [
    new winston.transports.File({ filename: 'recommendation-service.log' }),
    new winston.transports.Console()
  ]
});

class RecommendationService {
  constructor() {
    this.app = express();
    this.port = process.env.PORT || 3007;
    
    // Database connections
    this.db = new Pool({
      host: process.env.DB_HOST || 'localhost',
      port: process.env.DB_PORT || 5432,
      database: process.env.DB_NAME || 'geofarm_recommendations',
      user: process.env.DB_USER || 'postgres',
      password: process.env.DB_PASSWORD || 'password',
      ssl: false
    });
    
    this.redis = new Redis({
      host: process.env.REDIS_HOST || 'localhost',
      port: process.env.REDIS_PORT || 6379,
      password: process.env.REDIS_PASSWORD || undefined
    });
    
    // AI Model configuration
    this.aiModelUrl = process.env.AI_MODEL_URL || 'http://ai-model-service:5000';
    
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
    // Main recommendation endpoints
    this.app.post('/generate', this.generateRecommendations.bind(this));
    this.app.get('/recommendations', this.getRecommendations.bind(this));
    this.app.get('/recommendations/:id', this.getRecommendationById.bind(this));
    this.app.put('/recommendations/:id/status', this.updateRecommendationStatus.bind(this));
    
    // Specific recommendation types
    this.app.post('/irrigation', this.getIrrigationRecommendations.bind(this));
    this.app.post('/fertilization', this.getFertilizationRecommendations.bind(this));
    this.app.post('/pest-control', this.getPestControlRecommendations.bind(this));
    this.app.post('/planting', this.getPlantingRecommendations.bind(this));
    this.app.post('/harvesting', this.getHarvestingRecommendations.bind(this));
    this.app.post('/crop-rotation', this.getCropRotationRecommendations.bind(this));
    
    // Real-time recommendations
    this.app.post('/real-time', this.getRealTimeRecommendations.bind(this));
    this.app.get('/alerts', this.getRecommendationAlerts.bind(this));
    this.app.post('/alerts', this.createRecommendationAlert.bind(this));
    
    // Analytics and insights
    this.app.get('/analytics', this.getRecommendationAnalytics.bind(this));
    this.app.get('/trends', this.getRecommendationTrends.bind(this));
    this.app.get('/effectiveness', this.getRecommendationEffectiveness.bind(this));
    
    // Knowledge base
    this.app.get('/knowledge-base', this.getKnowledgeBase.bind(this));
    this.app.post('/knowledge-base', this.addKnowledgeBaseItem.bind(this));
    
    // Health check
    this.app.get('/health', (req, res) => {
      res.json({ 
        status: 'healthy', 
        service: 'recommendation-service', 
        timestamp: new Date().toISOString(),
        recommendationsGenerated: this.recommendationsGenerated || 0
      });
    });
  }
  
  setupErrorHandling() {
    this.app.use((error, req, res, next) => {
      logger.error('Error in recommendation service:', error);
      res.status(500).json({ 
        error: 'Internal server error',
        message: process.env.NODE_ENV === 'development' ? error.message : undefined
      });
    });
  }
  
  async initializeDatabase() {
    try {
      await this.db.query(`
        CREATE TABLE IF NOT EXISTS recommendations (
          id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          farm_id UUID NOT NULL,
          field_id UUID,
          crop_id UUID,
          recommendation_type VARCHAR(50) NOT NULL,
          title VARCHAR(200) NOT NULL,
          description TEXT NOT NULL,
          priority VARCHAR(20) DEFAULT 'medium',
          status VARCHAR(20) DEFAULT 'pending',
          category VARCHAR(50) NOT NULL,
          conditions JSONB DEFAULT '{}',
          actions JSONB DEFAULT '[]',
          timeline JSONB DEFAULT '{}',
          expected_outcome JSONB DEFAULT '{}',
          resources_required JSONB DEFAULT '[]',
          cost_estimate JSONB DEFAULT '{}',
          effectiveness_score DECIMAL(5, 2),
          data_sources JSONB DEFAULT '[]',
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          expires_at TIMESTAMP
        );
      `);
      
      await this.db.query(`
        CREATE TABLE IF NOT EXISTS recommendation_alerts (
          id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          farm_id UUID NOT NULL,
          field_id UUID,
          alert_type VARCHAR(50) NOT NULL,
          severity VARCHAR(20) DEFAULT 'medium',
          title VARCHAR(200) NOT NULL,
          message TEXT NOT NULL,
          conditions JSONB DEFAULT '{}',
          recommendations JSONB DEFAULT '[]',
          is_active BOOLEAN DEFAULT true,
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          expires_at TIMESTAMP
        );
      `);
      
      await this.db.query(`
        CREATE TABLE IF NOT EXISTS knowledge_base (
          id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          category VARCHAR(50) NOT NULL,
          subcategory VARCHAR(50),
          title VARCHAR(200) NOT NULL,
          content TEXT NOT NULL,
          tags JSONB DEFAULT '[]',
          conditions JSONB DEFAULT '{}',
          sources JSONB DEFAULT '[]',
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
      `);
      
      await this.db.query(`
        CREATE TABLE IF NOT EXISTS recommendation_feedback (
          id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          recommendation_id UUID REFERENCES recommendations(id) ON DELETE CASCADE,
          user_id UUID NOT NULL,
          effectiveness_rating INTEGER CHECK (effectiveness_rating >= 1 AND effectiveness_rating <= 5),
          feedback_text TEXT,
          implemented_at TIMESTAMP,
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
      `);
      
      await this.db.query(`
        CREATE INDEX IF NOT EXISTS idx_recommendations_farm ON recommendations(farm_id);
        CREATE INDEX IF NOT EXISTS idx_recommendations_type ON recommendations(recommendation_type);
        CREATE INDEX IF NOT EXISTS idx_recommendations_status ON recommendations(status);
        CREATE INDEX IF NOT EXISTS idx_recommendations_created_at ON recommendations(created_at DESC);
        CREATE INDEX IF NOT EXISTS idx_alerts_farm ON recommendation_alerts(farm_id);
        CREATE INDEX IF NOT EXISTS idx_alerts_active ON recommendation_alerts(is_active);
        CREATE INDEX IF NOT EXISTS idx_knowledge_category ON knowledge_base(category);
        CREATE INDEX IF NOT EXISTS idx_feedback_recommendation ON recommendation_feedback(recommendation_id);
      `);
      
      // Insert default knowledge base data
      await this.insertDefaultKnowledgeBase();
      
      logger.info('Recommendation service database initialized successfully');
    } catch (error) {
      logger.error('Database initialization error:', error);
      throw error;
    }
  }
  
  async insertDefaultKnowledgeBase() {
    const knowledgeItems = [
      {
        category: 'irrigation',
        subcategory: 'water_management',
        title: 'Drip Irrigation Best Practices',
        content: 'Drip irrigation is the most efficient method for crop watering, delivering water directly to plant roots. Key benefits include 50% water savings, reduced weed growth, and improved crop yields. Install drip lines 12-16 inches apart for most crops.',
        tags: ['irrigation', 'water', 'efficiency', 'drip'],
        conditions: { soil_type: 'any', climate: 'any' },
        sources: ['FAO Irrigation Guidelines', 'University Agricultural Extensions']
      },
      {
        category: 'fertilization',
        subcategory: 'nutrient_management',
        title: 'Soil Testing and Fertilizer Application',
        content: 'Regular soil testing is crucial for optimal fertilizer application. Test soil pH, NPK levels, and organic matter content annually. Apply fertilizers based on test results and crop requirements to avoid over-fertilization and environmental damage.',
        tags: ['fertilizer', 'soil', 'testing', 'nutrients'],
        conditions: { soil_test_required: true },
        sources: ['Soil Science Society', 'Agricultural Research Centers']
      },
      {
        category: 'pest_control',
        subcategory: 'integrated_pest_management',
        title: 'Integrated Pest Management (IPM) Strategies',
        content: 'IPM combines biological, cultural, and chemical practices for sustainable pest control. Monitor pest populations regularly, use beneficial insects, rotate crops, and apply pesticides only when necessary. This approach reduces chemical use by 50-80%.',
        tags: ['pest_control', 'IPM', 'sustainable', 'biological'],
        conditions: { pest_pressure: 'moderate_to_high' },
        sources: ['IPM Research Institute', 'Organic Farming Associations']
      },
      {
        category: 'planting',
        subcategory: 'crop_selection',
        title: 'Climate-Smart Crop Selection',
        content: 'Choose crop varieties adapted to local climate conditions and future climate projections. Consider drought tolerance, heat resistance, and disease resistance. Climate-smart varieties can increase yields by 20-30% under changing conditions.',
        tags: ['climate', 'crop_selection', 'adaptation', 'varieties'],
        conditions: { climate_change_consideration: true },
        sources: ['Climate Change Agriculture', 'Seed Research Institutes']
      },
      {
        category: 'harvesting',
        subcategory: 'timing',
        title: 'Optimal Harvest Timing',
        content: "Harvest timing significantly impacts crop quality and yield. Monitor crop maturity indicators including color changes, firmness, and sugar content. Use the 'golden window' approach - harvest when quality peaks but before over-ripening.",
        tags: ['harvest', 'timing', 'quality', 'maturity'],
        conditions: { crop_maturity: 'monitoring_required' },
        sources: ['Post-Harvest Technology', 'Crop Science Journals']
      }
    ];
    
    for (const item of knowledgeItems) {
      const exists = await this.db.query('SELECT id FROM knowledge_base WHERE title = $1', [item.title]);
      
      if (exists.rows.length === 0) {
        await this.db.query(
          'INSERT INTO knowledge_base (category, subcategory, title, content, tags, conditions, sources) VALUES ($1, $2, $3, $4, $5, $6, $7)',
          [
            item.category,
            item.subcategory,
            item.title,
            item.content,
            JSON.stringify(item.tags),
            JSON.stringify(item.conditions),
            JSON.stringify(item.sources)
          ]
        );
      }
    }
  }
  
  async generateRecommendations(req, res) {
    try {
      const { farmId, fieldId, cropId, recommendationTypes, priorityLevel } = req.body;
      
      if (!farmId) {
        return res.status(400).json({ error: 'Farm ID is required' });
      }
      
      // Get current farm data
      const farmData = await this.getFarmData(farmId, fieldId, cropId);
      
      // Get environmental data
      const weatherData = await this.getWeatherData(fieldId);
      const soilData = await this.getSoilData(fieldId);
      
      // Get crop health data
      const healthData = await this.getCropHealthData(fieldId, cropId);
      
      // Generate recommendations based on available data
      const recommendations = [];
      
      if (!recommendationTypes || recommendationTypes.includes('irrigation')) {
        const irrigationRecs = await this.generateIrrigationRecommendations(farmData, weatherData, soilData);
        recommendations.push(...irrigationRecs);
      }
      
      if (!recommendationTypes || recommendationTypes.includes('fertilization')) {
        const fertilizationRecs = await this.generateFertilizationRecommendations(farmData, soilData, healthData);
        recommendations.push(...fertilizationRecs);
      }
      
      if (!recommendationTypes || recommendationTypes.includes('pest_control')) {
        const pestControlRecs = await this.generatePestControlRecommendations(farmData, healthData);
        recommendations.push(...pestControlRecs);
      }
      
      if (!recommendationTypes || recommendationTypes.includes('planting')) {
        const plantingRecs = await this.generatePlantingRecommendations(farmData, weatherData, soilData);
        recommendations.push(...plantingRecs);
      }
      
      // Store recommendations in database
      const storedRecommendations = [];
      
      for (const rec of recommendations) {
        const result = await this.db.query(
          `INSERT INTO recommendations (
            farm_id, field_id, crop_id, recommendation_type, title, description,
            priority, category, conditions, actions, timeline, expected_outcome,
            resources_required, cost_estimate, data_sources, expires_at
          ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16) RETURNING *`,
          [
            farmId,
            fieldId,
            cropId,
            rec.type,
            rec.title,
            rec.description,
            rec.priority || priorityLevel || 'medium',
            rec.category,
            JSON.stringify(rec.conditions || {}),
            JSON.stringify(rec.actions || []),
            JSON.stringify(rec.timeline || {}),
            JSON.stringify(rec.expectedOutcome || {}),
            JSON.stringify(rec.resourcesRequired || []),
            JSON.stringify(rec.costEstimate || {}),
            JSON.stringify(rec.dataSources || []),
            new Date(Date.now() + 7 * 24 * 60 * 60 * 1000) // Expires in 7 days
          ]
        );
        
        storedRecommendations.push(result.rows[0]);
      }
      
      // Cache recommendations in Redis
      await this.cacheRecommendations(farmId, storedRecommendations);
      
      logger.info(`Generated ${storedRecommendations.length} recommendations for farm ${farmId}`);
      
      res.json({
        message: 'Recommendations generated successfully',
        recommendations: storedRecommendations.map(rec => ({
          id: rec.id,
          type: rec.recommendation_type,
          title: rec.title,
          description: rec.description,
          priority: rec.priority,
          category: rec.category,
          status: rec.status,
          createdAt: rec.created_at
        }))
      });
    } catch (error) {
      logger.error('Generate recommendations error:', error);
      res.status(500).json({ error: 'Failed to generate recommendations' });
    }
  }
  
  async getIrrigationRecommendations(req, res) {
    try {
      const { farmId, fieldId, cropId } = req.body;
      
      const farmData = await this.getFarmData(farmId, fieldId, cropId);
      const weatherData = await this.getWeatherData(fieldId);
      const soilData = await this.getSoilData(fieldId);
      
      const recommendations = await this.generateIrrigationRecommendations(farmData, weatherData, soilData);
      
      res.json({ recommendations });
    } catch (error) {
      logger.error('Get irrigation recommendations error:', error);
      res.status(500).json({ error: 'Failed to get irrigation recommendations' });
    }
  }
  
  async generateIrrigationRecommendations(farmData, weatherData, soilData) {
    const recommendations = [];
    
    // Analyze current conditions
    const currentWeather = weatherData.current;
    const forecast = weatherData.forecast;
    const soilMoisture = soilData.moisture || 50;
    
    // Check soil moisture levels
    if (soilMoisture < 30) {
      recommendations.push({
        type: 'irrigation',
        title: 'Immediate Irrigation Required',
        description: 'Soil moisture levels are critically low. Immediate irrigation is needed to prevent crop stress.',
        category: 'water_management',
        priority: 'high',
        conditions: { soil_moisture: soilMoisture, weather: currentWeather },
        actions: [
          'Initiate immediate irrigation cycle',
          'Monitor soil moisture every 2 hours',
          'Check irrigation system for proper operation'
        ],
        timeline: { start: 'immediate', duration: '2-4 hours' },
        expectedOutcome: { water_savings: '10%', yield_improvement: '5-8%' },
        resourcesRequired: ['irrigation equipment', 'water supply', 'monitoring tools'],
        costEstimate: { amount: 50, currency: 'USD', unit: 'per_acre' },
        dataSources: ['soil_sensors', 'weather_api', 'crop_requirements']
      });
    }
    
    // Check precipitation forecast
    const weeklyPrecipitation = forecast.reduce((sum, day) => sum + (day.precipitation || 0), 0);
    
    if (weeklyPrecipitation < 10 && currentWeather.temperature > 25) {
      recommendations.push({
        type: 'irrigation',
        title: 'Weekly Irrigation Schedule',
        description: `Low precipitation forecast (${weeklyPrecipitation.toFixed(1)}mm) with high temperatures. Implement regular irrigation schedule.`,
        category: 'water_management',
        priority: 'medium',
        conditions: { precipitation_forecast: weeklyPrecipitation, temperature: currentWeather.temperature },
        actions: [
          'Schedule irrigation for early morning (5-7 AM)',
          'Apply 25-30mm water per week',
          'Use drip irrigation for efficiency'
        ],
        timeline: { start: 'within 24 hours', frequency: '3 times per week' },
        expectedOutcome: { water_efficiency: '85%', crop_health_improvement: 'significant' },
        resourcesRequired: ['drip irrigation system', 'timer controls', 'water source'],
        costEstimate: { amount: 30, currency: 'USD', unit: 'per_acre_weekly' },
        dataSources: ['weather_forecast', 'crop_water_requirements', 'soil_analysis']
      });
    }
    
    // Seasonal irrigation optimization
    if (currentWeather.season === 'summer' && currentWeather.temperature > 30) {
      recommendations.push({
        type: 'irrigation',
        title: 'Summer Irrigation Optimization',
        description: 'High summer temperatures require optimized irrigation strategies to minimize water loss and maintain crop health.',
        category: 'seasonal_management',
        priority: 'medium',
        conditions: { season: 'summer', temperature: currentWeather.temperature },
        actions: [
          'Increase irrigation frequency to daily during peak heat',
          'Mulch around plants to reduce evaporation',
          'Consider shade nets for sensitive crops'
        ],
        timeline: { start: 'immediately', duration: 'summer season' },
        expectedOutcome: { water_savings: '20%', evaporation_reduction: '30%' },
        resourcesRequired: ['mulching materials', 'shade equipment', 'increased water supply'],
        costEstimate: { amount: 100, currency: 'USD', unit: 'per_acre_seasonal' },
        dataSources: ['seasonal_climate_data', 'crop_heat_tolerance', 'evapotranspiration_rates']
      });
    }
    
    return recommendations;
  }
  
  async getFertilizationRecommendations(req, res) {
    try {
      const { farmId, fieldId, cropId } = req.body;
      
      const farmData = await this.getFarmData(farmId, fieldId, cropId);
      const soilData = await this.getSoilData(fieldId);
      const healthData = await this.getCropHealthData(fieldId, cropId);
      
      const recommendations = await this.generateFertilizationRecommendations(farmData, soilData, healthData);
      
      res.json({ recommendations });
    } catch (error) {
      logger.error('Get fertilization recommendations error:', error);
      res.status(500).json({ error: 'Failed to get fertilization recommendations' });
    }
  }
  
  async generateFertilizationRecommendations(farmData, soilData, healthData) {
    const recommendations = [];
    
    // Analyze soil nutrients
    const soilNitrogen = soilData.nitrogen || 0;
    const soilPhosphorus = soilData.phosphorus || 0;
    const soilPotassium = soilData.potassium || 0;
    const soilPH = soilData.ph || 7.0;
    
    // Nitrogen recommendations
    if (soilNitrogen < 50) {
      recommendations.push({
        type: 'fertilization',
        title: 'Nitrogen Supplementation Required',
        description: `Soil nitrogen levels are low (${soilNitrogen} ppm). Apply nitrogen fertilizer to support plant growth.`,
        category: 'nutrient_management',
        priority: 'high',
        conditions: { soil_nitrogen: soilNitrogen, crop_growth_stage: farmData.growthStage },
        actions: [
          'Apply 100-150 kg/ha of nitrogen fertilizer',
          'Use split application: 50% at planting, 50% during vegetative growth',
          'Consider slow-release formulations'
        ],
        timeline: { start: 'immediate', frequency: 'split application' },
        expectedOutcome: { yield_increase: '15-20%', plant_vigor_improvement: 'significant' },
        resourcesRequired: ['nitrogen fertilizer', 'application equipment', 'soil testing kit'],
        costEstimate: { amount: 200, currency: 'USD', unit: 'per_hectare' },
        dataSources: ['soil_nutrient_analysis', 'crop_requirements', 'growth_stage_assessment']
      });
    }
    
    // pH adjustment recommendations
    if (soilPH < 6.0) {
      recommendations.push({
        type: 'fertilization',
        title: 'Soil pH Adjustment - Lime Application',
        description: `Soil pH is too acidic (${soilPH}). Apply lime to raise pH to optimal levels for nutrient availability.`,
        category: 'soil_management',
        priority: 'medium',
        conditions: { soil_ph: soilPH, target_ph: '6.5-7.0' },
        actions: [
          'Apply agricultural lime at 2-3 tons per hectare',
          'Incorporate lime into soil 2-3 months before planting',
          'Retest soil pH after 6 months'
        ],
        timeline: { start: '2-3 months before planting', duration: 'gradual adjustment' },
        expectedOutcome: { nutrient_availability: 'improved', soil_health: 'enhanced' },
        resourcesRequired: ['agricultural lime', 'soil incorporation equipment', 'pH testing materials'],
        costEstimate: { amount: 300, currency: 'USD', unit: 'per_hectare' },
        dataSources: ['soil_ph_test', 'lime_requirement_calculation', 'crop_ph_preferences']
      });
    }
    
    // Crop-specific fertilization
    if (farmData.cropType === 'tomato' && healthData.nutrientDeficiencies) {
      recommendations.push({
        type: 'fertilization',
        title: 'Tomato Nutrient Management',
        description: 'Tomatoes showing signs of nutrient deficiencies. Apply balanced fertilizer with micronutrients.',
        category: 'crop_specific',
        priority: 'medium',
        conditions: { crop_type: 'tomato', deficiencies_detected: true },
        actions: [
          'Apply NPK fertilizer (10-10-10) at 500 kg/ha',
          'Include micronutrients: magnesium, calcium, boron',
          'Apply as side dressing during fruit development'
        ],
        timeline: { start: 'fruit development stage', frequency: 'every 3-4 weeks' },
        expectedOutcome: { fruit_quality: 'improved', yield_increase: '10-15%' },
        resourcesRequired: ['balanced NPK fertilizer', 'micronutrient supplements', 'side-dressing equipment'],
        costEstimate: { amount: 150, currency: 'USD', unit: 'per_hectare_application' },
        dataSources: ['crop_nutrient_requirements', 'deficiency_symptoms', 'yield_targets']
      });
    }
    
    return recommendations;
  }
  
  async getPestControlRecommendations(req, res) {
    try {
      const { farmId, fieldId, cropId } = req.body;
      
      const farmData = await this.getFarmData(farmId, fieldId, cropId);
      const healthData = await this.getCropHealthData(fieldId, cropId);
      
      const recommendations = await this.generatePestControlRecommendations(farmData, healthData);
      
      res.json({ recommendations });
    } catch (error) {
      logger.error('Get pest control recommendations error:', error);
      res.status(500).json({ error: 'Failed to get pest control recommendations' });
    }
  }
  
  async generatePestControlRecommendations(farmData, healthData) {
    const recommendations = [];
    
    // Check for pest detection
    if (healthData.pestDetection && healthData.pestDetection.length > 0) {
      for (const pest of healthData.pestDetection) {
        if (pest.severity === 'high') {
          recommendations.push({
            type: 'pest_control',
            title: `Immediate ${pest.name} Control Required`,
            description: `High population of ${pest.name} detected (${pest.count}/plant). Immediate intervention needed to prevent crop damage.`,
            category: 'pest_management',
            priority: 'high',
            conditions: { pest_type: pest.name, population_level: pest.count, severity: pest.severity },
            actions: [
              `Apply appropriate pesticide for ${pest.name}`,
              'Monitor pest populations daily',
              'Consider biological control agents'
            ],
            timeline: { start: 'immediate', monitoring: 'daily for 1 week' },
            expectedOutcome: { pest_reduction: '80-90%', crop_protection: 'effective' },
            resourcesRequired: ['pesticide', 'spraying equipment', 'protective gear', 'monitoring tools'],
            costEstimate: { amount: 80, currency: 'USD', unit: 'per_hectare_treatment' },
            dataSources: ['pest_monitoring', 'damage_assessment', 'weather_conditions']
          });
        } else if (pest.severity === 'medium') {
          recommendations.push({
            type: 'pest_control',
            title: `${pest.name} Monitoring and Prevention`,
            description: `Moderate ${pest.name} population detected. Implement preventive measures and monitoring.`,
            category: 'preventive_care',
            priority: 'medium',
            conditions: { pest_type: pest.name, population_level: pest.count, severity: pest.severity },
            actions: [
              'Increase monitoring frequency',
              'Use pheromone traps',
              'Apply neem oil or other organic treatments'
            ],
            timeline: { start: 'within 48 hours', monitoring: 'every 3 days' },
            expectedOutcome: { pest_prevention: 'effective', population_control: 'maintained' },
            resourcesRequired: ['monitoring traps', 'organic treatments', 'scouting tools'],
            costEstimate: { amount: 40, currency: 'USD', unit: 'per_hectare_preventive' },
            dataSources: ['pest_forecast', 'beneficial_insect_counts', 'crop_stage_assessment']
          });
        }
      }
    }
    
    // Preventive pest control recommendations
    recommendations.push({
      type: 'pest_control',
      title: 'Integrated Pest Management (IPM) Implementation',
      description: 'Implement comprehensive IPM strategy to prevent pest problems and reduce chemical pesticide use.',
      category: 'integrated_management',
      priority: 'medium',
      conditions: { season: 'growing', pest_pressure: 'preventive_mode' },
      actions: [
        'Monitor pest populations weekly',
        'Encourage beneficial insects',
        'Practice crop rotation',
        'Maintain field sanitation'
      ],
      timeline: { start: 'ongoing', duration: 'entire growing season' },
      expectedOutcome: { pesticide_reduction: '50-70%', pest_control: 'sustainable' },
      resourcesRequired: ['monitoring equipment', 'beneficial insects', 'training materials'],
      costEstimate: { amount: 25, currency: 'USD', unit: 'per_hectare_monthly' },
      dataSources: ['pest_surveys', 'beneficial_insect_monitoring', 'crop_rotation_history']
    });
    
    return recommendations;
  }
  
  async getPlantingRecommendations(req, res) {
    try {
      const { farmId, fieldId, cropId } = req.body;
      
      const farmData = await this.getFarmData(farmId, fieldId, cropId);
      const weatherData = await this.getWeatherData(fieldId);
      const soilData = await this.getSoilData(fieldId);
      
      const recommendations = await this.generatePlantingRecommendations(farmData, weatherData, soilData);
      
      res.json({ recommendations });
    } catch (error) {
      logger.error('Get planting recommendations error:', error);
      res.status(500).json({ error: 'Failed to get planting recommendations' });
    }
  }
  
  async generatePlantingRecommendations(farmData, weatherData, soilData) {
    const recommendations = [];
    
    const currentWeather = weatherData.current;
    const forecast = weatherData.forecast;
    
    // Optimal planting window
    const optimalTemp = farmData.cropOptimalTemperature || { min: 20, max: 25 };
    
    if (currentWeather.temperature >= optimalTemp.min && currentWeather.temperature <= optimalTemp.max) {
      recommendations.push({
        type: 'planting',
        title: 'Optimal Planting Conditions',
        description: `Current temperature (${currentWeather.temperature}°C) is optimal for planting ${farmData.cropType}.`,
        category: 'timing',
        priority: 'high',
        conditions: { temperature: currentWeather.temperature, soil_moisture: soilData.moisture },
        actions: [
          'Prepare seedbeds with proper tillage',
          'Plant seeds at recommended depth and spacing',
          'Apply starter fertilizer if needed'
        ],
        timeline: { start: 'within 3 days', duration: 'planting period' },
        expectedOutcome: { germination_rate: '90-95%', establishment_success: 'high' },
        resourcesRequired: ['seeds', 'planting equipment', 'starter fertilizer', 'labor'],
        costEstimate: { amount: 150, currency: 'USD', unit: 'per_hectare_planting' },
        dataSources: ['weather_forecast', 'soil_temperature', 'crop_calendar']
      });
    }
    
    // Frost protection for sensitive crops
    if (forecast.some(day => day.temperature_min < 5)) {
      recommendations.push({
        type: 'planting',
        title: 'Frost Risk - Delay Planting',
        description: 'Frost expected in the coming days. Delay planting until frost risk passes.',
        category: 'risk_management',
        priority: 'high',
        conditions: { frost_risk: true, min_temperature: Math.min(...forecast.map(d => d.temperature_min)) },
        actions: [
          'Monitor weather forecasts closely',
          'Prepare protective measures (row covers, mulch)',
          'Wait until frost-free period confirmed'
        ],
        timeline: { start: 'after frost risk', duration: 'until safe conditions' },
        expectedOutcome: { frost_damage_prevention: '100%', crop_survival: 'guaranteed' },
        resourcesRequired: ['weather_monitoring', 'protective_materials', 'flexible_schedule'],
        costEstimate: { amount: 20, currency: 'USD', unit: 'per_hectare_protection' },
        dataSources: ['weather_forecast', 'frost_warnings', 'crop_frost_tolerance']
      });
    }
    
    return recommendations;
  }
  
  async getHarvestingRecommendations(req, res) {
    try {
      const { farmId, fieldId, cropId } = req.body;
      
      const farmData = await this.getFarmData(farmId, fieldId, cropId);
      const weatherData = await this.getWeatherData(fieldId);
      
      const recommendations = await this.generateHarvestingRecommendations(farmData, weatherData);
      
      res.json({ recommendations });
    } catch (error) {
      logger.error('Get harvesting recommendations error:', error);
      res.status(500).json({ error: 'Failed to get harvesting recommendations' });
    }
  }
  
  async generateHarvestingRecommendations(farmData, weatherData) {
    const recommendations = [];
    
    const forecast = weatherData.forecast;
    
    // Weather-based harvesting recommendations
    const hasRainForecast = forecast.some(day => day.precipitation > 5);
    
    if (hasRainForecast) {
      recommendations.push({
        type: 'harvesting',
        title: 'Harvest Before Rain',
        description: 'Significant rainfall expected. Harvest mature crops before rain to prevent quality deterioration.',
        category: 'weather_protection',
        priority: 'high',
        conditions: { rain_forecast: true, crop_maturity: 'ready' },
        actions: [
          'Accelerate harvesting schedule',
          'Prioritize most mature fields',
          'Ensure proper storage facilities'
        ],
        timeline: { start: 'before rainfall', urgency: '24-48 hours' },
        expectedOutcome: { quality_preservation: 'maintained', post_harvest_losses: 'minimized' },
        resourcesRequired: ['harvesting equipment', 'storage facilities', 'additional labor'],
        costEstimate: { amount: 100, currency: 'USD', unit: 'per_hectare_rush_harvest' },
        dataSources: ['weather_forecast', 'crop_maturity_assessment', 'quality_parameters']
      });
    }
    
    // Optimal harvest timing
    recommendations.push({
      type: 'harvesting',
      title: 'Optimal Harvest Timing Assessment',
      description: 'Monitor crop maturity indicators to determine optimal harvest timing for maximum quality and yield.',
      category: 'quality_optimization',
      priority: 'medium',
      conditions: { crop_maturity: 'approaching_optimal' },
      actions: [
        'Check maturity indicators daily',
        'Test sample fruits/grains for quality',
        'Plan harvest logistics and equipment'
      ],
      timeline: { start: 'when maturity indicators met', duration: 'harvest window' },
      expectedOutcome: { optimal_quality: 'achieved', maximum_yield: 'realized' },
      resourcesRequired: ['quality testing equipment', 'harvest logistics', 'storage preparation'],
      costEstimate: { amount: 50, currency: 'USD', unit: 'per_hectare_monitoring' },
      dataSources: ['maturity_indices', 'quality_testing', 'market_requirements']
    });
    
    return recommendations;
  }
  
  async getRecommendations(req, res) {
    try {
      const { farmId, fieldId, cropId, type, status, limit = 20, offset = 0 } = req.query;
      
      let query = `
        SELECT r.*, c.name as crop_name
        FROM recommendations r
        LEFT JOIN crops c ON r.crop_id = c.id
        WHERE 1=1
      `;
      let params = [];
      let paramCount = 0;
      
      if (farmId) {
        paramCount++;
        query += ` AND r.farm_id = $${paramCount}`;
        params.push(farmId);
      }
      
      if (fieldId) {
        paramCount++;
        query += ` AND r.field_id = $${paramCount}`;
        params.push(fieldId);
      }
      
      if (cropId) {
        paramCount++;
        query += ` AND r.crop_id = $${paramCount}`;
        params.push(cropId);
      }
      
      if (type) {
        paramCount++;
        query += ` AND r.recommendation_type = $${paramCount}`;
        params.push(type);
      }
      
      if (status) {
        paramCount++;
        query += ` AND r.status = $${paramCount}`;
        params.push(status);
      }
      
      paramCount++;
      query += ` ORDER BY r.created_at DESC LIMIT $${paramCount}`;
      params.push(limit);
      
      paramCount++;
      query += ` OFFSET $${paramCount}`;
      params.push(offset);
      
      const result = await this.db.query(query, params);
      
      const recommendations = result.rows.map(rec => ({
        id: rec.id,
        farmId: rec.farm_id,
        fieldId: rec.field_id,
        cropId: rec.crop_id,
        cropName: rec.crop_name,
        type: rec.recommendation_type,
        title: rec.title,
        description: rec.description,
        priority: rec.priority,
        status: rec.status,
        category: rec.category,
        conditions: rec.conditions,
        actions: rec.actions,
        timeline: rec.timeline,
        expectedOutcome: rec.expected_outcome,
        resourcesRequired: rec.resources_required,
        costEstimate: rec.cost_estimate,
        effectivenessScore: rec.effectiveness_score,
        createdAt: rec.created_at,
        expiresAt: rec.expires_at
      }));
      
      res.json({ recommendations });
    } catch (error) {
      logger.error('Get recommendations error:', error);
      res.status(500).json({ error: 'Failed to get recommendations' });
    }
  }
  
  async getRecommendationById(req, res) {
    try {
      const recommendationId = req.params.id;
      
      const result = await this.db.query(`
        SELECT r.*, c.name as crop_name
        FROM recommendations r
        LEFT JOIN crops c ON r.crop_id = c.id
        WHERE r.id = $1
      `, [recommendationId]);
      
      if (result.rows.length === 0) {
        return res.status(404).json({ error: 'Recommendation not found' });
      }
      
      const rec = result.rows[0];
      
      res.json({
        recommendation: {
          id: rec.id,
          farmId: rec.farm_id,
          fieldId: rec.field_id,
          cropId: rec.crop_id,
          cropName: rec.crop_name,
          type: rec.recommendation_type,
          title: rec.title,
          description: rec.description,
          priority: rec.priority,
          status: rec.status,
          category: rec.category,
          conditions: rec.conditions,
          actions: rec.actions,
          timeline: rec.timeline,
          expectedOutcome: rec.expected_outcome,
          resourcesRequired: rec.resources_required,
          costEstimate: rec.cost_estimate,
          effectivenessScore: rec.effectiveness_score,
          dataSources: rec.data_sources,
          createdAt: rec.created_at,
          updatedAt: rec.updated_at,
          expiresAt: rec.expires_at
        }
      });
    } catch (error) {
      logger.error('Get recommendation by ID error:', error);
      res.status(500).json({ error: 'Failed to get recommendation' });
    }
  }
  
  async updateRecommendationStatus(req, res) {
    try {
      const recommendationId = req.params.id;
      const { status, effectivenessRating, feedback } = req.body;
      
      const validStatuses = ['pending', 'in_progress', 'completed', 'cancelled', 'expired'];
      
      if (!validStatuses.includes(status)) {
        return res.status(400).json({ error: 'Invalid status' });
      }
      
      await this.db.query(
        'UPDATE recommendations SET status = $1, updated_at = CURRENT_TIMESTAMP WHERE id = $2',
        [status, recommendationId]
      );
      
      // Add feedback if provided
      if (effectivenessRating && feedback) {
        await this.db.query(
          'INSERT INTO recommendation_feedback (recommendation_id, user_id, effectiveness_rating, feedback_text, implemented_at) VALUES ($1, $2, $3, $4, $5)',
          [recommendationId, req.user.userId, effectivenessRating, feedback, new Date()]
        );
      }
      
      logger.info(`Recommendation ${recommendationId} status updated to ${status}`);
      
      res.json({ message: 'Recommendation status updated successfully' });
    } catch (error) {
      logger.error('Update recommendation status error:', error);
      res.status(500).json({ error: 'Failed to update recommendation status' });
    }
  }
  
  // Helper methods for data retrieval
  async getFarmData(farmId, fieldId, cropId) {
    // This would integrate with farm management service
    return {
      farmId,
      fieldId,
      cropId,
      cropType: 'tomato', // Sample data
      growthStage: 'fruiting',
      cropOptimalTemperature: { min: 18, max: 27 }
    };
  }
  
  async getWeatherData(fieldId) {
    try {
      const response = await axios.get(`http://weather-service:3005/current`, {
        params: { fieldId }
      });
      
      return response.data;
    } catch (error) {
      logger.error('Get weather data error:', error);
      return { current: { temperature: 25, humidity: 60 }, forecast: [] };
    }
  }
  
  async getSoilData(fieldId) {
    // This would integrate with soil analysis service
    return {
      moisture: 45,
      nitrogen: 40,
      phosphorus: 30,
      potassium: 35,
      ph: 6.5
    };
  }
  
  async getCropHealthData(fieldId, cropId) {
    // This would integrate with crop detection service
    return {
      healthScore: 75,
      nutrientDeficiencies: false,
      pestDetection: []
    };
  }
  
  async cacheRecommendations(farmId, recommendations) {
    const cacheKey = `recommendations:${farmId}`;
    await this.redis.setex(cacheKey, 3600, JSON.stringify(recommendations)); // Cache for 1 hour
  }
  
  start() {
    this.app.listen(this.port, () => {
      logger.info(`Recommendation service running on port ${this.port}`);
    });
  }
}

// Start the service
if (require.main === module) {
  const recommendationService = new RecommendationService();
  recommendationService.start();
}

module.exports = RecommendationService;