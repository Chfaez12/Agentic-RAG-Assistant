from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

from langchain_qdrant import QdrantVectorStore

from app.config import settings
from app.rag.embeddings import get_embeddings


DOCUMENT_COLLECTION = "user_documents"

SUMMARY_COLLECTION = "conversation_summaries"


def get_qdrant_client():

    return QdrantClient(
        url=settings.QDRANT_URL
    )


def collection_exists(
    client,
    collection_name: str
) -> bool:

    collections = client.get_collections()

    existing_collections = [
        collection.name
        for collection in collections.collections
    ]

    return collection_name in existing_collections


def create_collection(
    client,
    collection_name: str
):

    embeddings = get_embeddings()

    embedding_dimension = len(
        embeddings.embed_query("dimension check")
    )

    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(
            size=embedding_dimension,
            distance=Distance.COSINE
        )
    )


def initialize_vector_store():

    client = get_qdrant_client()

    if not collection_exists(
        client,
        DOCUMENT_COLLECTION
    ):
        create_collection(
            client,
            DOCUMENT_COLLECTION
        )

    if not collection_exists(
        client,
        SUMMARY_COLLECTION
    ):
        create_collection(
            client,
            SUMMARY_COLLECTION
        )


def get_document_vector_store():

    initialize_vector_store()

    client = get_qdrant_client()

    embeddings = get_embeddings()

    return QdrantVectorStore(
        client=client,
        collection_name=DOCUMENT_COLLECTION,
        embedding=embeddings
    )


def get_summary_vector_store():

    initialize_vector_store()

    client = get_qdrant_client()

    embeddings = get_embeddings()

    return QdrantVectorStore(
        client=client,
        collection_name=SUMMARY_COLLECTION,
        embedding=embeddings
    )