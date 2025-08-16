"""
Data Integration Service
Integrates migrated SQLite data with operational PostgreSQL database
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, date
from decimal import Decimal
import json
from sqlalchemy import text, and_, or_
from sqlalchemy.exc import IntegrityError

from ..core.database_config import get_db_session, get_redis
from ..models.asset import Asset
from ..models.clo_deal import CLODeal, DealAsset
from ..models.cash_flow import AssetCashFlow

logger = logging.getLogger(__name__)

class DataIntegrationService:
    """Service for integrating migrated data with operational database"""
    
    def __init__(self):
        self.redis_client = get_redis()
        
        # Migration database mappings
        self.migration_db_mapping = {
            'assets': 'assets',
            'correlations': 'correlations', 
            'scenarios': 'scenarios',
            'config': 'config',
            'reference': 'reference'
        }
    
    def sync_assets_to_operational(self) -> Dict[str, Any]:
        """Sync migrated assets to operational database"""
        logger.info("Starting asset synchronization to operational database...")
        
        stats = {
            'assets_processed': 0,
            'assets_created': 0,
            'assets_updated': 0,
            'errors': []
        }
        
        try:
            # Read from migrated assets database
            with get_db_session('assets') as source_session:
                # Query all migrated assets
                migrated_assets = source_session.execute(text("""
                    SELECT * FROM assets
                """)).fetchall()
                
                logger.info(f"Found {len(migrated_assets)} migrated assets")
                stats['assets_processed'] = len(migrated_assets)
            
            # Write to operational database
            with get_db_session('postgresql') as target_session:
                for asset_row in migrated_assets:
                    try:
                        # Convert row to dict (adjust based on actual column names)
                        asset_data = dict(asset_row._mapping) if hasattr(asset_row, '_mapping') else dict(asset_row)
                        
                        # Check if asset already exists
                        existing_asset = target_session.query(Asset).filter_by(
                            blkrock_id=asset_data.get('blkrock_id')
                        ).first()
                        
                        if existing_asset:
                            # Update existing asset
                            self._update_asset_from_migration(existing_asset, asset_data)
                            stats['assets_updated'] += 1
                        else:
                            # Create new asset
                            new_asset = self._create_asset_from_migration(asset_data)
                            target_session.add(new_asset)
                            stats['assets_created'] += 1
                        
                        # Commit every 50 assets
                        if (stats['assets_created'] + stats['assets_updated']) % 50 == 0:
                            target_session.commit()
                            logger.info(f"Processed {stats['assets_created'] + stats['assets_updated']} assets...")
                    
                    except Exception as e:
                        error_msg = f"Error processing asset {asset_data.get('blkrock_id', 'unknown')}: {e}"
                        logger.error(error_msg)
                        stats['errors'].append(error_msg)
                        target_session.rollback()
                
                # Final commit
                target_session.commit()
            
            logger.info(f"✅ Asset sync completed: {stats['assets_created']} created, {stats['assets_updated']} updated")
            return stats
            
        except Exception as e:
            error_msg = f"Fatal error in asset synchronization: {e}"
            logger.error(error_msg)
            stats['errors'].append(error_msg)
            return stats
    
    def _create_asset_from_migration(self, asset_data: Dict[str, Any]) -> Asset:
        """Create Asset model from migrated data"""
        
        # Map migrated data to Asset model fields
        # Note: Adjust field mappings based on actual migrated data schema
        return Asset(
            blkrock_id=asset_data.get('blkrock_id'),
            issue_name=asset_data.get('issue_name'),
            issuer_name=asset_data.get('issuer_name'),
            bond_loan=asset_data.get('bond_loan'),
            par_amount=self._safe_decimal(asset_data.get('par_amount')),
            maturity=self._safe_date(asset_data.get('maturity')),
            dated_date=self._safe_date(asset_data.get('dated_date')),
            issue_date=self._safe_date(asset_data.get('issue_date')),
            first_payment_date=self._safe_date(asset_data.get('first_payment_date')),
            coupon=self._safe_decimal(asset_data.get('coupon')),
            coupon_type=asset_data.get('coupon_type'),
            index_name=asset_data.get('index_name'),
            cpn_spread=self._safe_decimal(asset_data.get('cpn_spread')),
            libor_floor=self._safe_decimal(asset_data.get('libor_floor')),
            payment_freq=asset_data.get('payment_freq'),
            mdy_rating=asset_data.get('mdy_rating'),
            mdy_dp_rating=asset_data.get('mdy_dp_rating'),
            mdy_dp_rating_warf=asset_data.get('mdy_dp_rating_warf'),
            mdy_recovery_rate=self._safe_decimal(asset_data.get('mdy_recovery_rate')),
            sp_rating=asset_data.get('sp_rating'),
            mdy_industry=asset_data.get('mdy_industry'),
            sp_industry=asset_data.get('sp_industry'),
            country=asset_data.get('country'),
            seniority=asset_data.get('seniority'),
            market_value=self._safe_decimal(asset_data.get('market_value')),
            facility_size=self._safe_decimal(asset_data.get('facility_size')),
            wal=self._safe_decimal(asset_data.get('wal')),
            # Add other fields as needed based on migrated schema
        )
    
    def _update_asset_from_migration(self, existing_asset: Asset, asset_data: Dict[str, Any]):
        """Update existing asset with migrated data"""
        
        # Update fields that might have changed
        if asset_data.get('issue_name'):
            existing_asset.issue_name = asset_data['issue_name']
        if asset_data.get('par_amount'):
            existing_asset.par_amount = self._safe_decimal(asset_data['par_amount'])
        if asset_data.get('market_value'):
            existing_asset.market_value = self._safe_decimal(asset_data['market_value'])
        if asset_data.get('mdy_rating'):
            existing_asset.mdy_rating = asset_data['mdy_rating']
        if asset_data.get('sp_rating'):
            existing_asset.sp_rating = asset_data['sp_rating']
        
        # Update timestamp
        existing_asset.updated_at = datetime.now()
    
    def cache_correlation_matrix(self) -> Dict[str, Any]:
        """Cache correlation matrix in Redis for performance"""
        logger.info("Caching correlation matrix in Redis...")
        
        if not self.redis_client:
            logger.warning("Redis not available, skipping correlation cache")
            return {'success': False, 'error': 'Redis unavailable'}
        
        try:
            # Read correlation matrix from migrated database
            with get_db_session('correlations') as session:
                correlations = session.execute(text("""
                    SELECT asset1_id, asset2_id, correlation_value 
                    FROM asset_correlations 
                    LIMIT 10000
                """)).fetchall()
                
                logger.info(f"Caching {len(correlations)} correlation pairs...")
                
                # Cache individual correlation pairs
                pipe = self.redis_client.pipeline()
                for corr in correlations:
                    key = f"corr:{corr[0]}:{corr[1]}"
                    pipe.setex(key, 3600, str(corr[2]))  # 1 hour TTL
                
                pipe.execute()
                
                # Cache matrix metadata
                matrix_info = {
                    'size': '488x488',
                    'total_pairs': len(correlations),
                    'cached_at': datetime.now().isoformat()
                }
                self.redis_client.setex(
                    'correlation_matrix_info', 
                    3600, 
                    json.dumps(matrix_info)
                )
                
                logger.info("✅ Correlation matrix cached successfully")
                return {'success': True, 'cached_pairs': len(correlations)}
        
        except Exception as e:
            error_msg = f"Error caching correlation matrix: {e}"
            logger.error(error_msg)
            return {'success': False, 'error': error_msg}
    
    def get_correlation(self, asset1_id: str, asset2_id: str) -> Optional[Decimal]:
        """Get correlation between two assets (from cache or database)"""
        
        # Try cache first
        if self.redis_client:
            try:
                key = f"corr:{asset1_id}:{asset2_id}"
                cached_value = self.redis_client.get(key)
                if cached_value:
                    return Decimal(cached_value.decode('utf-8'))
            except Exception as e:
                logger.warning(f"Redis cache lookup failed: {e}")
        
        # Fallback to database
        try:
            with get_db_session('correlations') as session:
                result = session.execute(text("""
                    SELECT correlation_value 
                    FROM asset_correlations 
                    WHERE asset1_id = :asset1 AND asset2_id = :asset2
                """), {'asset1': asset1_id, 'asset2': asset2_id}).fetchone()
                
                return Decimal(str(result[0])) if result else None
                
        except Exception as e:
            logger.error(f"Error retrieving correlation: {e}")
            return None
    
    def sync_scenario_parameters(self) -> Dict[str, Any]:
        """Sync MAG scenario parameters for operational use"""
        logger.info("Syncing MAG scenario parameters...")
        
        try:
            # Cache scenario parameters in Redis for fast access
            if self.redis_client:
                with get_db_session('scenarios') as session:
                    scenarios = session.execute(text("""
                        SELECT scenario_name, parameter_name, parameter_value, parameter_type
                        FROM scenario_inputs
                        ORDER BY scenario_name, parameter_name
                    """)).fetchall()
                    
                    # Group by scenario
                    scenario_data = {}
                    for row in scenarios:
                        scenario = row[0]
                        if scenario not in scenario_data:
                            scenario_data[scenario] = {}
                        scenario_data[scenario][row[1]] = {
                            'value': row[2],
                            'type': row[3]
                        }
                    
                    # Cache each scenario
                    for scenario_name, params in scenario_data.items():
                        cache_key = f"scenario:{scenario_name}"
                        self.redis_client.setex(
                            cache_key, 
                            7200,  # 2 hour TTL
                            json.dumps(params, default=str)
                        )
                    
                    logger.info(f"✅ Cached {len(scenario_data)} scenarios")
                    return {'success': True, 'scenarios_cached': len(scenario_data)}
        
        except Exception as e:
            error_msg = f"Error syncing scenario parameters: {e}"
            logger.error(error_msg)
            return {'success': False, 'error': error_msg}
    
    def get_scenario_parameters(self, scenario_name: str) -> Dict[str, Any]:
        """Get parameters for a specific scenario"""
        
        # Try cache first
        if self.redis_client:
            try:
                cache_key = f"scenario:{scenario_name}"
                cached_data = self.redis_client.get(cache_key)
                if cached_data:
                    return json.loads(cached_data.decode('utf-8'))
            except Exception as e:
                logger.warning(f"Scenario cache lookup failed: {e}")
        
        # Fallback to database
        try:
            with get_db_session('scenarios') as session:
                params = session.execute(text("""
                    SELECT parameter_name, parameter_value, parameter_type
                    FROM scenario_inputs
                    WHERE scenario_name = :scenario
                """), {'scenario': scenario_name}).fetchall()
                
                return {
                    row[0]: {'value': row[1], 'type': row[2]} 
                    for row in params
                }
                
        except Exception as e:
            logger.error(f"Error retrieving scenario parameters: {e}")
            return {}
    
    def run_full_integration(self) -> Dict[str, Any]:
        """Run complete data integration process"""
        logger.info("🚀 Starting full data integration...")
        
        results = {
            'start_time': datetime.now(),
            'asset_sync': {},
            'correlation_cache': {},
            'scenario_sync': {},
            'success': True
        }
        
        # Step 1: Sync assets
        logger.info("📊 Step 1: Syncing assets to operational database...")
        results['asset_sync'] = self.sync_assets_to_operational()
        
        # Step 2: Cache correlation matrix
        logger.info("🔗 Step 2: Caching correlation matrix...")
        results['correlation_cache'] = self.cache_correlation_matrix()
        
        # Step 3: Sync scenario parameters
        logger.info("🎯 Step 3: Syncing scenario parameters...")
        results['scenario_sync'] = self.sync_scenario_parameters()
        
        # Check overall success
        results['success'] = all([
            not results['asset_sync'].get('errors'),
            results['correlation_cache'].get('success', False),
            results['scenario_sync'].get('success', False)
        ])
        
        results['end_time'] = datetime.now()
        results['duration'] = (results['end_time'] - results['start_time']).total_seconds()
        
        if results['success']:
            logger.info("🎉 Data integration completed successfully!")
        else:
            logger.warning("⚠️ Data integration completed with some issues")
        
        return results
    
    def _safe_decimal(self, value: Any) -> Optional[Decimal]:
        """Safely convert value to Decimal"""
        if value is None:
            return None
        try:
            return Decimal(str(value))
        except (ValueError, TypeError):
            return None
    
    def get_assets_paginated(self, skip: int = 0, limit: int = 100, asset_type: Optional[str] = None, rating: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get paginated list of assets from PostgreSQL database"""
        try:
            with get_db_session('postgresql') as session:
                query = "SELECT * FROM assets"
                params = {}
                where_conditions = []
                
                if asset_type:
                    where_conditions.append("bond_loan = :asset_type")
                    params['asset_type'] = asset_type
                    
                if rating:
                    where_conditions.append("(mdy_rating = :rating OR sp_rating = :rating)")
                    params['rating'] = rating
                
                if where_conditions:
                    query += " WHERE " + " AND ".join(where_conditions)
                
                query += f" LIMIT {limit} OFFSET {skip}"
                
                result = session.execute(text(query), params).fetchall()
                
                # Convert to dict format and map to API schema
                assets = []
                for row in result:
                    row_dict = dict(row._mapping) if hasattr(row, '_mapping') else dict(row)
                    
                    # Map database fields to API schema fields
                    asset_dict = {
                        'id': row_dict.get('blkrock_id'),
                        'cusip': row_dict.get('cusip'),  # Will be None if not in DB
                        'isin': row_dict.get('isin'),    # Will be None if not in DB
                        'asset_name': row_dict.get('issue_name'),
                        'asset_type': row_dict.get('bond_loan'),
                        'industry': row_dict.get('mdy_industry'),
                        'sector': row_dict.get('sp_industry'), 
                        'current_balance': row_dict.get('par_amount'),
                        'original_balance': row_dict.get('facility_size'),
                        'coupon_rate': row_dict.get('coupon'),
                        'maturity_date': row_dict.get('maturity'),
                        'rating': row_dict.get('mdy_rating') or row_dict.get('sp_rating'),
                        'created_at': row_dict.get('created_at'),
                        'updated_at': row_dict.get('updated_at'),
                        'is_active': True,  # Default to active
                        'days_to_maturity': None,  # Could calculate this
                        'yield_to_maturity': None,  # Not available yet
                        'duration': row_dict.get('wal')  # Weighted Average Life as proxy
                    }
                    assets.append(asset_dict)
                
                return assets
                
        except Exception as e:
            logger.error(f"Error fetching paginated assets: {e}")
            return []
    
    def get_assets_count(self, asset_type: Optional[str] = None, rating: Optional[str] = None) -> int:
        """Get total count of assets with optional filtering"""
        try:
            with get_db_session('postgresql') as session:
                query = "SELECT COUNT(*) FROM assets"
                params = {}
                where_conditions = []
                
                if asset_type:
                    where_conditions.append("bond_loan = :asset_type")
                    params['asset_type'] = asset_type
                    
                if rating:
                    where_conditions.append("(mdy_rating = :rating OR sp_rating = :rating)")
                    params['rating'] = rating
                
                if where_conditions:
                    query += " WHERE " + " AND ".join(where_conditions)
                
                result = session.execute(text(query), params).fetchone()
                return result[0] if result else 0
                
        except Exception as e:
            logger.error(f"Error counting assets: {e}")
            return 0
    
    def get_asset_by_id(self, asset_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific asset by ID from PostgreSQL database"""
        try:
            with get_db_session('postgresql') as session:
                result = session.execute(text("""
                    SELECT * FROM assets 
                    WHERE blkrock_id = :asset_id
                """), {'asset_id': asset_id}).fetchone()
                
                if result:
                    row_dict = dict(result._mapping) if hasattr(result, '_mapping') else dict(result)
                    
                    # Map database fields to API schema fields
                    asset_dict = {
                        'id': row_dict.get('blkrock_id'),
                        'cusip': row_dict.get('cusip'),  # Will be None if not in DB
                        'isin': row_dict.get('isin'),    # Will be None if not in DB
                        'asset_name': row_dict.get('issue_name'),
                        'asset_type': row_dict.get('bond_loan'),
                        'industry': row_dict.get('mdy_industry'),
                        'sector': row_dict.get('sp_industry'), 
                        'current_balance': row_dict.get('par_amount'),
                        'original_balance': row_dict.get('facility_size'),
                        'coupon_rate': row_dict.get('coupon'),
                        'maturity_date': row_dict.get('maturity'),
                        'rating': row_dict.get('mdy_rating') or row_dict.get('sp_rating'),
                        'created_at': row_dict.get('created_at'),
                        'updated_at': row_dict.get('updated_at'),
                        'is_active': True,  # Default to active
                        'days_to_maturity': None,  # Could calculate this
                        'yield_to_maturity': None,  # Not available yet
                        'duration': row_dict.get('wal')  # Weighted Average Life as proxy
                    }
                    return asset_dict
                return None
                
        except Exception as e:
            logger.error(f"Error fetching asset {asset_id}: {e}")
            return None
    
    def get_asset_correlations(self, asset_id: str, limit: int = 50, threshold: Optional[float] = None) -> List[Dict[str, Any]]:
        """Get correlations for a specific asset"""
        try:
            with get_db_session('correlations') as session:
                query = """
                    SELECT asset1_id, asset2_id, correlation_value 
                    FROM asset_correlations 
                    WHERE asset1_id = :asset_id OR asset2_id = :asset_id
                """
                params = {'asset_id': asset_id}
                
                if threshold is not None:
                    query += " AND ABS(correlation_value) >= :threshold"
                    params['threshold'] = threshold
                
                query += f" LIMIT {limit}"
                
                result = session.execute(text(query), params).fetchall()
                
                correlations = []
                for row in result:
                    correlations.append({
                        'asset_id_1': row[0],
                        'asset_id_2': row[1],
                        'correlation': float(row[2]),
                        'last_updated': None
                    })
                
                return correlations
                
        except Exception as e:
            logger.error(f"Error fetching correlations for asset {asset_id}: {e}")
            return []
    
    def get_asset_statistics(self) -> Dict[str, Any]:
        """Get asset statistics summary"""
        try:
            stats = {'total_count': 0, 'by_type': {}, 'by_rating': {}, 'correlation_count': 0}
            
            # Get asset counts from PostgreSQL
            with get_db_session('postgresql') as session:
                # Total count
                total_result = session.execute(text("SELECT COUNT(*) FROM assets")).fetchone()
                stats['total_count'] = total_result[0] if total_result else 0
                
                # By type (bond/loan)
                type_result = session.execute(text("""
                    SELECT bond_loan, COUNT(*) 
                    FROM assets 
                    WHERE bond_loan IS NOT NULL 
                    GROUP BY bond_loan
                """)).fetchall()
                stats['by_type'] = {row[0]: row[1] for row in type_result}
                
                # By rating
                rating_result = session.execute(text("""
                    SELECT mdy_rating, COUNT(*) 
                    FROM assets 
                    WHERE mdy_rating IS NOT NULL 
                    GROUP BY mdy_rating
                """)).fetchall()
                stats['by_rating'] = {row[0]: row[1] for row in rating_result}
            
            # Get correlation count (keep this from SQLite correlations DB for now)
            try:
                with get_db_session('correlations') as session:
                    corr_result = session.execute(text("SELECT COUNT(*) FROM asset_correlations")).fetchone()
                    stats['correlation_count'] = corr_result[0] if corr_result else 0
            except Exception:
                stats['correlation_count'] = 0
            
            return stats
            
        except Exception as e:
            logger.error(f"Error fetching asset statistics: {e}")
            return {'total_count': 0, 'by_type': {}, 'by_rating': {}, 'correlation_count': 0}

    def _safe_date(self, value: Any) -> Optional[date]:
        """Safely convert value to date"""
        if value is None:
            return None
        if isinstance(value, date):
            return value
        if isinstance(value, datetime):
            return value.date()
        try:
            # Try parsing string date
            if isinstance(value, str):
                return datetime.strptime(value, '%Y-%m-%d').date()
        except ValueError:
            pass
        return None