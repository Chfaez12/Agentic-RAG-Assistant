from pydantic import (
    BaseModel,
    Field
)


class AgentChatRequest(
    BaseModel
):

    message: str = Field(
        ...,
        min_length=1,
        description="Message for the DocOps Agent"
    )

    thread_id: str = Field(
        ...,
        min_length=1,
        description=(
            "Persistent conversation thread ID"
        )
    )


class AgentResponse(
    BaseModel
):

    thread_id: str

    answer: str

    tools_used: list[str]

    iterations: int

    tool_calls: int

    blocked: bool = False


class AgentHistoryResponse(
    BaseModel
):

    thread_id: str

    messages: list[dict]