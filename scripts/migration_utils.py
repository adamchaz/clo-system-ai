#!/usr/bin/env python3
"""
CLO Data Migration Utilities
Common utilities and helper functions for data migration operations

This module provides:
- Database backup and restore utilities
- Data quality scanning and reporting
- Migration rollback capabilities
- Performance monitoring tools
- Batch processing utilities
"""

import json
import logging
import shutil
import subprocess
import os
from pathlib import Path
from datetime import datetime, date
from decimal import Decimal
from typing import Dict, List, Any, Optional, Union
import hashlib
import tempfile

# Database imports
from sqlalchemy import create_engine, text, MetaData, Table
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError

# Configure logging
logger = logging.getLogger(__name__)

class BackupManager:
    """Manage database backups for migration safety"""
    
    def __init__(self, database_url: str, backup_dir: Path = None):
        self.database_url = database_url
        self.backup_dir = backup_dir or Path("migration_backups")
        self.backup_dir.mkdir(exist_ok=True)
        
    def create_backup(self, backup_name: str = None) -> Path:
        """Create full database backup"""
        if not backup_name:
            backup_name = f"pre_migration_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        backup_file = self.backup_dir / f"{backup_name}.sql"
        
        try:
            logger.info(f"Creating database backup: {backup_file}")
            
            # Extract connection details from URL
            # postgresql://user:pass@host:port/dbname
            url_parts = self.database_url.replace('postgresql://', '').split('/')
            connection_part = url_parts[0]
            db_name = url_parts[1] if len(url_parts) > 1 else 'clo_db'
            
            user_pass, host_port = connection_part.split('@')
            user, password = user_pass.split(':')
            host = host_port.split(':')[0]
            port = host_port.split(':')[1] if ':' in host_port else '5432'
            
            # Use pg_dump to create backup
            env = os.environ.copy()
            env['PGPASSWORD'] = password
            
            cmd = [
                'pg_dump',
                '-h', host,
                '-p', port,
                '-U', user,
                '-d', db_name,
                '--no-password',
                '--verbose',
                '--format=custom',
                '--file', str(backup_file)
            ]
            
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"Backup created successfully: {backup_file}")
                return backup_file
            else:
                logger.error(f"Backup failed: {result.stderr}")
                raise Exception(f"pg_dump failed: {result.stderr}")
                
        except Exception as e:
            logger.error(f"Error creating backup: {e}")
            raise
    
    def restore_backup(self, backup_file: Path) -> bool:
        """Restore database from backup"""
        try:
            logger.info(f"Restoring database from backup: {backup_file}")
            
            if not backup_file.exists():
                raise FileNotFoundError(f"Backup file not found: {backup_file}")
            
            # Extract connection details
            url_parts = self.database_url.replace('postgresql://', '').split('/')
            connection_part = url_parts[0]
            db_name = url_parts[1] if len(url_parts) > 1 else 'clo_db'
            
            user_pass, host_port = connection_part.split('@')
            user, password = user_pass.split(':')
            host = host_port.split(':')[0]
            port = host_port.split(':')[1] if ':' in host_port else '5432'
            
            # Use pg_restore
            env = os.environ.copy()
            env['PGPASSWORD'] = password
            
            cmd = [
                'pg_restore',
                '-h', host,
                '-p', port,
                '-U', user,
                '-d', db_name,
                '--no-password',
                '--verbose',
                '--clean',
                '--if-exists',
                str(backup_file)
            ]
            
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("Database restored successfully")
                return True
            else:
                logger.error(f"Restore failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error restoring backup: {e}")
            return False
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """List available backups"""
        backups = []
        
        for backup_file in self.backup_dir.glob("*.sql"):
            try:
                stat = backup_file.stat()
                backups.append({
                    'name': backup_file.stem,
                    'file_path': backup_file,
                    'size_mb': round(stat.st_size / (1024 * 1024), 2),
                    'created_at': datetime.fromtimestamp(stat.st_ctime),
                    'modified_at': datetime.fromtimestamp(stat.st_mtime)
                })
            except Exception as e:
                logger.warning(f"Error reading backup info for {backup_file}: {e}")
        
        return sorted(backups, key=lambda x: x['created_at'], reverse=True)

