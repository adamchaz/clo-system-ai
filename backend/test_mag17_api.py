#!/usr/bin/env python3
"""
Direct test of MAG17 API endpoint functionality
"""

import sys
sys.path.append('.')

from app.core.database_config import db_config
from sqlalchemy import text
from fastapi.testclient import TestClient
from app.main import app

def test_database_query():
    """Test the database query directly"""
    print("Testing database query...")
    
    try:
        with db_config.get_db_session('postgresql') as session:
            # Test the exact MAG17 query from the API
            asset_result = session.execute(text("""
                SELECT COUNT(*) as count, COALESCE(SUM(par_amount), 0) as total_par
                FROM assets 
                WHERE par_amount > 0 
                AND created_at::date = CURRENT_DATE
            """))
            asset_data = asset_result.fetchone()
            
            print(f"Database results: {asset_data.count} assets, ${asset_data.total_par:,.2f} par")
            return asset_data.count, float(asset_data.total_par)
            
    except Exception as e:
        print(f"Database query error: {e}")
        return None, None

def test_portfolio_list_api():
    """Test the portfolio list API"""
    print("\nTesting portfolio list API...")
    
    client = TestClient(app)
    try:
        response = client.get("/api/v1/portfolios/")
        
        if response.status_code == 200:
            data = response.json()
            
            # Find MAG17
            for portfolio in data['data']:
                if portfolio['id'] == 'MAG17':
                    print(f"MAG17 in list: {portfolio['current_asset_count']} assets, ${portfolio['current_portfolio_balance']:,.2f}")
                    return portfolio['current_asset_count'], portfolio['current_portfolio_balance']
            
            print("MAG17 not found in portfolio list")
            return None, None
        else:
            print(f"API error: {response.status_code} - {response.text}")
            return None, None
            
    except Exception as e:
        print(f"API test error: {e}")
        return None, None

def test_mag17_detail_api():
    """Test the MAG17 detail API"""
    print("\nTesting MAG17 detail API...")
    
    client = TestClient(app)
    try:
        response = client.get("/api/v1/portfolios/MAG17")
        
        if response.status_code == 200:
            data = response.json()
            print(f"MAG17 details: {data['current_asset_count']} assets, ${data['current_portfolio_balance']:,.2f}")
            print(f"Tranches: {len(data.get('tranches', []))}")
            return True
        else:
            print(f"MAG17 detail API error: {response.status_code}")
            print(f"Error details: {response.text}")
            return False
            
    except Exception as e:
        print(f"MAG17 detail test error: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("MAG17 API FUNCTIONALITY TEST")
    print("=" * 60)
    
    # Test database
    db_count, db_par = test_database_query()
    
    # Test API endpoints
    list_count, list_par = test_portfolio_list_api()
    detail_success = test_mag17_detail_api()
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    if db_count and db_par:
        print(f"✓ Database: {db_count} assets, ${db_par:,.2f}")
    else:
        print("✗ Database query failed")
    
    if list_count and list_par:
        if list_count == db_count and abs(list_par - db_par) < 1000:
            print(f"✓ Portfolio List API: Correct data")
        else:
            print(f"⚠ Portfolio List API: Shows {list_count} assets, ${list_par:,.2f} (mismatch)")
    else:
        print("✗ Portfolio List API failed")
    
    if detail_success:
        print("✓ MAG17 Detail API: Working")
    else:
        print("✗ MAG17 Detail API: Failed")
    
    print("=" * 60)

if __name__ == "__main__":
    main()