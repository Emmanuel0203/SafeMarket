#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PostgreSQL Setup Script (Simple Alternative)
Using direct psql command instead of psycopg2
This avoids encoding issues on Windows
"""

import subprocess
import sys
import os
import getpass
from pathlib import Path

# Configuration
PG_USER = os.getenv("PG_USER", "postgres")
PG_HOST = os.getenv("PG_HOST", "localhost")
PG_PORT = os.getenv("PG_PORT", "5432")
PG_PASSWORD = os.getenv("PG_PASSWORD", None)
DB_NAME = "safemarket"

SCRIPT_DIR = Path(__file__).parent
SCHEMA_FILE = SCRIPT_DIR / "schema_improved.sql"

def run_command(cmd, shell=False):
    """Run command and return output"""
    try:
        result = subprocess.run(
            cmd,
            shell=shell,
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return 1, "", "Command timeout"
    except Exception as e:
        return 1, "", str(e)

def env_with_password():
    """Create environment with password"""
    env = os.environ.copy()
    if PG_PASSWORD:
        env['PGPASSWORD'] = PG_PASSWORD
    return env

def test_psql_available():
    """Check if psql is available"""
    returncode, stdout, stderr = run_command(["psql", "--version"])
    if returncode == 0:
        print(f"✓ PostgreSQL client found: {stdout.strip()}")
        return True
    else:
        print(f"❌ psql not found in PATH")
        print(f"   Please ensure PostgreSQL is installed and in PATH")
        return False

def test_connection():
    """Test PostgreSQL connection"""
    cmd = [
        "psql",
        f"-U{PG_USER}",
        f"-h{PG_HOST}",
        "-l"
    ]
    
    print(f"Testing connection to {PG_HOST}:{PG_PORT} as {PG_USER}...")
    returncode, stdout, stderr = run_command(cmd)
    
    if returncode == 0:
        print("✅ Connection successful!")
        return True
    else:
        print(f"❌ Connection failed:")
        print(f"   {stderr}")
        return False

def create_database():
    """Create database using psql"""
    print(f"Creating database '{DB_NAME}'...")
    
    # Check if exists
    cmd = [
        "psql",
        f"-U{PG_USER}",
        f"-h{PG_HOST}",
        "-lqt"
    ]
    
    returncode, stdout, stderr = run_command(cmd)
    
    if DB_NAME in stdout:
        print(f"✓ Database '{DB_NAME}' already exists")
        return True
    
    # Create it
    sql = f"CREATE DATABASE {DB_NAME} ENCODING 'UTF8';"
    cmd = [
        "psql",
        f"-U{PG_USER}",
        f"-h{PG_HOST}",
        "-d", "postgres",
        "-c", sql
    ]
    
    returncode, stdout, stderr = run_command(cmd)
    
    if returncode == 0:
        print(f"✅ Database created: {DB_NAME}")
        return True
    else:
        print(f"❌ Failed to create database:")
        print(f"   {stderr}")
        return False

def load_schema():
    """Load schema from SQL file"""
    if not SCHEMA_FILE.exists():
        print(f"❌ Schema file not found: {SCHEMA_FILE}")
        return False
    
    print(f"Loading schema from {SCHEMA_FILE.name}...")
    
    cmd = [
        "psql",
        f"-U{PG_USER}",
        f"-h{PG_HOST}",
        "-d", DB_NAME,
        "-f", str(SCHEMA_FILE),
        "-v", "ON_ERROR_STOP=1"  # Stop on first error
    ]
    
    returncode, stdout, stderr = run_command(cmd)
    
    if returncode == 0:
        # Count lines for feedback
        lines = stdout.count('\n')
        print(f"✅ Schema loaded successfully ({lines} lines)")
        return True
    else:
        # Show last part of error
        error_lines = stderr.split('\n')
        print(f"❌ Errors loading schema:")
        for line in error_lines[-10:]:
            if line.strip():
                print(f"   {line}")
        return False

def verify_data():
    """Verify data was loaded"""
    print("Verifying data...")
    
    tables_to_check = ['users', 'transactions', 'devices', 'sessions']
    
    for table in tables_to_check:
        cmd = [
            "psql",
            f"-U{PG_USER}",
            f"-h{PG_HOST}",
            "-d", DB_NAME,
            "-tc",
            f"SELECT COUNT(*) FROM {table};"
        ]
        
        returncode, stdout, stderr = run_command(cmd)
        
        if returncode == 0:
            count = stdout.strip()
            print(f"  {table}: {count} records")
        else:
            print(f"  {table}: ⚠️ Error checking")

def show_summary():
    """Show database summary"""
    print("\nDatabase Summary:")
    
    cmd = [
        "psql",
        f"-U{PG_USER}",
        f"-h{PG_HOST}",
        "-d", DB_NAME,
        "-tc",
        "SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename;"
    ]
    
    returncode, stdout, stderr = run_command(cmd)
    
    if returncode == 0:
        tables = [t.strip() for t in stdout.strip().split('\n') if t.strip()]
        print(f"  Tables created: {len(tables)}")
        print(f"  Tables: {', '.join(tables[:5])}...")

def main():
    """Main setup flow"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="SafeMarket PostgreSQL Setup (Simple)",
        epilog="This script uses psql directly to avoid encoding issues."
    )
    parser.add_argument("--test-only", action="store_true", help="Test connection only")
    parser.add_argument("--no-password", action="store_true", help="Don't prompt for password")
    args = parser.parse_args()
    
    print("\n" + "="*60)
    print("  SafeMarket PostgreSQL Setup (Simple Method)")
    print("="*60)
    print(f"Host: {PG_HOST}:{PG_PORT}")
    print(f"User: {PG_USER}")
    print(f"Database: {DB_NAME}")
    
    # Check psql available
    if not test_psql_available():
        sys.exit(1)
    
    # Prompt for password if not set
    global PG_PASSWORD
    if not PG_PASSWORD and not args.no_password:
        PG_PASSWORD = getpass.getpass("\n🔐 PostgreSQL Password: ")
    
    # Test connection
    if not test_connection():
        print("\n💡 Tips:")
        print("  - Ensure PostgreSQL is running")
        print("  - Check password is correct")
        print("  - Try: psql -U postgres -h localhost -l")
        sys.exit(1)
    
    if args.test_only:
        print("\n✅ Connection test passed!")
        sys.exit(0)
    
    # Create database
    if not create_database():
        sys.exit(1)
    
    # Load schema
    if not load_schema():
        print("\n💡 Tips:")
        print("  - Check that schema_improved.sql exists")
        print("  - Try loading manually: psql -U postgres -d safemarket -f schema_improved.sql")
        sys.exit(1)
    
    # Verify
    verify_data()
    show_summary()
    
    print("\n" + "="*60)
    print("  ✨ Setup Complete!")
    print("="*60)
    print("\nNext steps:")
    print(f"  1. Update .env: DATABASE_URL=postgresql://{PG_USER}:password@{PG_HOST}:{PG_PORT}/{DB_NAME}")
    print("  2. Run: python main.py")
    print("  3. Visit: http://localhost:8000/docs")

if __name__ == "__main__":
    main()
