"""
Script to create admin user for SmartCAPI
Run this script once to create the admin account
"""
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.database import SessionLocal
from app.db.models import User, UserRole
from app.core.security import get_password_hash

def create_admin_user():
    db = SessionLocal()
    
    try:
        # Check if admin already exists
        existing_admin = db.query(User).filter(User.username == "admincapi").first()
        
        if existing_admin:
            print("⚠️ Admin user 'admincapi' already exists. Updating password...")
            existing_admin.hashed_password = get_password_hash("supercapi")
            existing_admin.is_active = True
            existing_admin.role = UserRole.ADMIN
            db.commit()
            print("✅ Admin password reset to 'supercapi' successfully!")
            return
        
        # Create admin user
        admin_user = User(
            username="admincapi",
            email="admin@smartcapi.com",
            hashed_password=get_password_hash("supercapi"),
            full_name="Administrator",
            phone="000000000000",
            role=UserRole.ADMIN,
            is_active=True
        )
        
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        print("✅ Admin user created successfully!")
        print(f"   Username: admincapi")
        print(f"   Password: supercapi")
        print(f"   Role: {admin_user.role}")
        print(f"   Email: {admin_user.email}")
        
    except Exception as e:
        print(f"❌ Error creating admin user: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("Creating admin user for SmartCAPI...")
    create_admin_user()
