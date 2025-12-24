"""
Database Migration Script
Adds reset_token and reset_token_expires columns to users table
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import sqlite3
from datetime import datetime

def migrate_database():
    """Add reset token columns to users table"""
    
    db_path = "smartcapi.db"
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'reset_token' not in columns:
            print("Adding reset_token column...")
            cursor.execute("""
                ALTER TABLE users 
                ADD COLUMN reset_token VARCHAR(255)
            """)
            print("✅ reset_token column added successfully")
        else:
            print("ℹ️  reset_token column already exists")
        
        if 'reset_token_expires' not in columns:
            print("Adding reset_token_expires column...")
            cursor.execute("""
                ALTER TABLE users 
                ADD COLUMN reset_token_expires TIMESTAMP
            """)
            print("✅ reset_token_expires column added successfully")
        else:
            print("ℹ️  reset_token_expires column already exists")
        
        # Commit changes
        conn.commit()
        print("\n✅ Database migration completed successfully!")
        
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        return False
    
    finally:
        if conn:
            conn.close()
    
    return True

if __name__ == "__main__":
    print("=" * 50)
    print("SmartCAPI Database Migration")
    print("Adding password reset columns to users table")
    print("=" * 50)
    print()
    
    success = migrate_database()
    
    if success:
        print("\n" + "=" * 50)
        print("Migration completed! You can now use the")
        print("forget password and reset password features.")
        print("=" * 50)
    else:
        print("\n" + "=" * 50)
        print("Migration failed! Please check the error above.")
        print("=" * 50)
