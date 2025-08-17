#!/usr/bin/env python3
"""
Test database connections for CLO system
"""

import psycopg2
import redis
import time

def test_postgresql():
    """Test PostgreSQL connection"""
    print("Testing PostgreSQL Connection...")
    
    try:
        # Connection parameters - try with adamchaz password to CLO database on port 5433
        conn = psycopg2.connect(
            host='127.0.0.1',
            port=5433,
            database='clo_dev', 
            user='postgres',
            password='adamchaz'
        )
        
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        
        cursor.execute("SELECT current_database();")
        database = cursor.fetchone()[0]
        
        print(f"SUCCESS: Connected to PostgreSQL")
        print(f"Database: {database}")
        print(f"Version: {version}")
        
        # Test creating a simple table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS test_table (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        cursor.execute("INSERT INTO test_table (name) VALUES ('CLO Test');")
        conn.commit()
        
        cursor.execute("SELECT COUNT(*) FROM test_table;")
        count = cursor.fetchone()[0]
        print(f"Test table created with {count} record(s)")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"FAILED: PostgreSQL connection failed: {e}")
        return False

def test_redis():
    """Test Redis connection"""
    print("\nTesting Redis Connection...")
    
    try:
        # Connect to Redis
        r = redis.Redis(host='localhost', port=6379, decode_responses=True)
        
        # Test connection
        r.ping()
        
        # Test basic operations
        r.set('test_key', 'CLO System Test')
        value = r.get('test_key')
        
        # Test hash operations (useful for asset correlation matrices)
        r.hset('test_asset', mapping={
            'par_amount': 1000000,
            'coupon_rate': 0.05,
            'rating': 'AAA'
        })
        
        asset_data = r.hgetall('test_asset')
        
        print(f"SUCCESS: Connected to Redis")
        print(f"Test value: {value}")
        print(f"Test asset data: {asset_data}")
        
        # Clean up
        r.delete('test_key', 'test_asset')
        
        return True
        
    except Exception as e:
        print(f"FAILED: Redis connection failed: {e}")
        return False

def test_sqlalchemy():
    """Test SQLAlchemy ORM connection"""
    print("\nTesting SQLAlchemy ORM...")
    
    try:
        from sqlalchemy import create_engine, text
        from sqlalchemy.orm import sessionmaker
        
        # Create engine with adamchaz password for CLO database on port 5433
        DATABASE_URL = "postgresql://postgres:adamchaz@127.0.0.1:5433/clo_dev"
        engine = create_engine(DATABASE_URL)
        
        # Test connection
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 'SQLAlchemy connection successful' as message;"))
            message = result.fetchone()[0]
            print(f"SUCCESS: {message}")
            
        # Test session
        Session = sessionmaker(bind=engine)
        session = Session()
        session.close()
        
        print("SQLAlchemy ORM ready for CLO models")
        
        return True
        
    except Exception as e:
        print(f"FAILED: SQLAlchemy connection failed: {e}")
        return False

def main():
    """Run all database tests"""
    print("CLO System Database Environment Test")
    print("=" * 50)
    
    results = []
    
    # Test each component
    tests = [
        ("PostgreSQL", test_postgresql),
        ("Redis", test_redis), 
        ("SQLAlchemy", test_sqlalchemy)
    ]
    
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            print(f"FAILED: {name} test crashed: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("Database Environment Test Summary:")
    print("=" * 50)
    
    passed = 0
    for name, success in results:
        status = "PASS" if success else "FAIL"
        print(f"{status}: {name}")
        if success:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("\nSUCCESS: Database environment is ready!")
        print("- PostgreSQL: Ready for CLO asset and deal data")
        print("- Redis: Ready for correlation matrix caching") 
        print("- SQLAlchemy: Ready for ORM model development")
    else:
        print("\nIssues detected. Check database configuration.")
    
    return passed == len(results)

if __name__ == "__main__":
    main()