from app.database import Base, engine

from app.models.user import User
from app.models.post import Post
from app.models.comment import Comment
from app.models.conversation import Conversation


def init_db():
    Base.metadata.create_all(
        bind=engine
    )