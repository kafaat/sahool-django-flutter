-- GeoFarm Platform Database Initialization
-- This script creates the initial database structure for all services

-- Create databases for different services
CREATE DATABASE geofarm_users;
CREATE DATABASE geofarm_notifications;
CREATE DATABASE geofarm_weather;
CREATE DATABASE geofarm_crops;
CREATE DATABASE geofarm_recommendations;
CREATE DATABASE geofarm_farms;
CREATE DATABASE geofarm_iot;
CREATE DATABASE geofarm_geochat;

-- Connect to main database
\c geofarm_main;

-- Create extension for UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create extension for PostGIS (spatial data)
CREATE EXTENSION IF NOT EXISTS postgis;

-- Create extension for JSON operations
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create shared users table (if not exists in user service)
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
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

-- Create shared farms table (if not exists in farm service)
CREATE TABLE IF NOT EXISTS farms (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(200) NOT NULL,
    owner_id UUID REFERENCES users(id),
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

-- Create shared crops table
CREATE TABLE IF NOT EXISTS crops (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    scientific_name VARCHAR(200),
    category VARCHAR(50),
    optimal_conditions JSONB DEFAULT '{}',
    growth_stages JSONB DEFAULT '[]',
    common_diseases JSONB DEFAULT '[]',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert default crop data
INSERT INTO crops (name, scientific_name, category, optimal_conditions, growth_stages, common_diseases) VALUES
('Wheat', 'Triticum aestivum', 'Cereal', '{"temperature": {"min": 15, "max": 25, "optimal": 20}, "humidity": {"min": 40, "max": 70, "optimal": 60}, "soil_ph": {"min": 6.0, "max": 7.5, "optimal": 6.5}, "water_requirement": "Moderate"}', '[{"stage": "Germination", "days": 7, "characteristics": ["Seed sprouting", "Root development"]}, {"stage": "Tillering", "days": 30, "characteristics": ["Multiple shoots", "Leaf development"]}, {"stage": "Stem Extension", "days": 30, "characteristics": ["Rapid stem growth", "Node formation"]}, {"stage": "Heading", "days": 15, "characteristics": ["Ear emergence", "Flowering"]}, {"stage": "Grain Filling", "days": 35, "characteristics": ["Kernel development", "Starch accumulation"]}, {"stage": "Maturity", "days": 15, "characteristics": ["Grain hardening", "Plant senescence"]}]', '[{"name": "Rust", "symptoms": ["Orange-brown pustules", "Leaf yellowing"], "treatment": "Fungicide application"}, {"name": "Powdery Mildew", "symptoms": ["White powdery coating", "Stunted growth"], "treatment": "Improve air circulation"}, {"name": "Fusarium Head Blight", "symptoms": ["Pinkish discoloration", "Shriveled grains"], "treatment": "Crop rotation"}]'),
('Corn', 'Zea mays', 'Cereal', '{"temperature": {"min": 18, "max": 32, "optimal": 25}, "humidity": {"min": 50, "max": 80, "optimal": 70}, "soil_ph": {"min": 5.8, "max": 7.0, "optimal": 6.2}, "water_requirement": "High"}', '[{"stage": "Germination", "days": 10, "characteristics": ["Seed sprouting", "Root establishment"]}, {"stage": "Vegetative", "days": 40, "characteristics": ["Leaf development", "Stem elongation"]}, {"stage": "Reproductive", "days": 20, "characteristics": ["Tassel emergence", "Silking"]}, {"stage": "Grain Filling", "days": 60, "characteristics": ["Kernel development", "Starch accumulation"]}, {"stage": "Maturity", "days": 20, "characteristics": ["Grain hardening", "Plant drying"]}]', '[{"name": "Northern Corn Leaf Blight", "symptoms": ["Long lesions", "Gray-green spots"], "treatment": "Fungicide application"}, {"name": "Gray Leaf Spot", "symptoms": ["Small brown spots", "Leaf necrosis"], "treatment": "Crop rotation"}, {"name": "Common Rust", "symptoms": ["Reddish-brown pustules", "Leaf damage"], "treatment": "Resistant varieties"}]'),
('Tomato', 'Solanum lycopersicum', 'Vegetable', '{"temperature": {"min": 18, "max": 27, "optimal": 22}, "humidity": {"min": 60, "max": 80, "optimal": 70}, "soil_ph": {"min": 6.0, "max": 6.8, "optimal": 6.4}, "water_requirement": "Moderate to High"}', '[{"stage": "Germination", "days": 7, "characteristics": ["Seed sprouting", "Cotyledon emergence"]}, {"stage": "Seedling", "days": 20, "characteristics": ["True leaf development", "Root growth"]}, {"stage": "Vegetative", "days": 30, "characteristics": ["Rapid growth", "Branching"]}, {"stage": "Flowering", "days": 15, "characteristics": ["Flower cluster formation", "Pollination"]}, {"stage": "Fruiting", "days": 60, "characteristics": ["Fruit development", "Color change"]}, {"stage": "Harvest", "days": 30, "characteristics": ["Fruit ripening", "Continuous harvest"]}]', '[{"name": "Early Blight", "symptoms": ["Dark concentric rings", "Leaf yellowing"], "treatment": "Fungicide application"}, {"name": "Late Blight", "symptoms": ["Water-soaked lesions", "White mold"], "treatment": "Copper-based fungicides"}, {"name": "Bacterial Spot", "symptoms": ["Small dark spots", "Leaf holes"], "treatment": "Copper sprays"}]');

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_farms_owner ON farms(owner_id);
CREATE INDEX IF NOT EXISTS idx_farms_location ON farms USING GIN(location);
CREATE INDEX IF NOT EXISTS idx_crops_category ON crops(category);

-- Create system settings table
CREATE TABLE IF NOT EXISTS system_settings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    key VARCHAR(100) UNIQUE NOT NULL,
    value JSONB NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert default system settings
INSERT INTO system_settings (key, value, description) VALUES
('platform_name', '"GeoFarm Platform"', 'Platform display name'),
('platform_version', '"2.0.0"', 'Current platform version'),
('max_file_upload_size', '{"value": 10485760, "unit": "bytes"}', 'Maximum file upload size'),
('default_timezone', '"UTC"', 'Default timezone for the platform'),
('session_timeout', '{"value": 3600, "unit": "seconds"}', 'User session timeout'),
('password_min_length', '8', 'Minimum password length requirement'),
('enable_notifications', 'true', 'Whether to enable system notifications'),
('enable_weather_alerts', 'true', 'Whether to enable weather alerts'),
('enable_iot_monitoring', 'true', 'Whether to enable IoT device monitoring'),
('max_devices_per_user', '10', 'Maximum number of devices per user');

-- Create audit log table
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50) NOT NULL,
    resource_id UUID,
    details JSONB DEFAULT '{}',
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action);

