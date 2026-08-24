from app.config import settings


def tool_call_allowed(tool_calls: int) -> bool:

    return ( tool_calls <settings.MAX_TOOL_CALLS)