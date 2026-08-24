from dataclasses import dataclass

@dataclass
class GuardrailResult:

    allowed: bool

    reason: str | None = None


DESTRUCTIVE_OPERATIONS = [
    "DELETE",
    "UPDATE",
    "INSERT",
    "DROP",
    "ALTER",
    "TRUNCATE",
    "CREATE",
    "REPLACE"
]


def check_sql_guardrail(query: str) -> GuardrailResult:

    normalized_query = (
        query.upper()
    )

    for operation in DESTRUCTIVE_OPERATIONS:

        if operation in normalized_query:

            return GuardrailResult(
                allowed=False,
                reason=(
                    "This request was blocked because "
                    "the database agent only supports "
                    "read-only operations."
                )
            )

    return GuardrailResult(
        allowed=True
    )