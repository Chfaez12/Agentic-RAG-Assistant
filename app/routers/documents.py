from fastapi import (APIRouter,Depends,File,UploadFile)

from app.auth.dependencies import (get_current_user)

from app.rag.ingestion import (ingest_document)

from app.schemas.document import (DocumentUploadResponse)


router = APIRouter(
    prefix="/documents",
    tags=["Documents"]
)


@router.post("/upload",response_model=DocumentUploadResponse)

async def upload_document(
    file: UploadFile = File(...),
    current_user=Depends(
        get_current_user
    )
):

    result = await ingest_document(
        file=file,
        user_id=current_user.id
    )

    return {
        "message":
            "Document uploaded and indexed successfully.",

        **result
    }