class DataQualityScanner:
    """Scan and report on data quality issues"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        
    def scan_database_quality(self) -> Dict[str, Any]:
        """Comprehensive data quality scan"""
        logger.info("Running comprehensive data quality scan...")
        
        quality_report = {
            'scan_timestamp': datetime.now(),
            'table_summaries': {},
            'data_quality_issues': [],
            'recommendations': [],
            'overall_score': 0
        }
        
        try:
            # Get all tables
            metadata = MetaData()
            metadata.reflect(bind=self.db.bind)
            
            total_quality_score = 0
            table_count = 0
            
            for table_name, table in metadata.tables.items():
                logger.info(f"Scanning table: {table_name}")
                
                table_summary = self._scan_table_quality(table_name, table)
                quality_report['table_summaries'][table_name] = table_summary
                
                total_quality_score += table_summary.get('quality_score', 0)
                table_count += 1
                
                # Collect issues
                for issue in table_summary.get('issues', []):
                    quality_report['data_quality_issues'].append({
                        'table': table_name,
                        'issue': issue
                    })
            
            # Calculate overall quality score
            if table_count > 0:
                quality_report['overall_score'] = round(total_quality_score / table_count, 2)
            
            # Generate recommendations
            quality_report['recommendations'] = self._generate_quality_recommendations(quality_report)
            
            logger.info(f"Data quality scan complete. Overall score: {quality_report['overall_score']}/100")
            return quality_report
            
        except Exception as e:
            logger.error(f"Error during data quality scan: {e}")
            quality_report['data_quality_issues'].append(f"Scan error: {e}")
            return quality_report
    
    def _scan_table_quality(self, table_name: str, table: Table) -> Dict[str, Any]:
        """Scan individual table for quality issues"""
        summary = {
            'record_count': 0,
            'column_count': len(table.columns),
            'null_percentages': {},
            'duplicate_count': 0,
            'quality_score': 100,
            'issues': []
        }
        
        try:
            # Get record count
            count_query = f"SELECT COUNT(*) FROM {table_name}"
            result = self.db.execute(text(count_query))
            summary['record_count'] = result.scalar()
            
            if summary['record_count'] == 0:
                summary['issues'].append("Table is empty")
                summary['quality_score'] -= 50
                return summary
            
            # Check null percentages for each column
            for column in table.columns:
                null_query = f"SELECT COUNT(*) FROM {table_name} WHERE {column.name} IS NULL"
                null_result = self.db.execute(text(null_query))
                null_count = null_result.scalar()
                
                null_percentage = (null_count / summary['record_count']) * 100
                summary['null_percentages'][column.name] = round(null_percentage, 2)
                
                # Flag high null percentages for important columns
                if null_percentage > 50:
                    summary['issues'].append(f"High null percentage in {column.name}: {null_percentage:.1f}%")
                    summary['quality_score'] -= 10
            
            # Check for duplicates on primary key if exists
            primary_key_columns = [col.name for col in table.columns if col.primary_key]
            if primary_key_columns:
                pk_columns = ', '.join(primary_key_columns)
                dup_query = f"""
                    SELECT COUNT(*) FROM (
                        SELECT {pk_columns}, COUNT(*) 
                        FROM {table_name} 
                        GROUP BY {pk_columns} 
                        HAVING COUNT(*) > 1
                    ) duplicates
                """
                dup_result = self.db.execute(text(dup_query))
                summary['duplicate_count'] = dup_result.scalar()
                
                if summary['duplicate_count'] > 0:
                    summary['issues'].append(f"Found {summary['duplicate_count']} duplicate records")
                    summary['quality_score'] -= 20
            
        except Exception as e:
            logger.error(f"Error scanning table {table_name}: {e}")
            summary['issues'].append(f"Scan error: {e}")
            summary['quality_score'] = 0
        
        return summary
    
    def _generate_quality_recommendations(self, quality_report: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on quality scan results"""
        recommendations = []
        
        overall_score = quality_report.get('overall_score', 0)
        
        if overall_score < 70:
            recommendations.append("Overall data quality is below acceptable threshold. Review all issues before production deployment.")
        
        # Count issues by type
        empty_tables = sum(1 for summary in quality_report['table_summaries'].values() if summary['record_count'] == 0)
        if empty_tables > 0:
            recommendations.append(f"Found {empty_tables} empty tables. Verify these are expected to be empty.")
        
        # High null percentages
        high_null_issues = [issue for issue in quality_report['data_quality_issues'] if 'High null percentage' in issue.get('issue', '')]
        if high_null_issues:
            recommendations.append("Address high null percentages in critical columns.")
        
        # Duplicate records
        duplicate_issues = [issue for issue in quality_report['data_quality_issues'] if 'duplicate' in issue.get('issue', '').lower()]
        if duplicate_issues:
            recommendations.append("Resolve duplicate records before production deployment.")
        
        return recommendations

