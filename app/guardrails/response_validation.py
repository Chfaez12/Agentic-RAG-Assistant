from app.schemas.agent import (AgentResponse)


def validate_agent_response(response: dict) -> AgentResponse:

    """
    Validate the final response before
    returning it from the API.
    """

    return AgentResponse.model_validate(response)