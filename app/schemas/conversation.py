from datetime import datetime

from pydantic import BaseModel


class ConversationResponse(BaseModel):

    thread_id: str

    user_id: int

    created_at: datetime