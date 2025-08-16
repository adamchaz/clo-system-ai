#!/usr/bin/env python3
"""
SQLite to PostgreSQL Migration Script
Migrates CLO system data from SQLite databases to PostgreSQL operational database.
"""

import sys
import os
sys.path.append('.')

import sqlite3
import logging
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text, Table, MetaData
from app.core.database import engine
from datetime import datetime
from typing import Dict, List, Tuple, Any
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SQLiteToPostgreSQLMigrator:
    """Migrates data from SQLite databases to PostgreSQL operational database"""
    
    def __init__(self):
        self.pg_engine = engine
        self.Session = sessionmaker(bind=self.pg_engine)
        self.migration_report = {
            'start_time': datetime.now().isoformat(),
            'databases_processed': [],
            'total_records_migrated': 0,
            'errors': []
        }
        
    def get_sqlite_databases(self) -> List[str]:
        """Get list of SQLite database files to migrate"""
        db_path = 'data/databases/'
        databases = []
        
        if os.path.exists(db_path):
            for file in os.listdir(db_path):
                if file.endswith('.db') and file.startswith('clo_'):
                    databases.append(os.path.join(db_path, file))
        
        logger.info(f"Found {len(databases)} SQLite databases to migrate")
        return databases
    
    def create_postgresql_tables(self):
        """Create PostgreSQL tables for migrated data"""
        session = self.Session()
        
        try:
            # Asset Correlations Table
            session.execute(text("""
                CREATE TABLE IF NOT EXISTS asset_correlations_migrated (
                    id SERIAL PRIMARY KEY,
                    borrower_1 VARCHAR(100) NOT NULL,
                    borrower_2 VARCHAR(100) NOT NULL,
                    correlation_coefficient DECIMAL(10,8),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(borrower_1, borrower_2)
                )
            """))
            
            # MAG Scenarios Table - using TEXT for parameter_value to handle mixed data types
            session.execute(text("""
                CREATE TABLE IF NOT EXISTS mag_scenarios_migrated (
                    id SERIAL PRIMARY KEY,
                    scenario_name VARCHAR(100),
                    parameter_name VARCHAR(200),
                    parameter_value TEXT,
                    time_period VARCHAR(50),
                    data_type VARCHAR(50),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            # Model Configuration Table
            session.execute(text("""
                CREATE TABLE IF NOT EXISTS model_config_migrated (
                    id SERIAL PRIMARY KEY,
                    parameter_name VARCHAR(200),
                    parameter_value TEXT,
                    parameter_type VARCHAR(50),
                    description TEXT,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            # Reference Data Table
            session.execute(text("""
                CREATE TABLE IF NOT EXISTS reference_data_migrated (
                    id SERIAL PRIMARY KEY,
                    category VARCHAR(100),
                    code VARCHAR(50),
                    description TEXT,
                    value TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            session.commit()
            logger.info("PostgreSQL migration tables created successfully")
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating PostgreSQL tables: {e}")
            raise
        finally:
            session.close()
    
    def migrate_asset_correlations(self, sqlite_db_path: str) -> int:
        """Migrate asset correlation data"""
        logger.info(f"Migrating asset correlations from {sqlite_db_path}")
        
        sqlite_conn = sqlite3.connect(sqlite_db_path)
        sqlite_cursor = sqlite_conn.cursor()
        
        pg_session = self.Session()
        records_migrated = 0
        
        try:
            # Get data from SQLite - using actual column names
            sqlite_cursor.execute("""
                SELECT asset1_id, asset2_id, correlation_value
                FROM asset_correlations
            """)
            
            batch_size = 1000
            batch = []
            
            while True:
                rows = sqlite_cursor.fetchmany(batch_size)
                if not rows:
                    break
                
                for row in rows:
                    batch.append({
                        'borrower_1': row[0],
                        'borrower_2': row[1], 
                        'correlation_coefficient': row[2]
                    })
                
                # Insert batch into PostgreSQL
                if batch:
                    pg_session.execute(text("""
                        INSERT INTO asset_correlations_migrated 
                        (borrower_1, borrower_2, correlation_coefficient)
                        VALUES (:borrower_1, :borrower_2, :correlation_coefficient)
                        ON CONFLICT (borrower_1, borrower_2) DO UPDATE SET
                        correlation_coefficient = EXCLUDED.correlation_coefficient
                    """), batch)
                    
                    records_migrated += len(batch)
                    batch = []
                    
                    if records_migrated % 10000 == 0:
                        logger.info(f"Migrated {records_migrated:,} correlations...")
            
            pg_session.commit()
            logger.info(f"Asset correlations migration complete: {records_migrated:,} records")
            
        except Exception as e:
            pg_session.rollback()
            logger.error(f"Error migrating asset correlations: {e}")
            raise
        finally:
            sqlite_conn.close()
            pg_session.close()
        
        return records_migrated
    
    def migrate_mag_scenarios(self, sqlite_db_path: str) -> int:
        """Migrate MAG scenario data"""
        logger.info(f"Migrating MAG scenarios from {sqlite_db_path}")
        
        sqlite_conn = sqlite3.connect(sqlite_db_path)
        sqlite_cursor = sqlite_conn.cursor()
        
        pg_session = self.Session()
        records_migrated = 0
        
        try:
            # Get data from SQLite - using actual column names
            sqlite_cursor.execute("""
                SELECT scenario_name, parameter_name, parameter_value,
                       section_name, parameter_type
                FROM scenario_inputs
            """)
            
            batch_size = 1000
            batch = []
            
            while True:
                rows = sqlite_cursor.fetchmany(batch_size)
                if not rows:
                    break
                
                for row in rows:
                    batch.append({
                        'scenario_name': row[0],
                        'parameter_name': row[1],
                        'parameter_value': row[2],
                        'time_period': row[3],  # section_name -> time_period
                        'data_type': row[4]     # parameter_type -> data_type
                    })
                
                # Insert batch into PostgreSQL
                if batch:
                    pg_session.execute(text("""
                        INSERT INTO mag_scenarios_migrated 
                        (scenario_name, parameter_name, parameter_value, time_period, data_type)
                        VALUES (:scenario_name, :parameter_name, :parameter_value, :time_period, :data_type)
                    """), batch)
                    
                    records_migrated += len(batch)
                    batch = []
            
            pg_session.commit()
            logger.info(f"MAG scenarios migration complete: {records_migrated:,} records")
            
        except Exception as e:
            pg_session.rollback()
            logger.error(f"Error migrating MAG scenarios: {e}")
            raise
        finally:
            sqlite_conn.close()
            pg_session.close()
        
        return records_migrated
    
    def migrate_model_config(self, sqlite_db_path: str) -> int:
        """Migrate model configuration data"""
        logger.info(f"Migrating model config from {sqlite_db_path}")
        
        sqlite_conn = sqlite3.connect(sqlite_db_path)
        sqlite_cursor = sqlite_conn.cursor()
        
        pg_session = self.Session()
        records_migrated = 0
        
        try:
            # Get data from SQLite - using actual column names
            sqlite_cursor.execute("""
                SELECT parameter_name, parameter_value, parameter_type,
                       description, is_active
                FROM model_parameters
            """)
            
            batch = []
            for row in sqlite_cursor.fetchall():
                # Convert text values to boolean
                is_active_val = True  # default
                if row[4] is not None:
                    if isinstance(row[4], str):
                        is_active_val = row[4].lower() in ('active', 'true', '1', 'yes')
                    else:
                        is_active_val = bool(row[4])
                
                batch.append({
                    'parameter_name': row[0],
                    'parameter_value': row[1],
                    'parameter_type': row[2],
                    'description': row[3],
                    'is_active': is_active_val
                })
            
            # Insert into PostgreSQL
            if batch:
                pg_session.execute(text("""
                    INSERT INTO model_config_migrated 
                    (parameter_name, parameter_value, parameter_type, description, is_active)
                    VALUES (:parameter_name, :parameter_value, :parameter_type, :description, :is_active)
                """), batch)
                
                records_migrated = len(batch)
            
            pg_session.commit()
            logger.info(f"Model config migration complete: {records_migrated:,} records")
            
        except Exception as e:
            pg_session.rollback()
            logger.error(f"Error migrating model config: {e}")
            raise
        finally:
            sqlite_conn.close()
            pg_session.close()
        
        return records_migrated
    
    def check_existing_asset_data(self) -> bool:
        """Check if assets are already migrated in PostgreSQL"""
        session = self.Session()
        try:
            result = session.execute(text("SELECT COUNT(*) FROM assets")).scalar()
            logger.info(f"Found {result:,} assets already in PostgreSQL")
            return result > 0
        except Exception as e:
            logger.error(f"Error checking existing assets: {e}")
            return False
        finally:
            session.close()
    
    def migrate_database(self, sqlite_db_path: str) -> Dict[str, Any]:
        """Migrate a single SQLite database"""
        db_name = os.path.basename(sqlite_db_path)
        logger.info(f"Starting migration of {db_name}")
        
        db_result = {
            'database': db_name,
            'tables_migrated': [],
            'records_migrated': 0,
            'errors': []
        }
        
        try:
            if 'correlations' in db_name:
                records = self.migrate_asset_correlations(sqlite_db_path)
                db_result['tables_migrated'].append('asset_correlations')
                db_result['records_migrated'] = records
                
            elif 'mag_scenarios' in db_name:
                records = self.migrate_mag_scenarios(sqlite_db_path)
                db_result['tables_migrated'].append('scenario_inputs')
                db_result['records_migrated'] = records
                
            elif 'model_config' in db_name:
                records = self.migrate_model_config(sqlite_db_path)
                db_result['tables_migrated'].append('model_parameters')
                db_result['records_migrated'] = records
                
            elif 'assets_production' in db_name:
                # Assets already exist in PostgreSQL
                logger.info(f"Skipping {db_name} - assets already migrated to PostgreSQL")
                db_result['records_migrated'] = 0
                db_result['tables_migrated'].append('assets (already in PostgreSQL)')
                
            elif 'reference_data' in db_name:
                logger.info(f"Skipping {db_name} - reference tables are empty")
                db_result['records_migrated'] = 0
                
        except Exception as e:
            error_msg = f"Failed to migrate {db_name}: {str(e)}"
            logger.error(error_msg)
            db_result['errors'].append(error_msg)
        
        return db_result
    
    def run_migration(self):
        """Execute complete migration from SQLite to PostgreSQL"""
        logger.info("Starting SQLite to PostgreSQL migration")
        
        try:
            # Create PostgreSQL tables
            self.create_postgresql_tables()
            
            # Check existing data
            assets_exist = self.check_existing_asset_data()
            
            # Get SQLite databases
            databases = self.get_sqlite_databases()
            
            if not databases:
                logger.warning("No SQLite databases found for migration")
                return
            
            # Migrate each database
            for db_path in databases:
                db_result = self.migrate_database(db_path)
                self.migration_report['databases_processed'].append(db_result)
                self.migration_report['total_records_migrated'] += db_result['records_migrated']
            
            # Finalize report
            self.migration_report['end_time'] = datetime.now().isoformat()
            self.migration_report['status'] = 'COMPLETED'
            
            # Generate report
            self.generate_migration_report()
            
            logger.info("Migration completed successfully!")
            logger.info(f"Total records migrated: {self.migration_report['total_records_migrated']:,}")
            
        except Exception as e:
            self.migration_report['status'] = 'FAILED'
            self.migration_report['end_time'] = datetime.now().isoformat()
            self.migration_report['errors'].append(str(e))
            logger.error(f"Migration failed: {e}")
            raise
    
    def generate_migration_report(self):
        """Generate comprehensive migration report"""
        report_file = f"migration_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(report_file, 'w') as f:
            json.dump(self.migration_report, f, indent=2)
        
        logger.info(f"Migration report saved: {report_file}")
        
        # Print summary
        print("\n" + "="*60)
        print("MIGRATION SUMMARY")
        print("="*60)
        print(f"Status: {self.migration_report['status']}")
        print(f"Total Records Migrated: {self.migration_report['total_records_migrated']:,}")
        print(f"Databases Processed: {len(self.migration_report['databases_processed'])}")
        
        for db_result in self.migration_report['databases_processed']:
            print(f"\n{db_result['database']}: {db_result['records_migrated']:,} records")
            if db_result['errors']:
                print(f"  Errors: {len(db_result['errors'])}")
        
        print("="*60)


if __name__ == "__main__":
    migrator = SQLiteToPostgreSQLMigrator()
    migrator.run_migration()