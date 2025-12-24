#!/usr/bin/env python3
"""
verify_and_create_admin.py
Script untuk verifikasi database dan membuat admin user untuk SmartCAPI PWA
Credentials: admincapi / supercapi
"""

import sys
import os
from pathlib import Path

# Add app directory to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

try:
    from app.db.database import SessionLocal, engine
    from app.db.models import Base, User
    from app.core.security import get_password_hash
    print("✓ Modules imported successfully")
except ImportError as e:
    print(f"✗ Import error: {e}")
    print("\nPastikan script dijalankan dari directory backend:")
    print("  cd /var/www/smartcapi/backend")
    print("  source .venv/bin/activate")
    print("  python verify_and_create_admin.py")
    sys.exit(1)

def verify_database():
    """Verify database connection and tables"""
    print("\n>>> Verifying database...")
    
    try:
        # Create tables if not exist
        Base.metadata.create_all(bind=engine)
        print("✓ Database tables verified/created")
        
        # Test connection
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        print("✓ Database connection OK")
        return True
        
    except Exception as e:
        print(f"✗ Database error: {e}")
        return False

def list_existing_users():
    """List all existing users in database"""
    print("\n>>> Listing existing users...")
    
    db = SessionLocal()
    try:
        users = db.query(User).all()
        
        if not users:
            print("  No users found in database")
            return []
        
        print(f"  Found {len(users)} user(s):")
        for user in users:
            print(f"    - {user.username} ({user.role}) - {user.email}")
            if user.username == "admincapi":
                print(f"      [This is the admin user]")
        
        return users
        
    except Exception as e:
        print(f"✗ Error listing users: {e}")
        return []
    finally:
        db.close()

def create_admin_user():
    """Create admin user with SmartCAPI default credentials"""
    print("\n>>> Creating admin user...")
    
    db = SessionLocal()
    
    try:
        # Check if admin already exists
        existing_admin = db.query(User).filter(User.username == "admincapi").first()
        
        if existing_admin:
            print("✓ Admin user 'admincapi' already exists")
            print(f"  ID: {existing_admin.id}")
            print(f"  Email: {existing_admin.email}")
            print(f"  Role: {existing_admin.role}")
            print(f"  Active: {existing_admin.is_active}")
            
            # Verify password
            print("\n  Testing password...")
            from app.core.security import verify_password
            if verify_password("supercapi", existing_admin.hashed_password):
                print("  ✓ Password 'supercapi' is correct")
            else:
                print("  ✗ Password mismatch! Updating to 'supercapi'...")
                existing_admin.hashed_password = get_password_hash("supercapi")
                db.commit()
                print("  ✓ Password updated")
            
            return existing_admin
        
        # Create new admin user
        print("  Creating new admin user...")
        admin_user = User(
            username="admincapi",
            email="admin@smartcapi.id",
            hashed_password=get_password_hash("supercapi"),
            full_name="Administrator",
            role="admin",
            is_active=True
        )
        
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        print("✓ Admin user created successfully!")
        print(f"  ID: {admin_user.id}")
        print(f"  Username: admincapi")
        print(f"  Password: supercapi")
        print(f"  Email: {admin_user.email}")
        print(f"  Role: {admin_user.role}")
        
        return admin_user
        
    except Exception as e:
        print(f"✗ Error creating admin user: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return None
    finally:
        db.close()

def main():
    print("=" * 50)
    print("SmartCAPI PWA - Database Verification")
    print("=" * 50)
    
    # 1. Verify database
    if not verify_database():
        print("\n✗ Database verification failed!")
        sys.exit(1)
    
    # 2. List existing users
    existing_users = list_existing_users()
    
    # 3. Create/verify admin user
    admin_user = create_admin_user()
    
    if admin_user:
        print("\n" + "=" * 50)
        print("SUCCESS!")
        print("=" * 50)
        print("\nYou can now login with:")
        print("  Username: admincapi")
        print("  Password: supercapi")
        print("  Role: admin")
        print("\n⚠️  IMPORTANT: Change password after first login!")
        print("=" * 50)
    else:
        print("\n" + "=" * 50)
        print("FAILED!")
        print("=" * 50)
        print("\nAdmin user creation failed. Check errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