class MigrationRollback:
    """Handle migration rollback operations"""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.backup_manager = BackupManager(database_url)
        
        engine = create_engine(database_url)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        self.db_session = SessionLocal()
        
    def create_rollback_point(self, rollback_name: str) -> Dict[str, Any]:
        """Create a rollback point before migration"""
        logger.info(f"Creating rollback point: {rollback_name}")
        
        rollback_info = {
            'rollback_name': rollback_name,
            'created_at': datetime.now(),
            'backup_file': None,
            'table_checksums': {},
            'record_counts': {}
        }
        
        try:
            # Create backup
            backup_file = self.backup_manager.create_backup(f"rollback_{rollback_name}")
            rollback_info['backup_file'] = str(backup_file)
            
            # Calculate table checksums and record counts
            metadata = MetaData()
            metadata.reflect(bind=self.db_session.bind)
            
            for table_name in metadata.tables.keys():
                # Get record count
                count_result = self.db_session.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                rollback_info['record_counts'][table_name] = count_result.scalar()
                
                # Calculate simple checksum (sum of primary key values if numeric)
                try:
                    checksum_result = self.db_session.execute(text(f"SELECT COUNT(*), COALESCE(SUM(CAST(REGEXP_REPLACE(COALESCE(CAST(id AS TEXT), '0'), '[^0-9]', '', 'g') AS BIGINT)), 0) FROM {table_name}"))
                    count, sum_val = checksum_result.fetchone()
                    rollback_info['table_checksums'][table_name] = f"{count}:{sum_val}"
                except:
                    # Fallback to just record count
                    rollback_info['table_checksums'][table_name] = str(rollback_info['record_counts'][table_name])
            
            # Save rollback info
            rollback_file = Path(f"rollback_points/rollback_{rollback_name}.json")
            rollback_file.parent.mkdir(exist_ok=True)
            
            with open(rollback_file, 'w') as f:
                json.dump(rollback_info, f, indent=2, default=str)
            
            logger.info(f"Rollback point created: {rollback_file}")
            return rollback_info
            
        except Exception as e:
            logger.error(f"Error creating rollback point: {e}")
            raise
        finally:
            self.db_session.close()
    
    def execute_rollback(self, rollback_name: str) -> bool:
        """Execute rollback to specified point"""
        logger.info(f"Executing rollback to: {rollback_name}")
        
        try:
            # Load rollback info
            rollback_file = Path(f"rollback_points/rollback_{rollback_name}.json")
            if not rollback_file.exists():
                raise FileNotFoundError(f"Rollback point not found: {rollback_name}")
            
            with open(rollback_file, 'r') as f:
                rollback_info = json.load(f)
            
            backup_file = Path(rollback_info['backup_file'])
            if not backup_file.exists():
                raise FileNotFoundError(f"Backup file not found: {backup_file}")
            
            # Restore from backup
            success = self.backup_manager.restore_backup(backup_file)
            
            if success:
                logger.info(f"Successfully rolled back to: {rollback_name}")
                return True
            else:
                logger.error(f"Failed to rollback to: {rollback_name}")
                return False
                
        except Exception as e:
            logger.error(f"Error executing rollback: {e}")
            return False

