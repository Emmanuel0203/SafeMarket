#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PostgreSQL Setup Script for SafeMarket
Automated setup: create database, run migrations, seed data
"""

import sys
import os
import subprocess
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from pathlib import Path
import getpass

# Fix encoding for Windows
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'

# Configuration
PG_USER = os.getenv("PG_USER", "postgres")
PG_PASSWORD = os.getenv("PG_PASSWORD", None)  # Will prompt if not set
PG_HOST = os.getenv("PG_HOST", "localhost")
PG_PORT = int(os.getenv("PG_PORT", "5432"))
DB_NAME = "safemarket"

SCRIPT_DIR = Path(__file__).parent
SCHEMA_FILE = SCRIPT_DIR / "schema_improved.sql"

def print_header(msg):
    """Print formatted header"""
    print("\n" + "="*60)
    print(f"  {msg}")
    print("="*60)

def connect_postgres(db_name=None):
    """Connect to PostgreSQL with better error handling"""
    global PG_PASSWORD
    
    # If password not set, prompt user
    if PG_PASSWORD is None:
        print("\n🔐 PostgreSQL Password Required")
        print(f"   Connecting to: {PG_HOST}:{PG_PORT} as user '{PG_USER}'")
        PG_PASSWORD = getpass.getpass("   Enter password: ")
        
        if not PG_PASSWORD:
            print("❌ Password required")
            sys.exit(1)
    
    try:
        conn = psycopg2.connect(
            user=PG_USER,
            password=PG_PASSWORD,
            host=PG_HOST,
            port=PG_PORT,
            database=db_name or "postgres",
            client_encoding='UTF8'  # Explicit UTF-8 encoding
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        return conn
    except psycopg2.OperationalError as e:
        print(f"❌ Cannot connect to PostgreSQL:")
        print(f"   Host: {PG_HOST}:{PG_PORT}")
        print(f"   User: {PG_USER}")
        print(f"   Error: {str(e)}")
        print("\n💡 Solutions:")
        print("   1. Ensure PostgreSQL is running")
        print("   2. Check password is correct")
        print("   3. Verify host/port are correct")
        print("   4. From command line, test with: psql -U postgres -h localhost -l")
        sys.exit(1)
    except psycopg2.Error as e:
        print(f"❌ Connection error: {str(e)}")
        sys.exit(1)
    except UnicodeDecodeError as e:
        print(f"❌ Encoding error (likely special characters in password):")
        print(f"   {str(e)}")
        print("\n💡 Solutions:")
        print("   1. Password should only contain ASCII characters (a-z, 0-9, @, _, etc.)")
        print("   2. Avoid special characters like: ó, é, ñ, etc.")
        print("   3. Reset PostgreSQL password if needed")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {type(e).__name__}: {str(e)}")
        sys.exit(1)

def database_exists():
    """Check if database exists"""
    try:
        conn = connect_postgres()
        cur = conn.cursor()
        cur.execute(f"SELECT 1 FROM pg_database WHERE datname = '{DB_NAME}'")
        exists = cur.fetchone() is not None
        cur.close()
        conn.close()
        return exists
    except Exception as e:
        # If we can't check, assume it doesn't exist
        print(f"⚠️ Warning checking database: {str(e)}")
        return False

def create_database():
    """Create PostgreSQL database"""
    if database_exists():
        print(f"✓ Database '{DB_NAME}' already exists")
        return
    
    try:
        conn = connect_postgres()
        cur = conn.cursor()
        cur.execute(f"CREATE DATABASE {DB_NAME}")
        cur.close()
        conn.close()
        print(f"✅ Database '{DB_NAME}' created successfully")
    except psycopg2.Error as e:
        print(f"❌ Error creating database: {e}")
        sys.exit(1)

def drop_database():
    """Drop PostgreSQL database (with cleanup)"""
    try:
        conn = connect_postgres()
        cur = conn.cursor()
        
        # Terminate all connections
        cur.execute(f"""
            SELECT pg_terminate_backend(pg_stat_activity.pid)
            FROM pg_stat_activity
            WHERE pg_stat_activity.datname = '{DB_NAME}'
            AND pid <> pg_backend_pid();
        """)
        
        cur.execute(f"DROP DATABASE IF EXISTS {DB_NAME}")
        cur.close()
        conn.close()
        print(f"✅ Database '{DB_NAME}' dropped successfully")
    except psycopg2.Error as e:
        print(f"❌ Error dropping database: {e}")

def run_sql_script(script_file):
    """Execute SQL script with better error handling"""
    if not script_file.exists():
        print(f"❌ Script not found: {script_file}")
        print(f"   Current directory: {Path.cwd()}")
        print(f"   Expected file: {script_file}")
        sys.exit(1)
    
    try:
        print(f"📁 Loading SQL from: {script_file}")
        conn = connect_postgres(DB_NAME)
        cur = conn.cursor()
        
        with open(script_file, 'r', encoding='utf-8') as f:
            sql = f.read()
        
        print(f"📝 SQL file size: {len(sql)} bytes")
        
        # Split by semicolons and execute statements
        statements = [s.strip() for s in sql.split(';') if s.strip()]
        print(f"🔄 Executing {len(statements)} SQL statements...")
        
        success_count = 0
        warning_count = 0
        
        for i, statement in enumerate(statements, 1):
            try:
                cur.execute(statement)
                success_count += 1
                if i % 10 == 0:  # Progress indicator
                    print(f"   [{i}/{len(statements)}] statements executed...")
            except psycopg2.Error as e:
                error_msg = str(e)
                # Skip expected errors
                if any(x in error_msg for x in ["already exists", "duplicate", "ALREADY EXIST"]):
                    warning_count += 1
                else:
                    print(f"⚠️ Statement {i} warning: {error_msg[:100]}")
                    warning_count += 1
        
        conn.commit()
        cur.close()
        conn.close()
        
        print(f"✅ SQL script executed successfully!")
        print(f"   ✓ Statements: {success_count} executed, {warning_count} warnings")
        
    except UnicodeDecodeError as e:
        print(f"❌ File encoding error: {e}")
        print(f"   Make sure schema_improved.sql is UTF-8 encoded")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error executing SQL: {type(e).__name__}: {str(e)}")
        print(f"   Check that database '{DB_NAME}' exists and is accessible")
        sys.exit(1)

def test_connection():
    """Test database connection and data"""
    try:
        conn = connect_postgres(DB_NAME)
        cur = conn.cursor()
        
        # Test basic query
        cur.execute("SELECT NOW()")
        current_time = cur.fetchone()[0]
        print(f"✓ Database time: {current_time}")
        
        # Count data
        tables = {
            'users': "SELECT COUNT(*) FROM users",
            'transactions': "SELECT COUNT(*) FROM transactions",
            'devices': "SELECT COUNT(*) FROM devices",
            'sessions': "SELECT COUNT(*) FROM sessions",
            'alerts': "SELECT COUNT(*) FROM alerts",
        }
        
        for table_name, query in tables.items():
            try:
                cur.execute(query)
                count = cur.fetchone()[0]
                print(f"✓ {table_name.capitalize()}: {count} records")
            except psycopg2.Error:
                print(f"⚠️ {table_name.capitalize()}: table not ready yet")
        
        cur.close()
        conn.close()
        
        print(f"\n✅ Connection test passed!")
        return True
        
    except psycopg2.Error as e:
        print(f"❌ Database error: {str(e)[:200]}")
        return False
    except Exception as e:
        print(f"❌ Test error: {type(e).__name__}: {str(e)[:200]}")
        return False

def show_summary():
    """Show setup summary"""
    try:
        conn = connect_postgres(DB_NAME)
        cur = conn.cursor()
        
        # Count tables
        cur.execute("""
            SELECT COUNT(*)
            FROM information_schema.tables
            WHERE table_schema = 'public'
        """)
        table_count = cur.fetchone()[0]
        
        # List all tables
        cur.execute("""
            SELECT tablename
            FROM pg_tables
            WHERE schemaname = 'public'
            ORDER BY tablename
        """)
        tables = [row[0] for row in cur.fetchall()]
        
        cur.close()
        conn.close()
        
        print(f"\n📊 Database Summary:")
        print(f"   Tables created: {table_count}")
        print(f"   Table list: {', '.join(tables)}")
        
    except Exception as e:
        print(f"⚠️ Error getting summary: {e}")

def main():
    """Main setup flow"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="SafeMarket PostgreSQL Setup",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python setup_postgres.py                    # Interactive setup
  python setup_postgres.py --test-only        # Test connection only
  python setup_postgres.py --reset            # Drop and recreate
  
