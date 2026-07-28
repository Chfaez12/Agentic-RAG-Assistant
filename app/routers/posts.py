from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.dependencies.database import get_db
from app.auth.dependencies import get_current_user
from app.models.post import Post
from app.models.user import User
from app.schemas.post import PostCreate, PostResponse

router = APIRouter(
    prefix="/posts",
    tags=["Posts"]
)


@router.post("/", response_model=PostResponse)
def create_post(post: PostCreate,db: Session = Depends(get_db),current_user: User = Depends(get_current_user)):
    new_post = Post(
        title=post.title,
        content=post.content,
        owner_id=current_user.id
    )

    db.add(new_post)
    db.commit()
    db.refresh(new_post)

    return new_post


@router.get("/", response_model=list[PostResponse])
def get_posts(db: Session = Depends(get_db)):
    return db.query(Post).all()


@router.get("/{post_id}", response_model=PostResponse)
def get_post(post_id: int, db: Session = Depends(get_db)):
    post = db.query(Post).filter(Post.id == post_id).first()

    if not post:
        raise HTTPException(404, "Post not found")

    return post


@router.put("/{post_id}", response_model=PostResponse)
def update_post(
    post_id: int,
    post: PostCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    existing_post = db.query(Post).filter(Post.id == post_id).first()

    if not existing_post:
        raise HTTPException(404, "Post not found")

    if existing_post.owner_id != current_user.id:
        raise HTTPException(
            status_code=401,
            detail="Only owner can update this post"
        )

    existing_post.title = post.title
    existing_post.content = post.content

    db.commit()
    db.refresh(existing_post)

    return existing_post


@router.delete("/{post_id}")
def delete_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    post = db.query(Post).filter(Post.id == post_id).first()

    if not post:
        raise HTTPException(404, "Post not found")

    if current_user.role != "admin" and post.owner_id != current_user.id:
        raise HTTPException(
            status_code=401,
            detail="Unauthorize: You cannot delete this post"
        )

    db.delete(post)
    db.commit()

    return {"message": "Post deleted successfully"}