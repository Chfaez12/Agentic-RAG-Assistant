from langchain_text_splitters import RecursiveCharacterTextSplitter


def chunk_text(text: str,chunk_size: int = 600,chunk_overlap: int = 100) -> list[str]:
    """
    Split document text into overlapping chunks.
    """

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len
    )

    chunks = splitter.split_text(text)

    return chunks