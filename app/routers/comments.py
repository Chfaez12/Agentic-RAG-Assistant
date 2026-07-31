from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.dependencies.database import get_db
from app.auth.dependencies import get_current_user
from app.models.comment import Comment
from app.models.post import Post
from app.models.user import User
from app.schemas.comment import CommentCreate, CommentResponse

router = APIRouter(
    prefix="/comments",
    tags=["Comments"]
)


@router.post("/post/{post_id}", response_model=CommentResponse)
def create_comment(
    post_id: int,
    comment: CommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    post = db.query(Post).filter(Post.id == post_id).first()

    if not post:
        raise HTTPException(
            status_code=404,
            detail="Post not found"
        )

    new_comment = Comment(
        content=comment.content,
        user_id=current_user.id,
        post_id=post_id
    )

    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)

    return new_comment

@router.get("/", response_model=list[CommentResponse])
def get_comments(db: Session = Depends(get_db)):
    return db.query(Comment).all()


@router.get("/{comment_id}", response_model=CommentResponse)
def get_comment(
    comment_id: int,
    db: Session = Depends(get_db)
):

    comment = db.query(Comment).filter(
        Comment.id == comment_id
    ).first()

    if not comment:
        raise HTTPException(
            status_code=404,
            detail="Comment not found"
        )

    return comment

@router.put("/{comment_id}", response_model=CommentResponse)
def update_comment(
    comment_id: int,
    comment: CommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    existing_comment = db.query(Comment).filter(
        Comment.id == comment_id
    ).first()

    if not existing_comment:
        raise HTTPException(
            status_code=404,
            detail="Comment not found"
        )

    if existing_comment.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Permission denied"
        )

    existing_comment.content = comment.content

    db.commit()
    db.refresh(existing_comment)

    return existing_comment


@router.delete("/{comment_id}")
def delete_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    comment = db.query(Comment).filter(
        Comment.id == comment_id
    ).first()

    if not comment:
        raise HTTPException(
            status_code=404,
            detail="Comment not found"
        )

    if current_user.role != "admin" and comment.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Permission denied"
        )

    db.delete(comment)
    db.commit()

    return {
        "message": "Comment deleted successfully"
    }