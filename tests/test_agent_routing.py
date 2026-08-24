from app.agent.graph import route_after_plan


def test_document_query_routes_to_retrieval():

    state = {
        "plan": "retrieval"
    }

    result = route_after_plan(state)

    assert result == "retrieval"


def test_database_query_routes_to_database():

    state = {
        "plan": "database"
    }

    result = route_after_plan(state)

    assert result == "database"


def test_general_query_routes_directly():

    state = {
        "plan": "direct"
    }

    result = route_after_plan(state)

    assert result == "direct"