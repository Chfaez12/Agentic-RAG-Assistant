from app.guardrails.sql_guardrail import (check_sql_guardrail)


def test_delete_is_blocked():

    result = check_sql_guardrail(
        "DELETE FROM posts"
    )

    assert result.allowed is False

    assert "read-only" in result.reason.lower()


def test_update_is_blocked():

    result = check_sql_guardrail(
        "UPDATE posts SET title='test'"
    )

    assert result.allowed is False


def test_select_is_allowed():

    result = check_sql_guardrail(
        "SELECT * FROM posts"
    )

    assert result.allowed is True