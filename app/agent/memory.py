import sqlite3

from langgraph.checkpoint.sqlite import SqliteSaver


CHECKPOINT_DB = "agent_checkpoints.db"


_connection = sqlite3.connect(
    CHECKPOINT_DB,
    check_same_thread=False
)


_checkpointer = SqliteSaver(
    _connection
)


def get_checkpointer():

    return _checkpointer