class PerformanceMonitor:
    """Monitor database performance during migration"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.metrics = {}
        
    def benchmark_query_performance(self) -> Dict[str, Any]:
        """Benchmark key query performance"""
        logger.info("Benchmarking database query performance...")
        
        benchmarks = {
            'timestamp': datetime.now(),
            'query_times': {},
            'recommendations': []
        }
        
        import time
        
        # Test queries
        test_queries = {
            'asset_count': "SELECT COUNT(*) FROM assets",
            'asset_sum_par': "SELECT SUM(par_amount) FROM assets WHERE par_amount IS NOT NULL",
            'asset_filter_rating': "SELECT COUNT(*) FROM assets WHERE sp_rating IN ('BBB+', 'BBB', 'BBB-')",
            'asset_join_deal': "SELECT COUNT(*) FROM assets a JOIN deal_assets da ON a.blkrock_id = da.blkrock_id",
            'complex_aggregation': """
                SELECT sp_rating, COUNT(*), AVG(par_amount), SUM(par_amount) 
                FROM assets 
                WHERE par_amount > 1000000 
                GROUP BY sp_rating 
                ORDER BY sp_rating
            """
        }
        
        for query_name, query in test_queries.items():
            try:
                start_time = time.time()
                result = self.db.execute(text(query))
                _ = result.fetchall()  # Fetch all results
                end_time = time.time()
                
                query_time = round(end_time - start_time, 4)
                benchmarks['query_times'][query_name] = query_time
                
                logger.info(f"{query_name}: {query_time}s")
                
                # Generate recommendations
                if query_time > 2:
                    benchmarks['recommendations'].append(f"Slow query detected: {query_name} ({query_time}s) - consider indexing")
                    
            except Exception as e:
                logger.error(f"Error benchmarking {query_name}: {e}")
                benchmarks['query_times'][query_name] = -1
        
        return benchmarks

class BatchProcessor:
    """Utility for batch processing operations"""
    
    def __init__(self, batch_size: int = 1000):
        self.batch_size = batch_size
        
    def process_in_batches(self, items: List[Any], processor_func, *args, **kwargs) -> Dict[str, Any]:
        """Process items in batches"""
        logger.info(f"Processing {len(items)} items in batches of {self.batch_size}")
        
        results = {
            'total_items': len(items),
            'processed_items': 0,
            'failed_items': 0,
            'batch_count': 0,
            'errors': []
        }
        
        for i in range(0, len(items), self.batch_size):
            batch = items[i:i + self.batch_size]
            batch_num = (i // self.batch_size) + 1
            
            try:
                logger.info(f"Processing batch {batch_num}: {len(batch)} items")
                
                batch_result = processor_func(batch, *args, **kwargs)
                
                if isinstance(batch_result, dict) and 'processed' in batch_result:
                    results['processed_items'] += batch_result['processed']
                    results['failed_items'] += batch_result.get('failed', 0)
                else:
                    results['processed_items'] += len(batch)
                
                results['batch_count'] += 1
                
            except Exception as e:
                logger.error(f"Error processing batch {batch_num}: {e}")
                results['failed_items'] += len(batch)
                results['errors'].append(f"Batch {batch_num}: {e}")
        
        logger.info(f"Batch processing complete: {results['processed_items']}/{results['total_items']} processed")
        return results

def calculate_file_hash(file_path: Path) -> str:
    """Calculate MD5 hash of file for integrity checking"""
    hash_md5 = hashlib.md5()
    
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    
    return hash_md5.hexdigest()

def validate_migration_prerequisites(config: Dict[str, Any]) -> List[str]:
    """Validate prerequisites for migration"""
    issues = []
    
    # Check Excel file exists
    excel_path = Path(config.get('excel_path', ''))
    if not excel_path.exists():
        issues.append(f"Excel file not found: {excel_path}")
    
    # Check database connection
    try:
        engine = create_engine(config.get('database_url'))
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as e:
        issues.append(f"Cannot connect to database: {e}")
    
    # Check disk space
    backup_dir = Path(config.get('backup_dir', 'migration_backups'))
    try:
        stat = shutil.disk_usage(backup_dir.parent if backup_dir.parent.exists() else Path('.'))
        free_gb = stat.free / (1024**3)
        if free_gb < 5:  # Require at least 5GB free
            issues.append(f"Insufficient disk space: {free_gb:.1f}GB free (minimum 5GB required)")
    except Exception as e:
        issues.append(f"Cannot check disk space: {e}")
    
    return issues

def generate_migration_summary(migration_results: Dict[str, Any]) -> str:
    """Generate human-readable migration summary"""
    summary = []
    summary.append("=" * 70)
    summary.append("CLO DATA MIGRATION SUMMARY")
    summary.append("=" * 70)
    
    migration_id = migration_results.get('migration_id', 'Unknown')
    summary.append(f"Migration ID: {migration_id}")
    
    success = migration_results.get('success', False)
    summary.append(f"Status: {'✅ SUCCESS' if success else '❌ FAILED'}")
    
    # Data summary
    raw_count = migration_results.get('raw_assets_extracted', 0)
    transformed_count = migration_results.get('assets_transformed', 0)
    loaded_count = migration_results.get('load_statistics', {}).get('assets_loaded', 0)
    
    summary.append(f"\nData Processing:")
    summary.append(f"  Raw Assets Extracted: {raw_count:,}")
    summary.append(f"  Assets Transformed: {transformed_count:,}")
    summary.append(f"  Assets Loaded: {loaded_count:,}")
    
    # Validation results
    validation = migration_results.get('validation_results', {})
    if validation:
        summary.append(f"\nValidation Results:")
        summary.append(f"  Asset Count Check: {'✅ PASS' if validation.get('asset_count_check') else '❌ FAIL'}")
        summary.append(f"  Data Completeness: {'✅ PASS' if validation.get('data_completeness_check') else '❌ FAIL'}")
        summary.append(f"  Data Accuracy: {'✅ PASS' if validation.get('data_accuracy_check') else '❌ FAIL'}")
    
    # Performance metrics
    load_stats = migration_results.get('load_statistics', {})
    if 'start_time' in load_stats and 'end_time' in load_stats:
        duration = (load_stats['end_time'] - load_stats['start_time']).total_seconds()
        summary.append(f"\nPerformance:")
        summary.append(f"  Migration Duration: {duration:.1f} seconds")
        summary.append(f"  Processing Rate: {loaded_count / max(duration, 1):.1f} assets/second")
    
    summary.append("=" * 70)
    
    return "\n".join(summary)

if __name__ == "__main__":
    # Example usage
    print("CLO Data Migration Utilities")
    print("Available utility classes:")
    print("  - BackupManager: Database backup and restore")
    print("  - DataQualityScanner: Data quality analysis")
    print("  - MigrationRollback: Rollback capabilities")
    print("  - PerformanceMonitor: Performance benchmarking")
    print("  - BatchProcessor: Batch processing utilities")
    print("\nImport this module to use these utilities in migration scripts.")