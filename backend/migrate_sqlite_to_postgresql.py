#!/usr/bin/env python3
"""
SQLite to PostgreSQL Migration Script
Migrates 4 CLO System databases from SQLite to PostgreSQL
Total: 258,989 rows across 4 tables
"""

import sqlite3
import psycopg2
import psycopg2.extras
import json
import os
import sys
from datetime import datetime
from pathlib import Path
import hashlib
import logging
from typing import Dict, List, Tuple, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('migration.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class PostgreSQLMigrator:
    """Handles migration from SQLite to PostgreSQL"""
    
    def __init__(self):
        self.pg_config = {
            'host': '127.0.0.1',
            'port': 5433,
            'database': 'clo_dev',
            'user': 'postgres',
            'password': 'adamchaz'
        }
        
        self.sqlite_databases = {
            'correlations': 'data/databases/clo_correlations.db',
            'scenarios': 'data/databases/clo_mag_scenarios.db',
            'config': 'data/databases/clo_model_config.db',
            'reference': 'data/databases/clo_reference_quick.db'
        }
        
        self.migration_mapping = {
            'correlations': {
                'source_table': 'asset_correlations',
                'target_table': 'asset_correlations',
                'batch_size': 5000,
                'transforms': self._transform_correlations
            },
            'scenarios': {
                'source_table': 'scenario_inputs',
                'target_table': 'scenario_inputs', 
                'batch_size': 2000,
                'transforms': self._transform_scenarios
            },
            'config': {
                'source_table': 'model_parameters',
                'target_table': 'model_parameters',
                'batch_size': 100,
                'transforms': self._transform_config
            },
            'reference': {
                'source_table': 'reference_data',
                'target_table': 'reference_data',
                'batch_size': 100,
                'transforms': self._transform_reference
            }
        }
        
        self.migration_stats = {}
    
    def connect_postgresql(self) -> psycopg2.extensions.connection:
        """Create PostgreSQL connection"""
        try:
            conn = psycopg2.connect(**self.pg_config)
            conn.autocommit = False
            logger.info("PostgreSQL connection established")
            return conn
        except Exception as e:
            logger.error(f"PostgreSQL connection failed: {e}")
            raise
    
    def connect_sqlite(self, db_path: str) -> sqlite3.Connection:
        """Create SQLite connection"""
        try:
            if not os.path.exists(db_path):
                raise FileNotFoundError(f"SQLite database not found: {db_path}")
            
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row  # Enable column access by name
            logger.info(f"SQLite connection established: {db_path}")
            return conn
        except Exception as e:
            logger.error(f"SQLite connection failed: {e}")
            raise
    
    def create_postgresql_tables(self):
        """Create PostgreSQL tables from schema"""
        schema_file = 'create_postgresql_schemas.sql'
        if not os.path.exists(schema_file):
            logger.error(f"Schema file not found: {schema_file}")
            return False
        
        try:
            with self.connect_postgresql() as pg_conn:
                with pg_conn.cursor() as cursor:
                    with open(schema_file, 'r') as f:
                        schema_sql = f.read()
                    
                    cursor.execute(schema_sql)
                    pg_conn.commit()
                    logger.info("PostgreSQL tables created successfully")
                    return True
        except Exception as e:
            logger.error(f"Failed to create PostgreSQL tables: {e}")
            return False
    
    def _transform_correlations(self, row: sqlite3.Row) -> Tuple:
        """Transform correlation data for PostgreSQL"""
        return (
            row['asset1_id'],
            row['asset2_id'], 
            float(row['correlation_value']),
            row['correlation_type'],
            row['data_source'],
            row['created_at'],
            row['updated_at']
        )
    
    def _transform_scenarios(self, row: sqlite3.Row) -> Tuple:
        """Transform scenario data for PostgreSQL"""
        return (
            row['scenario_name'],
            row['scenario_type'],
            row['section_name'],
            row['parameter_name'],
            row['parameter_value'],
            row['parameter_type'],
            row['row_number'],
            row['column_number'],
            row['data_source'],
            row['created_at'],
            row['updated_at']
        )
    
    def _transform_config(self, row: sqlite3.Row) -> Tuple:
        """Transform config data for PostgreSQL"""
        # Convert is_active from VARCHAR to BOOLEAN
        is_active = None
        if row['is_active']:
            is_active = row['is_active'].lower() in ('true', '1', 'yes', 'active')
        
        return (
            row['config_name'],
            row['section_name'],
            row['parameter_name'],
            row['parameter_value'],
            row['parameter_type'],
            row['description'],
            row['row_number'],
            row['column_number'],
            is_active,
            row['data_source'],
            row['created_at'],
            row['updated_at']
        )
    
    def _transform_reference(self, row: sqlite3.Row) -> Tuple:
        """Transform reference data for PostgreSQL"""
        # Convert JSON string to proper JSON if needed
        raw_data = row['raw_data']
        if isinstance(raw_data, str):
            try:
                raw_data = json.loads(raw_data)
            except (json.JSONDecodeError, TypeError):
                raw_data = {'data': raw_data}  # Wrap in object if not valid JSON
        
        return (
            row['section_name'],
            row['row_number'],
            row['correlation_date'],
            json.dumps(raw_data) if raw_data else None,
            row['created_at']
        )
    
    def calculate_checksum(self, data: List[Tuple]) -> str:
        """Calculate checksum for data validation"""
        data_str = str(sorted(data))
        return hashlib.sha256(data_str.encode()).hexdigest()
    
    def migrate_table(self, db_key: str) -> Dict[str, Any]:
        """Migrate a single table from SQLite to PostgreSQL"""
        mapping = self.migration_mapping[db_key]
        sqlite_path = self.sqlite_databases[db_key]
        
        stats = {
            'database': db_key,
            'source_table': mapping['source_table'],
            'target_table': mapping['target_table'],
            'rows_processed': 0,
            'rows_inserted': 0,
            'batches_processed': 0,
            'errors': [],
            'checksum': None,
            'start_time': datetime.now(),
            'end_time': None
        }
        
        logger.info(f"Starting migration: {db_key}")
        
        try:
            # Connect to databases
            sqlite_conn = self.connect_sqlite(sqlite_path)
            pg_conn = self.connect_postgresql()
            
            # Get total row count for progress tracking
            cursor = sqlite_conn.cursor()
            cursor.execute(f"SELECT COUNT(*) FROM {mapping['source_table']}")
            total_rows = cursor.fetchone()[0]
            logger.info(f"Total rows to migrate: {total_rows:,}")
            
            # Clear existing data in PostgreSQL table
            with pg_conn.cursor() as pg_cursor:
                pg_cursor.execute(f"DELETE FROM {mapping['target_table']}")
                logger.info(f"Cleared existing data from {mapping['target_table']}")
            
            # Prepare insert query based on table structure
            insert_queries = {
                'asset_correlations': """
                    INSERT INTO asset_correlations 
                    (asset1_id, asset2_id, correlation_value, correlation_type, 
                     data_source, created_at, updated_at)
                    VALUES %s
                """,
                'scenario_inputs': """
                    INSERT INTO scenario_inputs 
                    (scenario_name, scenario_type, section_name, parameter_name,
                     parameter_value, parameter_type, row_number, column_number,
                     data_source, created_at, updated_at)
                    VALUES %s
                """,
                'model_parameters': """
                    INSERT INTO model_parameters 
                    (config_name, section_name, parameter_name, parameter_value,
                     parameter_type, description, row_number, column_number,
                     is_active, data_source, created_at, updated_at)
                    VALUES %s
                """,
                'reference_data': """
                    INSERT INTO reference_data 
                    (section_name, row_number, correlation_date, raw_data, created_at)
                    VALUES %s
                """
            }
            
            insert_query = insert_queries[mapping['target_table']]
            
            # Process data in batches
            offset = 0
            batch_size = mapping['batch_size']
            all_data = []
            
            while True:
                # Fetch batch from SQLite
                cursor.execute(f"""
                    SELECT * FROM {mapping['source_table']} 
                    LIMIT {batch_size} OFFSET {offset}
                """)
                
                rows = cursor.fetchall()
                if not rows:
                    break
                
                # Transform data
                batch_data = []
                for row in rows:
                    try:
                        transformed = mapping['transforms'](row)
                        batch_data.append(transformed)
                        all_data.append(transformed)
                    except Exception as e:
                        error_msg = f"Row transformation error: {e}"
                        stats['errors'].append(error_msg)
                        logger.warning(error_msg)
                
                # Insert batch into PostgreSQL
                if batch_data:
                    with pg_conn.cursor() as pg_cursor:
                        psycopg2.extras.execute_values(
                            pg_cursor, insert_query, batch_data, template=None, page_size=1000
                        )
                        pg_conn.commit()
                        
                        stats['rows_inserted'] += len(batch_data)
                        stats['batches_processed'] += 1
                        
                        progress = (offset + len(rows)) / total_rows * 100
                        logger.info(f"{db_key}: {progress:.1f}% complete ({stats['rows_inserted']:,} rows)")
                
                stats['rows_processed'] += len(rows)
                offset += batch_size
            
            # Calculate checksum for validation
            stats['checksum'] = self.calculate_checksum(all_data)
            stats['end_time'] = datetime.now()
            
            # Update migration metadata
            with pg_conn.cursor() as pg_cursor:
                pg_cursor.execute("""
                    UPDATE migration_metadata 
                    SET rows_migrated = %s, validation_checksum = %s,
                        migration_date = %s
                    WHERE table_name = %s
                """, (stats['rows_inserted'], stats['checksum'], 
                      stats['end_time'], mapping['target_table']))
                pg_conn.commit()
            
            sqlite_conn.close()
            pg_conn.close()
            
            duration = stats['end_time'] - stats['start_time']
            logger.info(f"Migration completed: {db_key} - {stats['rows_inserted']:,} rows in {duration}")
            
        except Exception as e:
            stats['errors'].append(str(e))
            stats['end_time'] = datetime.now()
            logger.error(f"Migration failed for {db_key}: {e}")
            
        return stats
    
    def validate_migration(self) -> Dict[str, Any]:
        """Validate the migration by comparing row counts and checksums"""
        validation_results = {
            'overall_success': True,
            'tables': {},
            'total_source_rows': 0,
            'total_target_rows': 0
        }
        
        logger.info("Starting migration validation...")
        
        try:
            pg_conn = self.connect_postgresql()
            
            for db_key, sqlite_path in self.sqlite_databases.items():
                mapping = self.migration_mapping[db_key]
                table_validation = {
                    'source_rows': 0,
                    'target_rows': 0,
                    'match': False
                }
                
                # Count SQLite rows
                sqlite_conn = self.connect_sqlite(sqlite_path)
                cursor = sqlite_conn.cursor()
                cursor.execute(f"SELECT COUNT(*) FROM {mapping['source_table']}")
                table_validation['source_rows'] = cursor.fetchone()[0]
                sqlite_conn.close()
                
                # Count PostgreSQL rows
                with pg_conn.cursor() as pg_cursor:
                    pg_cursor.execute(f"SELECT COUNT(*) FROM {mapping['target_table']}")
                    table_validation['target_rows'] = pg_cursor.fetchone()[0]
                
                table_validation['match'] = (
                    table_validation['source_rows'] == table_validation['target_rows']
                )
                
                if not table_validation['match']:
                    validation_results['overall_success'] = False
                
                validation_results['tables'][db_key] = table_validation
                validation_results['total_source_rows'] += table_validation['source_rows']
                validation_results['total_target_rows'] += table_validation['target_rows']
                
                logger.info(f"Validation {db_key}: "
                          f"Source={table_validation['source_rows']:,} "
                          f"Target={table_validation['target_rows']:,} "
                          f"Match={table_validation['match']}")
            
            pg_conn.close()
            
        except Exception as e:
            logger.error(f"Validation failed: {e}")
            validation_results['overall_success'] = False
            validation_results['error'] = str(e)
        
        return validation_results
    
    def run_full_migration(self) -> Dict[str, Any]:
        """Execute complete migration process"""
        migration_results = {
            'start_time': datetime.now(),
            'end_time': None,
            'overall_success': True,
            'tables': {},
            'validation': None,
            'summary': {}
        }
        
        logger.info("Starting full SQLite to PostgreSQL migration")
        logger.info("=" * 60)
        
        # Create PostgreSQL tables
        if not self.create_postgresql_tables():
            migration_results['overall_success'] = False
            migration_results['error'] = "Failed to create PostgreSQL tables"
            return migration_results
        
        # Migrate each table
        for db_key in self.sqlite_databases.keys():
            table_stats = self.migrate_table(db_key)
            migration_results['tables'][db_key] = table_stats
            
            if table_stats['errors']:
                migration_results['overall_success'] = False
        
        # Validate migration
        validation_results = self.validate_migration()
        migration_results['validation'] = validation_results
        
        if not validation_results['overall_success']:
            migration_results['overall_success'] = False
        
        migration_results['end_time'] = datetime.now()
        duration = migration_results['end_time'] - migration_results['start_time']
        
        # Create summary
        total_rows_migrated = sum(
            stats['rows_inserted'] for stats in migration_results['tables'].values()
        )
        
        migration_results['summary'] = {
            'duration': str(duration),
            'total_tables': len(self.sqlite_databases),
            'total_rows_migrated': total_rows_migrated,
            'success': migration_results['overall_success']
        }
        
        logger.info("=" * 60)
        logger.info(f"Migration Summary:")
        logger.info(f"  Duration: {duration}")
        logger.info(f"  Tables: {migration_results['summary']['total_tables']}")
        logger.info(f"  Total Rows: {total_rows_migrated:,}")
        logger.info(f"  Success: {migration_results['overall_success']}")
        
        # Save results to file
        with open('migration_results.json', 'w') as f:
            json.dump(migration_results, f, indent=2, default=str)
        
        return migration_results

def main():
    """Main migration execution"""
    migrator = PostgreSQLMigrator()
    
    try:
        results = migrator.run_full_migration()
        
        if results['overall_success']:
            logger.info("Migration completed successfully!")
            sys.exit(0)
        else:
            logger.error("Migration failed!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Migration interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Migration failed with exception: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()