-- Create API usage tracking table
CREATE TABLE IF NOT EXISTS api_usage (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    endpoint VARCHAR(200) NOT NULL,
    method VARCHAR(10) NOT NULL,
    status_code INTEGER,
    response_time INTEGER,
    request_size INTEGER,
    response_size INTEGER,
    ip_address INET,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_api_usage_user_id ON api_usage(user_id);
CREATE INDEX IF NOT EXISTS idx_api_usage_endpoint ON api_usage(endpoint);
CREATE INDEX IF NOT EXISTS idx_api_usage_created_at ON api_usage(created_at DESC);

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO postgres;

-- Create read-only user for analytics
CREATE USER IF NOT EXISTS geofarm_analytics WITH PASSWORD 'analytics_password';
GRANT CONNECT ON DATABASE geofarm_main TO geofarm_analytics;
GRANT USAGE ON SCHEMA public TO geofarm_analytics;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO geofarm_analytics;

-- Create service user for microservices
CREATE USER IF NOT EXISTS geofarm_services WITH PASSWORD 'services_password';
GRANT CONNECT ON DATABASE geofarm_main TO geofarm_services;
GRANT USAGE ON SCHEMA public TO geofarm_services;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO geofarm_services;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO geofarm_services;

-- Create backup user
CREATE USER IF NOT EXISTS geofarm_backup WITH PASSWORD 'backup_password';
GRANT CONNECT ON DATABASE geofarm_main TO geofarm_backup;
GRANT USAGE ON SCHEMA public TO geofarm_backup;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO geofarm_backup;

-- Set up automatic cleanup jobs (if using pgAgent or similar)
-- Clean up old audit logs (older than 1 year)
-- Clean up old API usage data (older than 3 months)
-- Clean up expired sessions and tokens

-- Create function to clean up old data
CREATE OR REPLACE FUNCTION cleanup_old_data()
RETURNS void AS $$
BEGIN
    -- Delete audit logs older than 1 year
    DELETE FROM audit_logs WHERE created_at < NOW() - INTERVAL '1 year';
    
    -- Delete API usage data older than 3 months
    DELETE FROM api_usage WHERE created_at < NOW() - INTERVAL '3 months';
    
    -- Clean up old user sessions (older than 30 days)
    -- This would be in the user service database
    
    -- Clean up old notifications (older than 6 months)
    -- This would be in the notification service database
    
    RAISE NOTICE 'Cleanup completed at %', NOW();
END;
$$ LANGUAGE plpgsql;

-- Create indexes for commonly queried fields
CREATE INDEX IF NOT EXISTS idx_audit_logs_resource ON audit_logs(resource_type, resource_id);
CREATE INDEX IF NOT EXISTS idx_api_usage_status ON api_usage(status_code);
CREATE INDEX IF NOT EXISTS idx_system_settings_key ON system_settings(key);

-- Create materialized views for performance (if needed)
-- These would be created based on actual usage patterns

-- Set up monitoring and alerts
-- Create function to check system health
CREATE OR REPLACE FUNCTION check_system_health()
RETURNS TABLE(check_name text, status text, details jsonb) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        'database_size'::text,
        CASE 
            WHEN pg_database_size(current_database()) > 10737418240 THEN 'warning'
            ELSE 'healthy'
        END,
        jsonb_build_object(
            'size_bytes', pg_database_size(current_database()),
            'size_human', pg_size_pretty(pg_database_size(current_database()))
        );
    
    RETURN QUERY
    SELECT 
        'connection_count'::text,
        CASE 
            WHEN count(*) > 80 THEN 'warning'
            ELSE 'healthy'
        END,
        jsonb_build_object('connections', count(*))
    FROM pg_stat_activity;
    
    RETURN QUERY
    SELECT 
        'replication_lag'::text,
        'healthy'::text,
        jsonb_build_object('lag', 0);
END;
$$ LANGUAGE plpgsql;

-- Grant execute permissions
GRANT EXECUTE ON FUNCTION check_system_health() TO geofarm_analytics;
GRANT EXECUTE ON FUNCTION cleanup_old_data() TO geofarm_services;

-- Create monitoring user
CREATE USER IF NOT EXISTS geofarm_monitoring WITH PASSWORD 'monitoring_password';
GRANT CONNECT ON DATABASE geofarm_main TO geofarm_monitoring;
GRANT USAGE ON SCHEMA public TO geofarm_monitoring;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO geofarm_monitoring;
GRANT EXECUTE ON FUNCTION check_system_health() TO geofarm_monitoring;

-- Final notice
RAISE NOTICE 'GeoFarm Platform database initialization completed successfully!';
RAISE NOTICE 'Remember to update the following:';
RAISE NOTICE '1. Replace placeholder API keys in environment variables';
RAISE NOTICE '2. Configure SSL certificates for production';
RAISE NOTICE '3. Set up proper email SMTP credentials';
RAISE NOTICE '4. Configure backup and monitoring systems';
RAISE NOTICE '5. Review and adjust security settings for production use';