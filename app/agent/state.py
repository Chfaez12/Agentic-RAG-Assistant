from typing import Annotated, TypedDict

from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """
    Shared state for the complete LangGraph workflow.
    """

    messages: Annotated[
        list,
        add_messages
    ]

    user_id: int

    thread_id: str

    plan: str | None

    remaining_tools: list[str]

    tools_used: list[str]

    tool_results: list[str]

    reflection: str | None

    iteration_count: int

    tool_calls: int

    final_answer: str | None

    blocked: bool