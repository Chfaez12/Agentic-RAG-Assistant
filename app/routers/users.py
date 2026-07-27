from sqlalchemy.orm import Session
from fastapi import Depends
from app.dependencies.database import get_db
from app.models import user
from app.models.user import User
from fastapi import APIRouter,HTTPException
from app.schemas.user import UserResponse, UserCreate
from app.auth.hashing import hashed_password,verify_password
from fastapi.security import OAuth2PasswordRequestForm
from app.auth.jwt_handler import create_access_token
from app.auth.dependencies import get_current_user

router = APIRouter(
    prefix="/users",
    tags=["users"]
)


@router.get("/")
def get_users(db: Session = Depends(get_db)):
    users = db.query(User).all()

    return {
        "database_connected": True,
        "total_users": len(users),
        "users": users
    }

@router.post("/", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    hashed_pwd = hashed_password(user.password)
    new_user = User(username=user.username, email=user.email,hashed_password=hashed_pwd)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.put("/{user_id}", response_model=UserResponse)
def update_user(user_id: int, user: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.id == user_id).first()
    if not existing_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    existing_user.username = user.username
    existing_user.email = user.email
    existing_user.hashed_password = hashed_password(user.password)

    db.commit()
    db.refresh(existing_user)
    return user

@router.delete("/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id==user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="not found")

    db.delete(user)
    db.commit()
    return ("User deleted")
















