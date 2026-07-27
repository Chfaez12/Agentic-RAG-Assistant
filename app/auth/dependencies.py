from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from app.dependencies.database import get_db
from app.auth.oauth2 import oauth2_scheme
from app.auth.jwt_handler import verify_token
from app.models.user import User


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    payload = verify_token(token)

    username = payload.get("sub")

    user = db.query(User).filter(
        User.username == username
    ).first()

    if not user:
        raise HTTPException(401, "Invalid credentials")

    return user