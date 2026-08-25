from unittest.mock import MagicMock, patch
from app.rag.retrieval import retrieve_user_documents


def test_user_cannot_access_another_users_documents():

    mock_vector_store = MagicMock()

    mock_vector_store.similarity_search.return_value = []

    with patch(
        "app.rag.retrieval.get_document_vector_store",
        return_value=mock_vector_store
    ):

        retrieve_user_documents(
            query="secret document",
            user_id=1,
            k=4
        )

    mock_vector_store.similarity_search.assert_called_once()

    call_kwargs = (
        mock_vector_store
        .similarity_search
        .call_args
        .kwargs
    )

    user_filter = call_kwargs["filter"]

    assert user_filter is not None

    assert user_filter.must

    condition = user_filter.must[0]

    assert condition.key == "metadata.user_id"

    assert condition.match.value == 1