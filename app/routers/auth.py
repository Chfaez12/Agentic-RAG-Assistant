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

@router.post("/register", response_model=UserResponse)
def register(user:UserCreate, db: Session = Depends(get_db)):
    hashed = hashed_password(user.password)
    new_user = User(username=user.username, email=user.email, hashed_password=hashed,role=user.role)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user

@router.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):

    user = db.query(User).filter(User.username == form_data.username).first()

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid Credentials"
        )

    if not verify_password(
        form_data.password,
        user.hashed_password
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid Credentials"
        )

    token = create_access_token(
        {
            "sub": user.username,
            "role": user.role
        }
    )

    return {
        "access_token": token,
        "token_type": "bearer"
    }


@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    return current_user
##

