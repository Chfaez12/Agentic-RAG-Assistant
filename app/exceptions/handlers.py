from fastapi import Request
from fastapi.responses import JSONResponse

async def value_error_handler(
    request: Request,
    exc: ValueError
):

    return JSONResponse(status_code=400,
        content={
            "success": False,
            "message": str(exc)
        }
    )