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
from app.auth.roles import require_admin

router = APIRouter(
    prefix="/users",
    tags=["users"]
)

@router.get("/", response_model=list[UserResponse])
def get_users(
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    users = db.query(User).all()
    return users

@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    user: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    existing_user = db.query(User).filter(User.id == user_id).first()

    if not existing_user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    if current_user.role != "admin" and current_user.id != user_id:
        raise HTTPException(
            status_code=403,
            detail="Permission denied"
        )

    existing_user.username = user.username
    existing_user.email = user.email
    existing_user.hashed_password = hashed_password(user.password)

    if current_user.role == "admin":
        existing_user.role = user.role

    db.commit()
    db.refresh(existing_user)

    return existing_user

@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    
    if current_user.role != "admin" and current_user.id != user_id:
        raise HTTPException(
            status_code=403,
            detail="Permission denied"
        )

    db.delete(user)
    db.commit()

    return {
        "message": "User deleted successfully"
    }