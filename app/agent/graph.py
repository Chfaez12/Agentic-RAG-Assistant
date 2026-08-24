from langgraph.graph import (
    StateGraph,
    START,
    END
)

from app.config import settings
from app.agent.state import AgentState
from app.agent.memory import get_checkpointer

from app.agent.nodes import (
    plan_node,
    retrieval_node,
    database_node,
    observe_node,
    direct_answer_node,
    final_answer_node
)

from app.agent.reflection import (
    reflection_node
)


def route_after_plan(state):

    if state["plan"] == "direct":
        return "direct"

    if not state["remaining_tools"]:
        return "final"

    next_tool = (
        state["remaining_tools"][0]
    )

    return next_tool


def route_after_reflection(state):

    if state.get("blocked"):
        return "final"

    if (state["iteration_count"] >= settings.MAX_ITERATIONS):
        return "final"

    if state["reflection"] == "continue":

        if state["remaining_tools"]:

            return (
                state["remaining_tools"][0]
            )

    return "final"


def build_agent_graph(db):

    workflow = StateGraph(AgentState)

    workflow.add_node("plan", plan_node)

    workflow.add_node(
        "retrieval",
        retrieval_node
    )

    workflow.add_node(
        "database",
        lambda state: database_node(
            state,
            db
        )
    )

    workflow.add_node(
        "observe",
        observe_node
    )

    workflow.add_node(
        "reflect",
        reflection_node
    )

    workflow.add_node(
        "direct",
        direct_answer_node
    )

    workflow.add_node(
        "final",
        final_answer_node
    )

    workflow.add_edge(
        START,
        "plan"
    )

    workflow.add_conditional_edges(
        "plan",
        route_after_plan,
        {
            "retrieval": "retrieval",
            "database": "database",
            "direct": "direct",
            "final": "final"
        }
    )

    workflow.add_edge(
        "retrieval",
        "observe"
    )

    workflow.add_edge(
        "database",
        "observe"
    )

    workflow.add_edge(
        "observe",
        "reflect"
    )

    workflow.add_conditional_edges(
        "reflect",
        route_after_reflection,
        {
            "retrieval": "retrieval",
            "database": "database",
            "final": "final"
        }
    )

    workflow.add_edge(
        "direct",
        END
    )

    workflow.add_edge(
        "final",
        END
    )


    checkpointer = get_checkpointer()

    return workflow.compile(
        checkpointer=checkpointer
    )