-- CLO Management System Database Initialization
-- This script sets up the production PostgreSQL database with proper permissions and extensions

-- Create database (if not exists)
-- SELECT 'CREATE DATABASE clo_management' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'clo_management')\gexec

-- Connect to the database
\c clo_management;

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- Create schemas for organization
CREATE SCHEMA IF NOT EXISTS core;      -- Core business entities
CREATE SCHEMA IF NOT EXISTS calc;      -- Calculation results
CREATE SCHEMA IF NOT EXISTS config;    -- Configuration data
CREATE SCHEMA IF NOT EXISTS audit;     -- Audit trails
CREATE SCHEMA IF NOT EXISTS cache;     -- Cached data

-- Grant permissions to clo_user
GRANT ALL PRIVILEGES ON SCHEMA core TO clo_user;
GRANT ALL PRIVILEGES ON SCHEMA calc TO clo_user;
GRANT ALL PRIVILEGES ON SCHEMA config TO clo_user;
GRANT ALL PRIVILEGES ON SCHEMA audit TO clo_user;
GRANT ALL PRIVILEGES ON SCHEMA cache TO clo_user;

-- Set default schema search path
ALTER USER clo_user SET search_path TO public, core, calc, config, audit, cache;

-- Create audit function for tracking changes
CREATE OR REPLACE FUNCTION audit.audit_trigger_function()
RETURNS TRIGGER AS $$
BEGIN
    -- Insert audit record
    INSERT INTO audit.table_changes (
        table_name,
        operation,
        old_values,
        new_values,
        changed_by,
        changed_at
    ) VALUES (
        TG_TABLE_NAME,
        TG_OP,
        CASE WHEN TG_OP = 'DELETE' THEN row_to_json(OLD) ELSE NULL END,
        CASE WHEN TG_OP IN ('INSERT', 'UPDATE') THEN row_to_json(NEW) ELSE NULL END,
        current_user,
        current_timestamp
    );
    
    -- Return appropriate record
    RETURN CASE 
        WHEN TG_OP = 'DELETE' THEN OLD 
        ELSE NEW 
    END;
END;
$$ LANGUAGE plpgsql;

-- Create audit table
CREATE TABLE IF NOT EXISTS audit.table_changes (
    id SERIAL PRIMARY KEY,
    table_name TEXT NOT NULL,
    operation TEXT NOT NULL CHECK (operation IN ('INSERT', 'UPDATE', 'DELETE')),
    old_values JSONB,
    new_values JSONB,
    changed_by TEXT NOT NULL,
    changed_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create index on audit table
CREATE INDEX IF NOT EXISTS idx_table_changes_table_time 
ON audit.table_changes (table_name, changed_at);

-- Create performance monitoring functions
CREATE OR REPLACE FUNCTION config.get_database_stats()
RETURNS TABLE (
    stat_name TEXT,
    stat_value NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        'total_connections' as stat_name,
        (SELECT count(*) FROM pg_stat_activity)::numeric as stat_value
    UNION ALL
    SELECT 
        'active_connections' as stat_name,
        (SELECT count(*) FROM pg_stat_activity WHERE state = 'active')::numeric as stat_value
    UNION ALL
    SELECT 
        'database_size_mb' as stat_name,
        (SELECT pg_database_size('clo_management') / 1024 / 1024)::numeric as stat_value;
END;
$$ LANGUAGE plpgsql;

-- Create function for cleaning old audit records
CREATE OR REPLACE FUNCTION audit.cleanup_old_audits(retention_days INTEGER DEFAULT 90)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM audit.table_changes 
    WHERE changed_at < (CURRENT_TIMESTAMP - (retention_days || ' days')::INTERVAL);
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Grant execute permissions
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA config TO clo_user;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA audit TO clo_user;

-- Set up connection limits and timeouts
ALTER USER clo_user CONNECTION LIMIT 50;

-- Optimize PostgreSQL settings for CLO workload
-- (These are handled in docker-compose.yml, but documented here)

COMMENT ON DATABASE clo_management IS 'CLO Portfolio Management System - Production Database';

-- Log the initialization
INSERT INTO audit.table_changes (
    table_name, 
    operation, 
    new_values, 
    changed_by, 
    changed_at
) VALUES (
    'database_initialization',
    'INSERT',
    '{"event": "database_initialized", "version": "1.0.0"}'::jsonb,
    'system',
    CURRENT_TIMESTAMP
);