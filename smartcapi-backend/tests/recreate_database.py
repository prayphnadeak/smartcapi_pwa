"""
Script to recreate the database with updated schema
This will delete the existing database and create a new one with cascade delete rules
"""
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.database import engine
from app.db.models import Base

def recreate_database():
    db_path = "smartcapi.db"
    
    # Delete existing database
    if os.path.exists(db_path):
        print(f"Deleting existing database: {db_path}")
        os.remove(db_path)
        print("Database deleted successfully")
    
    # Create new database with updated schema
    print("Creating new database with updated schema...")
    Base.metadata.create_all(bind=engine)
    print("Database created successfully with CASCADE delete rules")
    print("\nRemember to run create_admin.py to create the admin user!")

if __name__ == "__main__":
    print("=" * 60)
    print("Database Recreation Script")
    print("=" * 60)
    print("\nWARNING: This will delete all existing data!")
    
    confirm = input("\nAre you sure you want to continue? (yes/no): ")
    
    if confirm.lower() == "yes":
        recreate_database()
    else:
        print("Operation cancelled")