Environment variables:
  PG_USER=postgres        # PostgreSQL username
  PG_PASSWORD=mypass      # PostgreSQL password (will prompt if not set)
  PG_HOST=localhost       # PostgreSQL host
  PG_PORT=5432            # PostgreSQL port
        """
    )
    parser.add_argument(
        "--drop",
        action="store_true",
        help="Drop database before creating (cleanup)"
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Complete reset: drop and recreate"
    )
    parser.add_argument(
        "--test-only",
        action="store_true",
        help="Only test connection"
    )
    
    args = parser.parse_args()
    
    print_header("SafeMarket PostgreSQL Setup")
    print(f"PostgreSQL Host: {PG_HOST}:{PG_PORT}")
    print(f"PostgreSQL User: {PG_USER}")
    print(f"Database Name: {DB_NAME}")
    print(f"Schema File: {SCHEMA_FILE}")
    
    if args.test_only:
        print_header("Testing Connection")
        if test_connection():
            print("\n✅ All systems ready!")
        else:
            print("\n❌ Connection test failed")
            sys.exit(1)
        return
    
    if args.reset or args.drop:
        print_header("Dropping Existing Database")
        confirm = input("Are you sure? (type 'yes' to confirm): ")
        if confirm.lower() != 'yes':
            print("Cancelled")
            return
        drop_database()
    
    print_header("Creating Database")
    create_database()
    
    print_header("Running SQL Schema")
    run_sql_script(SCHEMA_FILE)
    
    print_header("Verifying Setup")
    if test_connection():
        print_header("Setup Complete!")
        show_summary()
        
        print("\n✨ SafeMarket is ready to use!")
        print("\nNext steps:")
        print("  1. Update .env with PostgreSQL connection string:")
        print(f"     DATABASE_URL=postgresql://{PG_USER}:password@{PG_HOST}:{PG_PORT}/{DB_NAME}")
        print("  2. Start the API: python main.py")
        print("  3. Access docs: http://localhost:8000/docs")
    else:
        print_header("Setup verification failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
