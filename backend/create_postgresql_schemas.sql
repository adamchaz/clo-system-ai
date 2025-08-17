-- PostgreSQL Migration Schemas
-- CLO System SQLite to PostgreSQL Migration
-- Created from analysis of 4 SQLite databases (258,989 total rows, 50MB)

-- =====================================================
-- CORRELATION DATA (45.2MB, 238,144 rows)
-- =====================================================

CREATE TABLE IF NOT EXISTS asset_correlations (
    id SERIAL PRIMARY KEY,
    asset1_id VARCHAR(50) NOT NULL,
    asset2_id VARCHAR(50) NOT NULL,
    correlation_value DECIMAL(10, 8) NOT NULL,
    correlation_type VARCHAR(20),
    data_source VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for correlation table (performance critical - 238K rows)
CREATE INDEX IF NOT EXISTS idx_correlations_asset1_id ON asset_correlations(asset1_id);
CREATE INDEX IF NOT EXISTS idx_correlations_asset2_id ON asset_correlations(asset2_id);
CREATE INDEX IF NOT EXISTS idx_correlations_assets_pair ON asset_correlations(asset1_id, asset2_id);
CREATE INDEX IF NOT EXISTS idx_correlations_type ON asset_correlations(correlation_type);
CREATE INDEX IF NOT EXISTS idx_correlations_value ON asset_correlations(correlation_value);

-- Unique constraint for correlation pairs
ALTER TABLE asset_correlations ADD CONSTRAINT unique_asset_correlation 
UNIQUE (asset1_id, asset2_id, correlation_type);

-- =====================================================
-- MAG SCENARIO DATA (4.5MB, 19,795 rows)
-- =====================================================

CREATE TABLE IF NOT EXISTS scenario_inputs (
    id SERIAL PRIMARY KEY,
    scenario_name VARCHAR(50) NOT NULL,
    scenario_type VARCHAR(20),
    section_name VARCHAR(100),
    parameter_name VARCHAR(150) NOT NULL,
    parameter_value TEXT,
    parameter_type VARCHAR(20),
    row_number INTEGER,
    column_number INTEGER,
    data_source VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for scenario table
CREATE INDEX IF NOT EXISTS idx_scenarios_name ON scenario_inputs(scenario_name);
CREATE INDEX IF NOT EXISTS idx_scenarios_type ON scenario_inputs(scenario_type);
CREATE INDEX IF NOT EXISTS idx_scenarios_section ON scenario_inputs(section_name);
CREATE INDEX IF NOT EXISTS idx_scenarios_parameter ON scenario_inputs(parameter_name);
CREATE INDEX IF NOT EXISTS idx_scenarios_position ON scenario_inputs(row_number, column_number);

-- =====================================================
-- MODEL CONFIG DATA (120KB, 356 rows)
-- =====================================================

CREATE TABLE IF NOT EXISTS model_parameters (
    id SERIAL PRIMARY KEY,
    config_name VARCHAR(50) NOT NULL,
    section_name VARCHAR(100),
    parameter_name VARCHAR(200) NOT NULL,
    parameter_value TEXT,
    parameter_type VARCHAR(20),
    description TEXT,
    row_number INTEGER,
    column_number INTEGER,
    is_active BOOLEAN DEFAULT TRUE,  -- Convert VARCHAR(10) to BOOLEAN
    data_source VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for model config table
CREATE INDEX IF NOT EXISTS idx_config_name ON model_parameters(config_name);
CREATE INDEX IF NOT EXISTS idx_config_section ON model_parameters(section_name);
CREATE INDEX IF NOT EXISTS idx_config_parameter ON model_parameters(parameter_name);
CREATE INDEX IF NOT EXISTS idx_config_active ON model_parameters(is_active);

-- =====================================================
-- REFERENCE DATA (188KB, 694 rows)
-- =====================================================

CREATE TABLE IF NOT EXISTS reference_data (
    id SERIAL PRIMARY KEY,
    section_name VARCHAR(100),
    row_number INTEGER,
    correlation_date DATE,
    raw_data JSONB,  -- Use JSONB for better performance
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for reference table
CREATE INDEX IF NOT EXISTS idx_reference_section ON reference_data(section_name);
CREATE INDEX IF NOT EXISTS idx_reference_row ON reference_data(row_number);
CREATE INDEX IF NOT EXISTS idx_reference_date ON reference_data(correlation_date);
CREATE INDEX IF NOT EXISTS idx_reference_jsonb ON reference_data USING GIN(raw_data);

-- =====================================================
-- PERFORMANCE OPTIMIZATIONS
-- =====================================================

-- Enable autovacuum for all tables
ALTER TABLE asset_correlations SET (
    autovacuum_vacuum_scale_factor = 0.1,
    autovacuum_analyze_scale_factor = 0.05
);

ALTER TABLE scenario_inputs SET (
    autovacuum_vacuum_scale_factor = 0.1,
    autovacuum_analyze_scale_factor = 0.05
);

-- =====================================================
-- TABLE COMMENTS
-- =====================================================

COMMENT ON TABLE asset_correlations IS 'Asset correlation matrix data migrated from SQLite (238,144 rows)';
COMMENT ON TABLE scenario_inputs IS 'MAG waterfall scenario parameters migrated from SQLite (19,795 rows)';
COMMENT ON TABLE model_parameters IS 'Model configuration settings migrated from SQLite (356 rows)';
COMMENT ON TABLE reference_data IS 'Reference lookup data migrated from SQLite (694 rows)';

-- =====================================================
-- MIGRATION METADATA
-- =====================================================

CREATE TABLE IF NOT EXISTS migration_metadata (
    id SERIAL PRIMARY KEY,
    table_name VARCHAR(100) NOT NULL,
    source_database VARCHAR(100) NOT NULL,
    rows_migrated INTEGER NOT NULL,
    migration_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    validation_checksum VARCHAR(64),
    migration_notes TEXT
);

INSERT INTO migration_metadata (table_name, source_database, rows_migrated, migration_notes) VALUES
('asset_correlations', 'clo_correlations.db', 238144, 'Core correlation matrix data'),
('scenario_inputs', 'clo_mag_scenarios.db', 19795, 'MAG waterfall scenario parameters'),
('model_parameters', 'clo_model_config.db', 356, 'Model configuration settings'),
('reference_data', 'clo_reference_quick.db', 694, 'Reference lookup data');

-- Create application user if not exists
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'clo_app_user') THEN
        CREATE USER clo_app_user WITH PASSWORD 'clo_app_password';
    END IF;
END
$$;

-- Grant permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO clo_app_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO clo_app_user;