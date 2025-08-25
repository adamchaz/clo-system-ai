"""
Concentration Threshold Service
Business logic layer for concentration test threshold management with caching
"""

from typing import Optional, List, Dict, Tuple, Any
from datetime import date, datetime, timedelta
from decimal import Decimal
import json
import redis
import logging
from dataclasses import dataclass, asdict

from ..repositories.concentration_threshold_repository import ConcentrationThresholdRepository
from ..models.database.concentration_threshold_models import (
    ConcentrationTestDefinition, DealConcentrationThreshold, ConcentrationTestExecution
)
from ..core.config import settings


logger = logging.getLogger(__name__)


@dataclass
class ThresholdConfiguration:
    """Domain entity for threshold configuration"""
    deal_id: str
    test_id: int
    test_number: int
    test_name: str
    threshold_value: float
    effective_date: str
    expiry_date: Optional[str]
    mag_version: Optional[str]
    threshold_source: str  # 'deal', 'default', 'template'
    is_custom_override: bool
    test_category: str
    result_type: str


@dataclass
class ConcentrationTestResultDetail:
    """Enhanced test result with threshold details"""
    test_id: int
    test_number: int
    test_name: str
    threshold: float
    result: float
    numerator: Optional[float]
    denominator: Optional[float]
    pass_fail_status: str
    excess_amount: Optional[float]
    threshold_source: str
    is_custom_override: bool
    effective_date: str
    mag_version: Optional[str]
    comments: Optional[str]


