import time
from fastapi import Request

async def log_requests(request:Request,call_next):
    start_time = time.time()

    print(f"Request: {request.method} {request.url}")

    response = await call_next(request)

    process_time = time.time() - start_time

    print(f"Completed in {process_time:.4f} sec")

    return response
