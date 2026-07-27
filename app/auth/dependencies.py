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

    if payload is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid Token"
        )

    username = payload.get("sub")

    user = db.query(User).filter(
        User.username == username
    ).first()

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="User not found"
        )

    return user