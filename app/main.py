from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.models import User, Post, Comment
from app.routers.users import router as user_router
from app.routers.auth import router as auth_router
from app.middleware.logger import log_requests
from app.routers.posts import router as postrouter
from app.routers.comments import router as commentrouter

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Project 2 API",
    version="1.0.0"
)

app.include_router(auth_router)
app.include_router(user_router)

app.include_router(postrouter)
app.include_router(commentrouter)

app.middleware("http")(log_requests)


app.add_middleware(

    CORSMiddleware,

    allow_origins=[
        "http://localhost:3000"
    ],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"]
)

from app.exceptions.handlers import value_error_handler

app.add_exception_handler(
    ValueError,
    value_error_handler
)