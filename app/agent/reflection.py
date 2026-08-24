from langchain_openai import ChatOpenAI

from app.config import settings
from app.agent.prompts import REFLECTION_PROMPT

from langchain_groq import ChatGroq

from langchain_groq import ChatGroq

llm = ChatGroq(
    model=settings.LLM_MODEL,
    api_key=settings.GROQ_API_KEY
)


def reflection_node(state):
    """
    Decide whether the agent has enough information
    to generate the final answer.
    """

    if state.get("blocked"):
        return {
            "reflection": "answer"
        }

    if state["iteration_count"] >= settings.MAX_ITERATIONS:
        return {
            "reflection": "answer"
        }

    tool_results = state.get(
        "tool_results",
        []
    )

    if not tool_results:
        return {
            "reflection": "answer"
        }

    user_message = (
        state["messages"][-1].content
    )

    prompt = f"""
{REFLECTION_PROMPT}

User question:

{user_message}

Current plan:

{state.get("plan")}

Tools used:

{state.get("tools_used")}

Tool results:

{tool_results}
"""

    response = llm.invoke(prompt)

    decision = (
        response.content
        .strip()
        .lower()
    )

    if decision not in [
        "answer",
        "continue"
    ]:
        decision = "answer"

    return {
        "reflection": decision
    }