import uuid
from pathlib import Path

from fastapi import UploadFile, HTTPException
from langchain_core.documents import Document
from pypdf import PdfReader

from app.rag.chunking import chunk_text
from app.rag.vector_store import (
    get_document_vector_store
)


UPLOAD_DIRECTORY = Path("uploads")


def extract_text(
    file_path: Path,
    filename: str
) -> str:

    extension = Path(filename).suffix.lower()

    if extension == ".txt":

        return file_path.read_text(
            encoding="utf-8"
        )

    if extension == ".pdf":

        reader = PdfReader(
            str(file_path)
        )

        text = ""

        for page in reader.pages:

            page_text = page.extract_text()

            if page_text:
                text += page_text + "\n"

        return text

    raise HTTPException(
        status_code=400,
        detail="Only PDF and TXT documents are supported."
    )


async def ingest_document(
    file: UploadFile,
    user_id: int
):

    allowed_extensions = {
        ".pdf",
        ".txt"
    }

    extension = Path(
        file.filename
    ).suffix.lower()

    if extension not in allowed_extensions:

        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported file type. "
                "Only PDF and TXT files are allowed."
            )
        )

    UPLOAD_DIRECTORY.mkdir(
        exist_ok=True
    )

    document_id = str(
        uuid.uuid4()
    )

    file_path = (
        UPLOAD_DIRECTORY /
        f"{document_id}{extension}"
    )

    content = await file.read()

    with open(
        file_path,
        "wb"
    ) as buffer:

        buffer.write(content)

    text = extract_text(
        file_path=file_path,
        filename=file.filename
    )

    if not text.strip():

        raise HTTPException(
            status_code=400,
            detail="No text could be extracted from the document."
        )

    chunks = chunk_text(text)

    documents = []

    for index, chunk in enumerate(chunks):

        documents.append(

            Document(
                page_content=chunk,
                metadata={
                    "document_id": document_id,
                    "user_id": user_id,
                    "filename": file.filename,
                    "chunk_index": index
                }
            )
        )

    vector_store = (
        get_document_vector_store()
    )

    vector_store.add_documents(
        documents
    )

    return {
        "document_id": document_id,
        "filename": file.filename,
        "chunks_created": len(chunks)
    }