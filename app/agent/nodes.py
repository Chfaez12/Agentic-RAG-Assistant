import json

from langchain_core.messages import (
    HumanMessage,
    AIMessage
)
from langchain_groq import ChatGroq

from langchain_openai import ChatOpenAI
from sqlalchemy.orm import Session

from app.config import settings

from app.agent.prompts import (
    PLANNER_PROMPT,
    DATABASE_PLANNER_PROMPT,
    FINAL_RESPONSE_PROMPT
)

from app.agent.tools import (
    DatabaseQuery,
    database_tool,
    document_retrieval_tool
)

from app.guardrails.sql_guardrail import (
    check_sql_guardrail
)

from app.guardrails.tool_limit import (
    tool_call_allowed
)


llm = ChatGroq(
    model=settings.LLM_MODEL,
    api_key=settings.GROQ_API_KEY
)


def plan_node(state):
    """
    Decide which tools are required.
    """

    user_message = (
        state["messages"][-1].content
    )

    prompt = f"""
{PLANNER_PROMPT}

User request:

{user_message}
"""

    response = llm.invoke(prompt)

    plan = (
        response.content
        .strip()
        .lower()
    )

    valid_plans = {
        "retrieval",
        "database",
        "both",
        "direct"
    }

    if plan not in valid_plans:
        plan = "direct"

    if plan == "retrieval":
        remaining_tools = [
            "retrieval"
        ]

    elif plan == "database":
        remaining_tools = [
            "database"
        ]

    elif plan == "both":
        remaining_tools = [
            "retrieval",
            "database"
        ]

    else:
        remaining_tools = []

    return {
        "plan": plan,
        "remaining_tools": remaining_tools,
        "tools_used": [],
        "tool_results": [],
        "reflection": None
    }


def retrieval_node(state):
    """
    Search ONLY the authenticated user's documents.
    """

    if not tool_call_allowed(
        state["tool_calls"]
    ):
        return {
            "blocked": True,
            "final_answer": (
                "The maximum allowed tool calls "
                "for this request has been reached."
            )
        }

    user_message = (
        state["messages"][-1].content
    )

    result = document_retrieval_tool(
        query=user_message,
        user_id=state["user_id"]
    )

    remaining_tools = [
        tool
        for tool in state["remaining_tools"]
        if tool != "retrieval"
    ]

    return {
        "remaining_tools": remaining_tools,

        "tools_used": [
            *state["tools_used"],
            "document_retrieval"
        ],

        "tool_results": [
            *state["tool_results"],
            result
        ],

        "tool_calls":
            state["tool_calls"] + 1
    }



def database_node(
    state,
    db: Session
):
    """
    Run a strictly typed read-only DB query.
    """

    if not tool_call_allowed(
        state["tool_calls"]
    ):
        return {
            "blocked": True,
            "final_answer": (
                "The maximum allowed tool calls "
                "for this request has been reached."
            )
        }

    user_message = (
        state["messages"][-1].content
    )

    
    guardrail = check_sql_guardrail(
        user_message
    )

    if not guardrail.allowed:
        return {
            "blocked": True,
            "final_answer": guardrail.reason
        }

    prompt = f"""
{DATABASE_PLANNER_PROMPT}

User request:

{user_message}
"""

    response = llm.invoke(prompt)

    try:

        content = (
            response.content
            .replace("```json", "")
            .replace("```", "")
            .strip()
        )

        data = json.loads(content)

        database_request = DatabaseQuery(
            **data
        )

    except Exception:

        return {
            "blocked": True,
            "final_answer": (
                "I could not safely convert your request "
                "into a supported read-only database query."
            )
        }

    result = database_tool(
        request=database_request,
        user_id=state["user_id"],
        db=db
    )

    remaining_tools = [
        tool
        for tool in state["remaining_tools"]
        if tool != "database"
    ]

    return {
        "remaining_tools": remaining_tools,

        "tools_used": [
            *state["tools_used"],
            "database"
        ],

        "tool_results": [
            *state["tool_results"],
            result
        ],

        "tool_calls":
            state["tool_calls"] + 1
    }


def observe_node(state):
    """
    Record that one reasoning cycle has completed.
    """

    return {
        "iteration_count":
            state["iteration_count"] + 1
    }


def direct_answer_node(state):
    """
    Answer a general question without tools.
    """

    user_message = (
        state["messages"][-1].content
    )

    response = llm.invoke(
        [
            HumanMessage(
                content=user_message
            )
        ]
    )

    return {
        "final_answer": response.content,

        "messages": [
            AIMessage(
                content=response.content
            )
        ]
    }

def final_answer_node(state):
    """
    Generate the final answer using the tool results.
    """

    if state.get("blocked"):

        answer = (
            state.get("final_answer")
            or
            "The request was blocked."
        )

        return {
            "final_answer": answer,

            "messages": [
                AIMessage(
                    content=answer
                )
            ]
        }

    user_message = (
        state["messages"][-1].content
    )

    tool_results = (
        state.get(
            "tool_results",
            []
        )
    )

    if not tool_results:

        return {
            "final_answer":
                "No information was found.",

            "messages": [
                AIMessage(
                    content="No information was found."
                )
            ]
        }

    prompt = f"""
{FINAL_RESPONSE_PROMPT}

User question:

{user_message}

Tool results:

{tool_results}
"""

    response = llm.invoke(prompt)

    return {
        "final_answer":
            response.content,

        "messages": [
            AIMessage(
                content=response.content
            )
        ]
    }