class ConcentrationThresholdCache:
    """Redis cache manager for concentration test thresholds"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.ttl = getattr(settings, 'THRESHOLD_CACHE_TTL', 3600)  # 1 hour default
        self.prefix = getattr(settings, 'CONCENTRATION_CACHE_PREFIX', 'conc_test:')
    
    def _make_key(self, key_type: str, *args) -> str:
        """Create cache key"""
        return f"{self.prefix}{key_type}:" + ":".join(str(arg) for arg in args)
    
    async def get_threshold(self, deal_id: str, test_id: int, analysis_date: str) -> Optional[Tuple[Decimal, str]]:
        """Get cached threshold value and source"""
        key = self._make_key('threshold', deal_id, test_id, analysis_date)
        try:
            cached_data = await self.redis.get(key)
            if cached_data:
                data = json.loads(cached_data)
                return Decimal(data['value']), data['source']
        except Exception as e:
            logger.warning(f"Cache get error for key {key}: {e}")
        return None
    
    async def cache_threshold(self, deal_id: str, test_id: int, analysis_date: str, 
                            threshold_value: Decimal, source: str):
        """Cache threshold value and source"""
        key = self._make_key('threshold', deal_id, test_id, analysis_date)
        data = {'value': str(threshold_value), 'source': source}
        try:
            await self.redis.setex(key, self.ttl, json.dumps(data))
        except Exception as e:
            logger.warning(f"Cache set error for key {key}: {e}")
    
    async def get_deal_thresholds(self, deal_id: str, analysis_date: str) -> Optional[List[Dict]]:
        """Get cached deal threshold configurations"""
        key = self._make_key('deal_thresholds', deal_id, analysis_date)
        try:
            cached_data = await self.redis.get(key)
            if cached_data:
                return json.loads(cached_data)
        except Exception as e:
            logger.warning(f"Cache get error for key {key}: {e}")
        return None
    
    async def cache_deal_thresholds(self, deal_id: str, analysis_date: str, 
                                  threshold_configs: List[ThresholdConfiguration]):
        """Cache deal threshold configurations"""
        key = self._make_key('deal_thresholds', deal_id, analysis_date)
        data = [asdict(config) for config in threshold_configs]
        try:
            await self.redis.setex(key, self.ttl, json.dumps(data))
        except Exception as e:
            logger.warning(f"Cache set error for key {key}: {e}")
    
    async def invalidate_deal_cache(self, deal_id: str):
        """Invalidate all cached data for a deal"""
        pattern = self._make_key('*', deal_id, '*')
        try:
            keys = await self.redis.keys(pattern)
            if keys:
                await self.redis.delete(*keys)
                logger.info(f"Invalidated {len(keys)} cache keys for deal {deal_id}")
        except Exception as e:
            logger.warning(f"Cache invalidation error for deal {deal_id}: {e}")
    
    async def invalidate_threshold_cache(self, deal_id: str, test_id: int):
        """Invalidate cached thresholds for a specific deal/test"""
        pattern = self._make_key('threshold', deal_id, test_id, '*')
        try:
            keys = await self.redis.keys(pattern)
            if keys:
                await self.redis.delete(*keys)
                logger.info(f"Invalidated {len(keys)} threshold cache keys for deal {deal_id}, test {test_id}")
        except Exception as e:
            logger.warning(f"Threshold cache invalidation error: {e}")


class ConcentrationThresholdService:
    """Business logic service for concentration test threshold management"""
    
    def __init__(self, 
                 repository: ConcentrationThresholdRepository,
                 cache: Optional[ConcentrationThresholdCache] = None):
        self.repository = repository
        self.cache = cache
        self.default_analysis_date = date(2016, 3, 23)
    
    # ========================================
    # Threshold Resolution
    # ========================================
    
    async def resolve_threshold(self, 
                              deal_id: str, 
                              test_id: int, 
                              analysis_date: date) -> Tuple[Decimal, str]:
        """
        Resolve effective threshold with caching and fallback logic
        Returns (threshold_value, threshold_source)
        """
        analysis_date_str = analysis_date.isoformat()
        
        # Try cache first
        if self.cache:
            cached_result = await self.cache.get_threshold(deal_id, test_id, analysis_date_str)
            if cached_result:
                return cached_result
        
        # Resolve from database
        threshold_value, source = await self.repository.resolve_effective_threshold(
            deal_id, test_id, analysis_date
        )
        
        # Cache the result
        if self.cache and threshold_value > 0:
            await self.cache.cache_threshold(
                deal_id, test_id, analysis_date_str, threshold_value, source
            )
        
        return threshold_value, source
    
    async def get_deal_thresholds(self, 
                                deal_id: str, 
                                analysis_date: Optional[date] = None) -> List[ThresholdConfiguration]:
        """Get all threshold configurations for a deal with caching"""
        analysis_date = analysis_date or self.default_analysis_date
        analysis_date_str = analysis_date.isoformat()
        
        # Try cache first
        if self.cache:
            cached_configs = await self.cache.get_deal_thresholds(deal_id, analysis_date_str)
            if cached_configs:
                return [ThresholdConfiguration(**config) for config in cached_configs]
        
        # Get from database
        threshold_pairs = await self.repository.get_all_deal_thresholds(deal_id, analysis_date)
        
        threshold_configs = []
        for test_def, deal_threshold in threshold_pairs:
            if deal_threshold:
                # Deal-specific threshold
                config = ThresholdConfiguration(
                    deal_id=deal_id,
                    test_id=test_def.test_id,
                    test_number=test_def.test_number,
                    test_name=test_def.test_name,
                    threshold_value=float(deal_threshold.threshold_value),
                    effective_date=deal_threshold.effective_date.isoformat(),
                    expiry_date=deal_threshold.expiry_date.isoformat() if deal_threshold.expiry_date else None,
                    mag_version=deal_threshold.mag_version,
                    threshold_source='deal',
                    is_custom_override=True,
                    test_category=test_def.test_category,
                    result_type=test_def.result_type
                )
            else:
                # Default threshold from test definition
                config = ThresholdConfiguration(
                    deal_id=deal_id,
                    test_id=test_def.test_id,
                    test_number=test_def.test_number,
                    test_name=test_def.test_name,
                    threshold_value=float(test_def.default_threshold) if test_def.default_threshold else 0.0,
                    effective_date=analysis_date.isoformat(),
                    expiry_date=None,
                    mag_version=None,
                    threshold_source='default',
                    is_custom_override=False,
                    test_category=test_def.test_category,
                    result_type=test_def.result_type
                )
            
            threshold_configs.append(config)
        
        # Cache the result
        if self.cache:
            await self.cache.cache_deal_thresholds(deal_id, analysis_date_str, threshold_configs)
        
        return threshold_configs
    
    # ========================================
    # Threshold Management
    # ========================================
    
    async def create_threshold_override(self,
                                      deal_id: str,
                                      test_id: int,
                                      threshold_value: Decimal,
                                      effective_date: date,
                                      user_id: int,
                                      expiry_date: Optional[date] = None,
                                      mag_version: Optional[str] = None,
                                      notes: Optional[str] = None) -> ThresholdConfiguration:
        """Create deal-specific threshold override with validation"""
        
        # Validate threshold value
        await self._validate_threshold_value(test_id, threshold_value)
        
        # Validate effective date
        if effective_date > date.today() + timedelta(days=365):
            raise ValueError("Effective date cannot be more than 1 year in the future")
        
        if expiry_date and expiry_date <= effective_date:
            raise ValueError("Expiry date must be after effective date")
        
        # Create threshold record
        deal_threshold = await self.repository.create_deal_threshold(
            deal_id=deal_id,
            test_id=test_id,
            threshold_value=threshold_value,
            effective_date=effective_date,
            created_by=user_id,
            expiry_date=expiry_date,
            mag_version=mag_version,
            notes=notes
        )
        
        # Invalidate cache
        if self.cache:
            await self.cache.invalidate_threshold_cache(deal_id, test_id)
            await self.cache.invalidate_deal_cache(deal_id)
        
        # Get test definition for complete configuration
        test_def = await self.repository.get_test_definition(test_id)
        
        return ThresholdConfiguration(
            deal_id=deal_id,
            test_id=test_id,
            test_number=test_def.test_number,
            test_name=test_def.test_name,
            threshold_value=float(threshold_value),
            effective_date=effective_date.isoformat(),
            expiry_date=expiry_date.isoformat() if expiry_date else None,
            mag_version=mag_version,
            threshold_source='deal',
            is_custom_override=True,
            test_category=test_def.test_category,
            result_type=test_def.result_type
        )
    
    async def get_threshold_history(self, 
                                  deal_id: str, 
                                  test_id: int) -> List[Dict[str, Any]]:
        """Get complete history of threshold changes"""
        history = await self.repository.get_threshold_history(deal_id, test_id)
        
        return [
            {
                'id': threshold.id,
                'threshold_value': float(threshold.threshold_value),
                'effective_date': threshold.effective_date.isoformat(),
                'expiry_date': threshold.expiry_date.isoformat() if threshold.expiry_date else None,
                'mag_version': threshold.mag_version,
                'rating_agency': threshold.rating_agency,
                'notes': threshold.notes,
                'created_by': threshold.created_by,
                'created_at': threshold.created_at.isoformat(),
                'updated_at': threshold.updated_at.isoformat()
            }
            for threshold in history
        ]
    
    # ========================================
    # Test Execution Integration
    # ========================================
    
    async def save_test_results(self,
                              deal_id: str,
                              analysis_date: date,
                              test_results: List[Dict[str, Any]]) -> List[ConcentrationTestExecution]:
        """Save concentration test execution results with threshold details"""
        
        executions = []
        for result in test_results:
            execution = await self.repository.save_test_execution(
                deal_id=deal_id,
                test_id=result['test_id'],
                analysis_date=analysis_date,
                threshold_used=Decimal(str(result['threshold'])),
                calculated_value=Decimal(str(result['result'])),
                pass_fail_status=result['pass_fail_status'],
                threshold_source=result.get('threshold_source', 'default'),
                numerator=Decimal(str(result['numerator'])) if result.get('numerator') else None,
                denominator=Decimal(str(result['denominator'])) if result.get('denominator') else None,
                excess_amount=Decimal(str(result.get('excess_amount', 0))),
                comments=result.get('comments')
            )
            executions.append(execution)
        
        # Create summary
        total_tests = len(test_results)
        passed_tests = sum(1 for r in test_results if r['pass_fail_status'] == 'PASS')
        failed_tests = sum(1 for r in test_results if r['pass_fail_status'] == 'FAIL')
        na_tests = sum(1 for r in test_results if r['pass_fail_status'] == 'N/A')
        
        total_violations = sum(
            Decimal(str(r.get('excess_amount', 0))) 
            for r in test_results if r['pass_fail_status'] == 'FAIL'
        )
        
        # Find worst violation
        worst_violation = None
        worst_amount = Decimal('0')
        for r in test_results:
            if r['pass_fail_status'] == 'FAIL' and r.get('excess_amount', 0) > worst_amount:
                worst_amount = Decimal(str(r['excess_amount']))
                worst_violation = r['test_id']
        
        await self.repository.create_test_summary(
            deal_id=deal_id,
            analysis_date=analysis_date,
            total_tests=total_tests,
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            na_tests=na_tests,
            total_violations=total_violations,
            worst_violation_test_id=worst_violation,
            worst_violation_amount=worst_amount if worst_violation else None
        )
        
        return executions
    
    async def get_test_results_with_thresholds(self,
                                             deal_id: str,
                                             analysis_date: date) -> Dict[str, Any]:
        """Get test execution results with complete threshold details"""
        
        executions = await self.repository.get_test_executions(deal_id, analysis_date)
        threshold_configs = await self.get_deal_thresholds(deal_id, analysis_date)
        
        # Create lookup for threshold configs
        config_lookup = {config.test_id: config for config in threshold_configs}
        
        detailed_results = []
        for execution in executions:
            config = config_lookup.get(execution.test_id)
            
            result = ConcentrationTestResultDetail(
                test_id=execution.test_id,
                test_number=config.test_number if config else 0,
                test_name=config.test_name if config else "Unknown Test",
                threshold=float(execution.threshold_used),
                result=float(execution.calculated_value),
                numerator=float(execution.numerator) if execution.numerator else None,
                denominator=float(execution.denominator) if execution.denominator else None,
                pass_fail_status=execution.pass_fail_status,
                excess_amount=float(execution.excess_amount) if execution.excess_amount else None,
                threshold_source=execution.threshold_source,
                is_custom_override=config.is_custom_override if config else False,
                effective_date=config.effective_date if config else analysis_date.isoformat(),
                mag_version=config.mag_version if config else None,
                comments=execution.comments
            )
            detailed_results.append(result)
        
        # Get summary
        summary = await self.repository.get_test_summary(deal_id, analysis_date)
        
        return {
            'deal_id': deal_id,
            'analysis_date': analysis_date.isoformat(),
            'test_results': [asdict(result) for result in detailed_results],
            'summary': {
                'total_tests': summary.total_tests if summary else len(detailed_results),
                'passed_tests': summary.passed_tests if summary else sum(1 for r in detailed_results if r.pass_fail_status == 'PASS'),
                'failed_tests': summary.failed_tests if summary else sum(1 for r in detailed_results if r.pass_fail_status == 'FAIL'),
                'na_tests': summary.na_tests if summary else sum(1 for r in detailed_results if r.pass_fail_status == 'N/A'),
                'total_violations': float(summary.total_violations) if summary else 0.0,
                'pass_rate': summary.pass_rate if summary else 0.0
            }
        }
    
    # ========================================
    # Validation Methods
    # ========================================
    
    async def _validate_threshold_value(self, test_id: int, threshold_value: Decimal):
        """Business validation for threshold values"""
        test_def = await self.repository.get_test_definition(test_id)
        
        if not test_def:
            raise ValueError(f"Test ID {test_id} not found")
        
        if not test_def.is_active:
            raise ValueError(f"Test {test_def.test_name} is not active")
        
        # Type-specific validation
        if test_def.result_type == 'percentage':
            if threshold_value < 0 or threshold_value > 100:
                raise ValueError("Percentage thresholds must be between 0 and 100")
        
        elif test_def.result_type == 'rating_factor':
            if threshold_value < 0 or threshold_value > 10000:
                raise ValueError("Rating factor thresholds must be between 0 and 10000")
        
        elif test_def.result_type == 'years':
            if threshold_value < 0 or threshold_value > 50:
                raise ValueError("Year thresholds must be between 0 and 50")
        
        elif test_def.result_type == 'absolute':
            if threshold_value < 0:
                raise ValueError("Absolute thresholds must be positive")
        
        # Test-specific business rules
        if test_def.test_number == 4 and threshold_value > 5:  # Single obligor limit
            raise ValueError("Single obligor concentration cannot exceed 5%")
        
        if test_def.test_category == 'rating' and test_def.result_type == 'percentage':
            if threshold_value > 50:  # Most rating concentration limits
                logger.warning(f"High rating concentration threshold: {threshold_value}% for {test_def.test_name}")
    
    # ========================================
    # Utility Methods
    # ========================================
    
    async def get_system_statistics(self) -> Dict[str, Any]:
        """Get comprehensive system statistics"""
        base_stats = await self.repository.get_threshold_statistics()
        
        # Add cache statistics if available
        if self.cache:
            try:
                cache_info = await self.cache.redis.info('memory')
                base_stats.update({
                    'cache_memory_used': cache_info.get('used_memory_human', 'N/A'),
                    'cache_connected': True
                })
            except Exception:
                base_stats['cache_connected'] = False
        else:
            base_stats['cache_connected'] = False
        
        return base_stats