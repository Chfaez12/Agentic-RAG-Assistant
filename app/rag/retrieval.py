from qdrant_client.models import Filter, FieldCondition, MatchValue

from app.rag.vector_store import (
    get_document_vector_store
)


def retrieve_user_documents(
    query: str,
    user_id: int,
    k: int = 4
):
    """
    Search ONLY documents belonging to the authenticated user.
    """

    vector_store = get_document_vector_store()

    user_filter = Filter(
        must=[
            FieldCondition(
                key="metadata.user_id",
                match=MatchValue(value=user_id)
            )
        ]
    )

    results = vector_store.similarity_search(
        query=query,
        k=k,
        filter=user_filter
    )

    return results