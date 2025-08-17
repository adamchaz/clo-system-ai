"""
Validate Yield Curve Migration
Tests that the migrated yield curve data is working properly
"""

import requests
import json
from datetime import date

def test_yield_curve_api():
    """Test the yield curve API endpoints"""
    base_url = "http://localhost:8000"
    
    print("Testing Yield Curve API Endpoints...")
    
    try:
        # Test list endpoint
        response = requests.get(f"{base_url}/api/v1/yield-curves/")
        if response.status_code == 200:
            data = response.json()
            print(f"List endpoint working: {len(data['curves'])} curves found")
            
            # Test individual curve endpoint
            if data['curves']:
                curve_id = data['curves'][0]['curve_id']
                curve_response = requests.get(f"{base_url}/api/v1/yield-curves/{curve_id}")
                
                if curve_response.status_code == 200:
                    curve_data = curve_response.json()
                    print(f"Individual curve endpoint working: {curve_data['curve_name']}")
                    print(f"  - Rate points: {len(curve_data['rates'])}")
                    print(f"  - Forward rates: {len(curve_data['forward_rates'])}")
                    return True
                else:
                    print(f"Individual curve endpoint failed: {curve_response.status_code}")
                    return False
            else:
                print("No curves found in response")
                return False
        else:
            print(f"List endpoint failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"API test failed: {e}")
        return False

def test_database_direct():
    """Test direct database access"""
    print("\nTesting Direct Database Access...")
    
    try:
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        from app.core.database_config import db_config
        from app.models.yield_curve import YieldCurveModel, YieldCurveService
        
        with db_config.get_db_session('postgresql') as session:
            # Test service functionality
            service = YieldCurveService(session)
            
            # Load a curve
            curve = service.load_yield_curve("USD_LIBOR_2016Q1", date(2016, 3, 23))
            
            if curve:
                print(f"Curve loaded successfully: {curve.name}")
                
                # Test spot rate calculation
                test_date = date(2016, 3, 23)
                spot_rate_3m = curve.spot_rate(test_date, 3)
                spot_rate_12m = curve.spot_rate(test_date, 12)
                
                print(f"Spot rate calculations working:")
                print(f"  - 3-month rate: {spot_rate_3m:.4f} ({spot_rate_3m*100:.2f}%)")
                print(f"  - 12-month rate: {spot_rate_12m:.4f} ({spot_rate_12m*100:.2f}%)")
                
                # Test zero rate calculation
                end_date = date(2016, 6, 23)  # 3 months later
                zero_rate = curve.zero_rate(test_date, end_date)
                print(f"  - Zero rate (3M): {zero_rate:.4f} ({zero_rate*100:.2f}%)")
                
                return True
            else:
                print("Failed to load curve from database")
                return False
                
    except Exception as e:
        print(f"Database test failed: {e}")
        return False

def main():
    """Run all validation tests"""
    print("=" * 50)
    print("YIELD CURVE MIGRATION VALIDATION")
    print("=" * 50)
    
    api_success = test_yield_curve_api()
    db_success = test_database_direct()
    
    print(f"\n" + "=" * 50)
    if api_success and db_success:
        print("ALL TESTS PASSED")
        print("Yield curve migration is fully operational!")
    else:
        print("SOME TESTS FAILED")
        print("Check the errors above for details")
    
    return api_success and db_success

if __name__ == "__main__":
    main()