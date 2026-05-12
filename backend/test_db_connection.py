#!/usr/bin/env python3
"""
Test database connection to PostgreSQL
"""

import sys
import logging
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Test database connection"""
    
    print("\n" + "="*70)
    print("  SAFEMARKET API - DATABASE CONNECTION TEST")
    print("="*70)
    
    # 1. Load environment variables
    print("\n[1] Loading environment configuration...")
    try:
        from core.config import DATABASE_URL, ENVIRONMENT
        print(f"    [OK] Environment loaded: {ENVIRONMENT}")
        print(f"    [OK] Database URL: {DATABASE_URL}")
    except Exception as e:
        print(f"    [ERROR] Failed to load config: {e}")
        return False
    
    # 2. Test database connection
    print("\n[2] Testing database connection...")
    try:
        from db import test_connection
        if test_connection():
            print("    [OK] PostgreSQL connection SUCCESSFUL")
        else:
            print("    [ERROR] PostgreSQL connection FAILED")
            return False
    except Exception as e:
        print(f"    [ERROR] Connection test error: {e}")
        return False
    
    # 3. Check database tables
    print("\n[3] Checking database tables...")
    try:
        from db import engine
        from sqlalchemy import inspect, text
        
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        print(f"    [OK] Found {len(tables)} tables in database:")
        for table in sorted(tables):
            print(f"       - {table}")
    except Exception as e:
        print(f"    [ERROR] Failed to check tables: {e}")
        return False
    
    # 4. Create tables if they don't exist
    print("\n[4] Ensuring database schema...")
    try:
        from db import Base, engine
        Base.metadata.create_all(bind=engine)
        print("    [OK] Database schema created/verified")
    except Exception as e:
        print(f"    [ERROR] Failed to create schema: {e}")
        return False
    
    # 5. Test a simple query
    print("\n[5] Testing database operations...")
    try:
        from db import engine
        from sqlalchemy import text

        with engine.connect() as connection:
            user_count = connection.execute(text("SELECT COUNT(*) FROM users")).scalar_one()

        print(f"    [OK] Database operations working")
        print(f"    [OK] Current users in database: {user_count}")
    except Exception as e:
        print(f"    [ERROR] Failed to execute query: {e}")
        return False
    
    print("\n" + "="*70)
    print("  ALL TESTS PASSED! Database is ready to use.")
    print("="*70 + "\n")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
