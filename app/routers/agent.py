from fastapi import (APIRouter,Depends,HTTPException)

from app import config
from langchain_core.messages import (HumanMessage)

from sqlalchemy.orm import Session

from app.auth.dependencies import (get_current_user)
from app.dependencies.database import (get_db)

from app.agent.graph import (build_agent_graph)

from app.schemas.agent import (AgentChatRequest,AgentResponse,AgentHistoryResponse)

from app.guardrails.response_validation import (validate_agent_response)

from app.models.conversation import Conversation

router = APIRouter(
    prefix="/agent",
    tags=["DocOps Agent"]
)

def get_or_create_conversation(thread_id: str,user_id: int,db: Session):
    conversation = (
        db.query(Conversation)
        .filter(
            Conversation.thread_id == thread_id
        )
        .first()
    )
    
    if conversation:

        if conversation.user_id != user_id:

            raise HTTPException(
                status_code=403,
                detail=(
                    "You do not have access "
                    "to this conversation."
                )
            )

        return conversation

    conversation = Conversation(
        thread_id=thread_id,
        user_id=user_id
    )

    db.add(conversation)
    db.commit()
    db.refresh(conversation)

    return conversation

@router.post("/chat",response_model=AgentResponse)
def chat_with_agent(
    request: AgentChatRequest,

    current_user=Depends(
        get_current_user
    ),

    db: Session = Depends(
        get_db
    )
):

    conversation = get_or_create_conversation(
        thread_id=request.thread_id,
        user_id=current_user.id,
        db=db
    )

    graph = build_agent_graph(
        db=db
    )

    initial_state = {

        "messages": [
            HumanMessage(
                content=request.message
            )
        ],

        "user_id": current_user.id,

        "thread_id": request.thread_id,

        "plan": None,

        "remaining_tools": [],

        "tools_used": [],

        "tool_results": [],

        "reflection": None,

        "iteration_count": 0,

        "tool_calls": 0,

        "final_answer": None,

        "blocked": False
    }

    config = {
        "configurable": {
            "thread_id": request.thread_id
        }
    }

    final_state = graph.invoke(
        initial_state,
        config=config
    )

    response_data = {

        "thread_id":
            request.thread_id,

        "answer":
            final_state.get(
                "final_answer"
            )
            or
            "I could not generate an answer.",

        "tools_used":
            final_state.get(
                "tools_used",
                []
            ),

        "iterations":
            final_state.get(
                "iteration_count",
                0
            ),

        "tool_calls":
            final_state.get(
                "tool_calls",
                0
            ),

        "blocked":
            final_state.get(
                "blocked",
                False
            )
    }

    return validate_agent_response(
        response_data
    )

@router.get(
    "/history/{thread_id}",
    response_model=AgentHistoryResponse
)
def get_agent_history(
    thread_id: str,

    current_user=Depends(
        get_current_user
    ),

    db: Session = Depends(
        get_db
    )
):

    conversation = (
        db.query(Conversation)
        .filter(
            Conversation.thread_id == thread_id
        )
        .first()
    )

    if not conversation:

        raise HTTPException(
            status_code=404,
            detail="Conversation not found."
        )

    if conversation.user_id != current_user.id:

        raise HTTPException(
            status_code=403,
            detail=(
                "You do not have access "
                "to this conversation."
            )
        )

    graph = build_agent_graph(
        db=db
    )

    config = {
        "configurable": {
            "thread_id": thread_id
        }
    }

    snapshot = graph.get_state(
        config
    )

    messages = []

    if snapshot.values:

        for message in snapshot.values.get(
            "messages",
            []
        ):

            messages.append({
                "type": message.type,
                "content": message.content
            })

    return {
        "thread_id": thread_id,
        "messages": messages
    }