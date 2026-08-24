from typing import Literal

from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.models.post import Post
from app.models.comment import Comment

from app.rag.retrieval import retrieve_user_documents


class DatabaseQuery(BaseModel):
    """
    Strict schema for all database operations.

    The agent cannot execute arbitrary SQL.
    It can only select one of these predefined
    read-only operations.
    """

    operation: Literal[
        "list_my_posts",
        "get_my_post",
        "list_comments_for_post",
        "count_comments",
        "list_my_comments"
    ]

    post_id: int | None = None

    limit: int = Field(
        default=10,
        ge=1,
        le=50
    )


def document_retrieval_tool(
    query: str,
    user_id: int
) -> str:
    """
    Retrieve documents belonging ONLY to the
    authenticated user.
    """

    documents = retrieve_user_documents(
        query=query,
        user_id=user_id
    )

    if not documents:
        return (
            "No relevant information was found "
            "in your uploaded documents."
        )

    results = []

    for document in documents:
        filename = document.metadata.get(
            "filename",
            "Unknown document"
        )

        results.append(
            f"[Source: {filename}]\n"
            f"{document.page_content}"
        )

    return "\n\n".join(results)


def database_tool(
    request: DatabaseQuery,
    user_id: int,
    db: Session
) -> str:
    """
    Strict read-only database tool.

    Every operation is scoped using the
    authenticated user's ID.
    """

    if request.operation == "list_my_posts":

        posts = (
            db.query(Post)
            .filter(Post.owner_id == user_id)
            .limit(request.limit)
            .all()
        )

        if not posts:
            return "You have no posts."

        return "\n".join(
            [
                (
                    f"Post ID: {post.id}\n"
                    f"Title: {post.title}\n"
                    f"Content: {post.content}"
                )
                for post in posts
            ]
        )

    if request.operation == "get_my_post":

        if request.post_id is None:
            return (
                "A post_id is required "
                "for this operation."
            )

        post = (
            db.query(Post)
            .filter(
                Post.id == request.post_id,
                Post.owner_id == user_id
            )
            .first()
        )

        if not post:
            return (
                "Post not found or you do not "
                "have permission to access it."
            )

        return (
            f"Post ID: {post.id}\n"
            f"Title: {post.title}\n"
            f"Content: {post.content}"
        )

    if request.operation == "list_comments_for_post":

        if request.post_id is None:
            return "A post_id is required."

        post = (
            db.query(Post)
            .filter(
                Post.id == request.post_id,
                Post.owner_id == user_id
            )
            .first()
        )

        if not post:
            return (
                "Post not found or you do not "
                "have permission to access it."
            )

        comments = (
            db.query(Comment)
            .filter(
                Comment.post_id == request.post_id
            )
            .limit(request.limit)
            .all()
        )

        if not comments:
            return (
                "No comments were found "
                "for this post."
            )

        return "\n".join(
            [
                (
                    f"Comment ID: {comment.id}\n"
                    f"Content: {comment.content}\n"
                    f"Author User ID: {comment.user_id}"
                )
                for comment in comments
            ]
        )

    if request.operation == "count_comments":

        if request.post_id is None:
            return "A post_id is required."

        post = (
            db.query(Post)
            .filter(
                Post.id == request.post_id,
                Post.owner_id == user_id
            )
            .first()
        )

        if not post:
            return (
                "Post not found or you do not "
                "have permission to access it."
            )

        count = (
            db.query(Comment)
            .filter(
                Comment.post_id == request.post_id
            )
            .count()
        )

        return (
            f"Post '{post.title}' has "
            f"{count} comment(s)."
        )


    if request.operation == "list_my_comments":

        comments = (
            db.query(Comment)
            .filter(
                Comment.user_id == user_id
            )
            .limit(request.limit)
            .all()
        )

        if not comments:
            return "You have not made any comments."

        return "\n".join(
            [
                (
                    f"Comment ID: {comment.id}\n"
                    f"Post ID: {comment.post_id}\n"
                    f"Content: {comment.content}"
                )
                for comment in comments
            ]
        )

    return "Unsupported database operation."