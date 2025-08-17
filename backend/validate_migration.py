#!/usr/bin/env python3
"""
Migration Validation Framework
Comprehensive validation for SQLite to PostgreSQL migration
Validates data integrity, performance, and application compatibility
"""

import sqlite3
import psycopg2
import psycopg2.extras
import json
import os
import sys
from datetime import datetime
import logging
import hashlib
from typing import Dict, List, Tuple, Any, Optional
from decimal import Decimal
import statistics

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('validation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MigrationValidator:
    """Comprehensive migration validation framework"""
    
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
        
        self.table_mapping = {
            'correlations': {
                'sqlite_table': 'asset_correlations',
                'postgres_table': 'asset_correlations',
                'key_columns': ['asset1_id', 'asset2_id'],
                'numeric_columns': ['correlation_value'],
                'critical_columns': ['asset1_id', 'asset2_id', 'correlation_value']
            },
            'scenarios': {
                'sqlite_table': 'scenario_inputs',
                'postgres_table': 'scenario_inputs',
                'key_columns': ['scenario_name', 'parameter_name'],
                'numeric_columns': ['row_number', 'column_number'],
                'critical_columns': ['scenario_name', 'parameter_name', 'parameter_value']
            },
            'config': {
                'sqlite_table': 'model_parameters',
                'postgres_table': 'model_parameters',
                'key_columns': ['config_name', 'parameter_name'],
                'numeric_columns': ['row_number', 'column_number'],
                'critical_columns': ['config_name', 'parameter_name', 'parameter_value']
            },
            'reference': {
                'sqlite_table': 'reference_data',
                'postgres_table': 'reference_data',
                'key_columns': ['section_name', 'row_number'],
                'numeric_columns': ['row_number'],
                'critical_columns': ['section_name', 'raw_data']
            }
        }
        
        self.validation_results = {}
    
    def connect_postgresql(self) -> psycopg2.extensions.connection:
        """Create PostgreSQL connection"""
        try:
            conn = psycopg2.connect(**self.pg_config)
            logger.debug("PostgreSQL connection established")
            return conn
        except Exception as e:
            logger.error(f"PostgreSQL connection failed: {e}")
            raise
    
    def connect_sqlite(self, db_path: str) -> sqlite3.Connection:
        """Create SQLite connection"""
        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            logger.debug(f"SQLite connection established: {db_path}")
            return conn
        except Exception as e:
            logger.error(f"SQLite connection failed: {e}")
            raise
    
    def validate_row_counts(self) -> Dict[str, Any]:
        """Validate that row counts match between SQLite and PostgreSQL"""
        logger.info("Validating row counts...")
        
        results = {
            'overall_success': True,
            'tables': {},
            'total_sqlite_rows': 0,
            'total_postgres_rows': 0
        }
        
        try:
            pg_conn = self.connect_postgresql()
            
            for db_key, sqlite_path in self.sqlite_databases.items():
                mapping = self.table_mapping[db_key]
                table_result = {'success': True, 'details': {}}
                
                # Get SQLite count
                sqlite_conn = self.connect_sqlite(sqlite_path)
                cursor = sqlite_conn.cursor()
                cursor.execute(f"SELECT COUNT(*) FROM {mapping['sqlite_table']}")
                sqlite_count = cursor.fetchone()[0]
                sqlite_conn.close()
                
                # Get PostgreSQL count
                with pg_conn.cursor() as pg_cursor:
                    pg_cursor.execute(f"SELECT COUNT(*) FROM {mapping['postgres_table']}")
                    postgres_count = pg_cursor.fetchone()[0]
                
                table_result['details'] = {
                    'sqlite_rows': sqlite_count,
                    'postgres_rows': postgres_count,
                    'match': sqlite_count == postgres_count,
                    'difference': postgres_count - sqlite_count
                }
                
                if not table_result['details']['match']:
                    table_result['success'] = False
                    results['overall_success'] = False
                    logger.warning(f"Row count mismatch in {db_key}: "
                                 f"SQLite={sqlite_count}, PostgreSQL={postgres_count}")
                else:
                    logger.info(f"Row count validation passed for {db_key}: {sqlite_count:,} rows")
                
                results['tables'][db_key] = table_result
                results['total_sqlite_rows'] += sqlite_count
                results['total_postgres_rows'] += postgres_count
            
            pg_conn.close()
            
        except Exception as e:
            logger.error(f"Row count validation failed: {e}")
            results['overall_success'] = False
            results['error'] = str(e)
        
        return results
    
    def validate_data_integrity(self, db_key: str, sample_size: int = 100) -> Dict[str, Any]:
        """Validate data integrity by comparing samples"""
        logger.info(f"Validating data integrity for {db_key} (sample size: {sample_size})...")
        
        mapping = self.table_mapping[db_key]
        sqlite_path = self.sqlite_databases[db_key]
        
        results = {
            'success': True,
            'samples_compared': 0,
            'mismatches': [],
            'critical_column_errors': 0,
            'numeric_precision_errors': 0
        }
        
        try:
            # Connect to both databases
            sqlite_conn = self.connect_sqlite(sqlite_path)
            pg_conn = self.connect_postgresql()
            
            # Get sample records from SQLite
            sqlite_cursor = sqlite_conn.cursor()
            sqlite_cursor.execute(f"""
                SELECT * FROM {mapping['sqlite_table']} 
                ORDER BY id 
                LIMIT {sample_size}
            """)
            sqlite_rows = sqlite_cursor.fetchall()
            
            # Get corresponding records from PostgreSQL
            with pg_conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as pg_cursor:
                pg_cursor.execute(f"""
                    SELECT * FROM {mapping['postgres_table']} 
                    ORDER BY id 
                    LIMIT {sample_size}
                """)
                postgres_rows = pg_cursor.fetchall()
            
            # Compare records
            for i, (sqlite_row, postgres_row) in enumerate(zip(sqlite_rows, postgres_rows)):
                row_mismatches = []
                
                # Compare each column
                for column in sqlite_row.keys():
                    if column == 'id':  # Skip auto-generated IDs
                        continue
                    
                    sqlite_val = sqlite_row[column]
                    postgres_val = postgres_row.get(column)
                    
                    # Handle None values
                    if sqlite_val is None and postgres_val is None:
                        continue
                    
                    # Special handling for different data types
                    if column in mapping.get('numeric_columns', []):
                        # Numeric comparison with tolerance
                        if sqlite_val is not None and postgres_val is not None:
                            try:
                                if abs(float(sqlite_val) - float(postgres_val)) > 0.00001:
                                    row_mismatches.append({
                                        'column': column,
                                        'sqlite_value': sqlite_val,
                                        'postgres_value': postgres_val,
                                        'type': 'numeric_precision'
                                    })
                                    results['numeric_precision_errors'] += 1
                            except (ValueError, TypeError):
                                row_mismatches.append({
                                    'column': column,
                                    'sqlite_value': sqlite_val,
                                    'postgres_value': postgres_val,
                                    'type': 'type_conversion'
                                })
                    elif column == 'raw_data':
                        # JSON comparison
                        try:
                            sqlite_json = json.loads(sqlite_val) if sqlite_val else None
                            postgres_json = json.loads(postgres_val) if postgres_val else None
                            if sqlite_json != postgres_json:
                                row_mismatches.append({
                                    'column': column,
                                    'sqlite_value': sqlite_val,
                                    'postgres_value': postgres_val,
                                    'type': 'json_data'
                                })
                        except (json.JSONDecodeError, TypeError):
                            if str(sqlite_val) != str(postgres_val):
                                row_mismatches.append({
                                    'column': column,
                                    'sqlite_value': sqlite_val,
                                    'postgres_value': postgres_val,
                                    'type': 'string_comparison'
                                })
                    else:
                        # String comparison
                        if str(sqlite_val) != str(postgres_val):
                            row_mismatches.append({
                                'column': column,
                                'sqlite_value': sqlite_val,
                                'postgres_value': postgres_val,
                                'type': 'string_mismatch'
                            })
                
                if row_mismatches:
                    results['mismatches'].append({
                        'row_index': i,
                        'mismatches': row_mismatches
                    })
                    
                    # Check if critical columns are affected
                    critical_affected = any(
                        mm['column'] in mapping['critical_columns'] 
                        for mm in row_mismatches
                    )
                    if critical_affected:
                        results['critical_column_errors'] += 1
                
                results['samples_compared'] += 1
            
            # Determine overall success
            if results['critical_column_errors'] > 0:
                results['success'] = False
                logger.error(f"Critical data integrity errors found in {db_key}: "
                           f"{results['critical_column_errors']} critical column errors")
            elif results['numeric_precision_errors'] > 5:  # Allow some tolerance
                results['success'] = False
                logger.warning(f"Too many numeric precision errors in {db_key}: "
                             f"{results['numeric_precision_errors']} errors")
            else:
                logger.info(f"Data integrity validation passed for {db_key}")
            
            sqlite_conn.close()
            pg_conn.close()
            
        except Exception as e:
            logger.error(f"Data integrity validation failed for {db_key}: {e}")
            results['success'] = False
            results['error'] = str(e)
        
        return results
    
    def validate_constraints_and_indexes(self) -> Dict[str, Any]:
        """Validate that PostgreSQL constraints and indexes are properly created"""
        logger.info("Validating PostgreSQL constraints and indexes...")
        
        results = {
            'success': True,
            'indexes': {},
            'constraints': {},
            'errors': []
        }
        
        expected_indexes = {
            'asset_correlations': [
                'idx_correlations_asset1_id',
                'idx_correlations_asset2_id', 
                'idx_correlations_assets_pair'
            ],
            'scenario_inputs': [
                'idx_scenarios_name',
                'idx_scenarios_type',
                'idx_scenarios_parameter'
            ],
            'model_parameters': [
                'idx_config_name',
                'idx_config_parameter'
            ],
            'reference_data': [
                'idx_reference_section',
                'idx_reference_jsonb'
            ]
        }
        
        try:
            pg_conn = self.connect_postgresql()
            
            with pg_conn.cursor() as cursor:
                # Check indexes
                for table, expected_idx in expected_indexes.items():
                    table_indexes = []
                    
                    cursor.execute("""
                        SELECT indexname FROM pg_indexes 
                        WHERE tablename = %s AND schemaname = 'public'
                    """, (table,))
                    
                    existing_indexes = [row[0] for row in cursor.fetchall()]
                    
                    for idx_name in expected_idx:
                        if idx_name in existing_indexes:
                            table_indexes.append({'name': idx_name, 'exists': True})
                        else:
                            table_indexes.append({'name': idx_name, 'exists': False})
                            results['errors'].append(f"Missing index: {idx_name} on {table}")
                            results['success'] = False
                    
                    results['indexes'][table] = table_indexes
                
                # Check constraints
                cursor.execute("""
                    SELECT conname, contype FROM pg_constraint c
                    JOIN pg_class t ON c.conrelid = t.oid
                    JOIN pg_namespace n ON t.relnamespace = n.oid
                    WHERE n.nspname = 'public'
                    AND t.relname IN ('asset_correlations', 'scenario_inputs', 
                                      'model_parameters', 'reference_data')
                """)
                
                constraints = cursor.fetchall()
                for constraint_name, constraint_type in constraints:
                    constraint_types = {
                        'p': 'PRIMARY KEY',
                        'u': 'UNIQUE',
                        'f': 'FOREIGN KEY',
                        'c': 'CHECK'
                    }
                    results['constraints'][constraint_name] = constraint_types.get(constraint_type, constraint_type)
            
            pg_conn.close()
            
            if results['success']:
                logger.info("Constraints and indexes validation passed")
            else:
                logger.error(f"Constraints and indexes validation failed: {len(results['errors'])} issues")
            
        except Exception as e:
            logger.error(f"Constraints and indexes validation failed: {e}")
            results['success'] = False
            results['error'] = str(e)
        
        return results
    
    def performance_benchmark(self) -> Dict[str, Any]:
        """Run performance benchmarks on migrated data"""
        logger.info("Running performance benchmarks...")
        
        results = {
            'success': True,
            'benchmarks': {},
            'overall_performance': 'good'
        }
        
        benchmark_queries = {
            'correlations_lookup': {
                'query': """SELECT correlation_value FROM asset_correlations 
                           WHERE asset1_id = 'ASSET001' AND asset2_id = 'ASSET002'""",
                'expected_max_time': 0.1  # 100ms
            },
            'scenario_search': {
                'query': """SELECT * FROM scenario_inputs 
                           WHERE scenario_name = 'MAG17' AND parameter_name LIKE 'Base%'""",
                'expected_max_time': 0.2  # 200ms
            },
            'config_lookup': {
                'query': """SELECT parameter_value FROM model_parameters 
                           WHERE config_name = 'Default' AND is_active = true""",
                'expected_max_time': 0.1  # 100ms
            },
            'reference_json_query': {
                'query': """SELECT * FROM reference_data 
                           WHERE raw_data->>'key' IS NOT NULL LIMIT 10""",
                'expected_max_time': 0.3  # 300ms
            }
        }
        
        try:
            pg_conn = self.connect_postgresql()
            
            for benchmark_name, config in benchmark_queries.items():
                times = []
                
                # Run each query 5 times
                for _ in range(5):
                    start_time = datetime.now()
                    
                    with pg_conn.cursor() as cursor:
                        cursor.execute(config['query'])
                        cursor.fetchall()  # Fetch all results
                    
                    end_time = datetime.now()
                    execution_time = (end_time - start_time).total_seconds()
                    times.append(execution_time)
                
                avg_time = statistics.mean(times)
                max_time = max(times)
                min_time = min(times)
                
                benchmark_result = {
                    'average_time': avg_time,
                    'max_time': max_time,
                    'min_time': min_time,
                    'expected_max_time': config['expected_max_time'],
                    'passes_benchmark': max_time <= config['expected_max_time'],
                    'times': times
                }
                
                results['benchmarks'][benchmark_name] = benchmark_result
                
                if not benchmark_result['passes_benchmark']:
                    results['success'] = False
                    logger.warning(f"Performance benchmark failed for {benchmark_name}: "
                                 f"{max_time:.3f}s > {config['expected_max_time']}s")
                else:
                    logger.info(f"Performance benchmark passed for {benchmark_name}: "
                              f"avg={avg_time:.3f}s max={max_time:.3f}s")
            
            pg_conn.close()
            
            # Overall performance assessment
            failed_benchmarks = sum(
                1 for b in results['benchmarks'].values() 
                if not b['passes_benchmark']
            )
            
            if failed_benchmarks == 0:
                results['overall_performance'] = 'excellent'
            elif failed_benchmarks <= 1:
                results['overall_performance'] = 'good'
            elif failed_benchmarks <= 2:
                results['overall_performance'] = 'acceptable'
            else:
                results['overall_performance'] = 'poor'
            
        except Exception as e:
            logger.error(f"Performance benchmark failed: {e}")
            results['success'] = False
            results['error'] = str(e)
        
        return results
    
    def run_comprehensive_validation(self) -> Dict[str, Any]:
        """Run all validation tests"""
        validation_start = datetime.now()
        
        logger.info("Starting comprehensive migration validation")
        logger.info("=" * 60)
        
        overall_results = {
            'start_time': validation_start,
            'end_time': None,
            'overall_success': True,
            'validations': {},
            'summary': {}
        }
        
        # 1. Row count validation
        row_count_results = self.validate_row_counts()
        overall_results['validations']['row_counts'] = row_count_results
        if not row_count_results['overall_success']:
            overall_results['overall_success'] = False
        
        # 2. Data integrity validation (for each table)
        data_integrity_results = {}
        for db_key in self.sqlite_databases.keys():
            integrity_result = self.validate_data_integrity(db_key, sample_size=100)
            data_integrity_results[db_key] = integrity_result
            if not integrity_result['success']:
                overall_results['overall_success'] = False
        
        overall_results['validations']['data_integrity'] = data_integrity_results
        
        # 3. Constraints and indexes validation
        constraints_results = self.validate_constraints_and_indexes()
        overall_results['validations']['constraints_indexes'] = constraints_results
        if not constraints_results['success']:
            overall_results['overall_success'] = False
        
        # 4. Performance benchmarks
        performance_results = self.performance_benchmark()
        overall_results['validations']['performance'] = performance_results
        if not performance_results['success']:
            # Performance issues don't fail the migration, just warn
            logger.warning("Performance benchmarks below expectations")
        
        overall_results['end_time'] = datetime.now()
        validation_duration = overall_results['end_time'] - validation_start
        
        # Create summary
        total_sqlite_rows = row_count_results.get('total_sqlite_rows', 0)
        total_postgres_rows = row_count_results.get('total_postgres_rows', 0)
        
        overall_results['summary'] = {
            'validation_duration': str(validation_duration),
            'total_sqlite_rows': total_sqlite_rows,
            'total_postgres_rows': total_postgres_rows,
            'row_count_match': total_sqlite_rows == total_postgres_rows,
            'data_integrity_passed': all(
                r['success'] for r in data_integrity_results.values()
            ),
            'constraints_indexes_passed': constraints_results['success'],
            'performance_rating': performance_results.get('overall_performance', 'unknown'),
            'overall_success': overall_results['overall_success']
        }
        
        logger.info("=" * 60)
        logger.info("Validation Summary:")
        logger.info(f"  Duration: {validation_duration}")
        logger.info(f"  Row Count Match: {overall_results['summary']['row_count_match']}")
        logger.info(f"  Data Integrity: {overall_results['summary']['data_integrity_passed']}")
        logger.info(f"  Constraints/Indexes: {overall_results['summary']['constraints_indexes_passed']}")
        logger.info(f"  Performance: {overall_results['summary']['performance_rating']}")
        logger.info(f"  Overall Success: {overall_results['overall_success']}")
        
        # Save results to file
        with open('validation_results.json', 'w') as f:
            json.dump(overall_results, f, indent=2, default=str)
        
        return overall_results

def main():
    """Main validation execution"""
    validator = MigrationValidator()
    
    try:
        results = validator.run_comprehensive_validation()
        
        if results['overall_success']:
            logger.info("All validation tests passed!")
            sys.exit(0)
        else:
            logger.error("Some validation tests failed!")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Validation failed with exception: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()