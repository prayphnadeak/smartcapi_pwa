from datetime import timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.security import verify_password, get_password_hash
from app.db.database import get_db
from app.db.models import User
from app.schemas.user import UserInDB

# Print to confirm reload
print("LOADING AUTH SERVICE (DEBUG MODE v4)")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

# Function to authenticate user
def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    user = db.query(User).filter(User.username == username).first()
    
    # Auto-create admin if not exists and credentials match
    if not user and username == "admincapi" and password == "supercapi":
        user = User(
            email="admin@smartcapi.com",
            username="admincapi",
            hashed_password=get_password_hash("supercapi"),
            full_name="Administrator",
            role="admin",
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

# Function to get current user from token
def get_current_user(
    db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> User:
    try:
        # DEBUG LOGGING
        print(f"DEBUG: Validating token: {token[:10]}...{token[-10:]}")
        
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        
        user_id = payload.get("sub")
        if user_id is None:
            print("DEBUG: No 'sub' in payload")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token invalid: missing user_id (sub)",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Robust conversion: handle both int and str
        user_id_int = None
        try:
            if isinstance(user_id, int):
                user_id_int = user_id
            else:
                user_id_int = int(user_id)
        except (ValueError, TypeError) as e:
            print(f"DEBUG: Failed to convert user_id '{user_id}' to int: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Token invalid: user_id format error ({user_id})",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
    except JWTError as e:
        print(f"DEBUG: JWTError: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token invalid: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"DEBUG: Unexpected error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token validation error: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = db.query(User).filter(User.id == user_id_int).first()
    if user is None:
        print(f"DEBUG: User with id {user_id_int} not found in DB")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"User not found (ID: {user_id_int})",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    return user

# Function to get current active user
def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

# Function to get current admin user
def get_current_admin_user(
    current_user: User = Depends(get_current_active_user),
) -> User:
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403, detail="The user doesn't have enough privileges"
        )
    return current_user