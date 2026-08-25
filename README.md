# DocOps Agent API

A secure, multi-turn AI assistant for working with a user's own documents and application data. The agent plans a response, chooses between document retrieval and read-only database queries, and uses guardrails to keep tool usage bounded and safe.

## Overview

This project combines:

- FastAPI backend with JWT-based auth
- LangGraph agent orchestration
- Groq-hosted LLM inference
- Qdrant vector search for user-scoped document retrieval
- Response and tool safety checks to prevent unsafe SQL or excessive tool usage

The result is a DocOps-style assistant that can answer questions using either:

- uploaded documents that belong to the current user, or
- the user's own posts/comments in the app database, or
- both together when a question requires cross-referencing both data sources

## Architecture

```text
                                                                                      +-------------------+
                                                                                      |   Browser / App   |
                                                                                      |   (Frontend)      |
                                                                                      +---------+---------+
                                                                                                |
                                                                                                | HTTPS
                                                                                                v
                                                                                      +---------+---------+
                                                                                      |   FastAPI API     |
                                                                                      |  /auth            |
                                                                                      |  /users           |
                                                                                      |  /documents       |
                                                                                      |  /agent/chat      |
                                                                                      +---------+---------+
                                                                                                |
                                                                                                | JWT auth + request context
                                                                                                v
                                                                                      +---------+---------+
                                                                                      |  Agent Graph      |
                                                                                      |  (LangGraph)      |
                                                                                      |  plan -> route    |
                                                                                      |  retrieval ->     |
                                                                                      |  database ->      |
                                                                                      |  reflect -> final |
                                                                                      +---------+---------+
                                                                                                |
                       +------------------------------------------------+------------------------------------------------+
                       |                                                                                   |
                       |                                                                                   v
        +--------------+----------------+                 +------------------------------+----------------------+
        |       Tool layer            |                 |        Guardrails / Safety       |                |
        | - document_retrieval_tool() |                 | - SQL guardrail                     |                 |
        | - database_tool()           |                 | - tool_call_allowed()           |                |
        +--------------+----------------+               | - response validation           |                          |
                       |                                   +----------------------------------+                    |
                       v                                                                                                       |
         +----------------------------+                                                                                 |
         |  User-scoped document RAG |                                                                                 |
         |  Qdrant vector store      |                                                                                 |
         +-----+----------------------+
               |
               | similarity search on user documents
               v
         +----------------------------+
         |  SQlite / app database  |
         |  Post model, Comment model|
         +----------------------------+

                       ^
                       |
                       |
                       +-----------------------------+
                                             |
                                             v
                              +--------------------+
                              |  LLM (Groq / OpenAI) |
                              |  planner + reasoning |
                              +--------------------+
```

## How the agent decides

The workflow is implemented with a LangGraph state machine:

1. Planner decides whether the request needs:
   - direct answer only
   - document retrieval only
   - database access only
   - both document retrieval and database data
2. Retrieval node searches only the current authenticated user's uploaded documents.
3. Database node uses a restricted, typed read-only query model instead of arbitrary SQL.
4. Reflection node decides if more information is needed or if the response is ready.
5. Final node produces the answer and enforces validation.

## Core components

- app/main.py: FastAPI app setup, middleware, and router registration
- app/routers/agent.py: chat endpoint and conversation history endpoint
- app/agent/graph.py: agent workflow and routing
- app/agent/nodes.py: planner, retrieval, database, observe, reflection, and final response nodes
- app/agent/tools.py: constrained document and database tools
- app/rag/: document ingestion, chunking, embeddings, vector retrieval
- app/models/: domain models for users, posts, comments, documents, and conversations
- app/auth/: JWT and auth dependencies
- app/guardrails/: SQL guardrail, tool limit checks, and response validation

## Prerequisites

- Python 3.11+
- Docker and Docker Compose
- A Groq API key
- A database and Qdrant instance (or Docker-based services)

## Setup

### 1) Clone the repository

```bash
git clone https://github.com/Chfaez12/Agentic-RAG-Assistant
cd Agentic-RAG-Assistant
```

### 2) Create a .env file

Create a file named `.env` in the project root with values like:

```env
DATABASE_URL=sqlite:///./users.db
QDRANT_URL=http://localhost:6333
GROQ_API_KEY=your_groq_api_key_here
LLM_MODEL=openai/gpt-oss-120b
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
SECRET_KEY=
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### 3) Install Python dependencies

```bash
python -m venv .venv
. .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 4) Start supporting services with Docker

This project includes SQlite and Qdrant in docker-compose.yml.

```bash
docker compose up -d SQLite qdrant
```

If you want to run the full stack in Docker as well:

```bash
docker compose up --build
```

### 5) Run the API locally

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Then open:

- Swagger UI: http://localhost:8000/docs
- Health/root endpoint: http://localhost:8000/

## Quick API flow

### Authentication

Use the auth endpoints to register/login and receive a JWT token. The token is required for `/agent/chat` and `/agent/history/{thread_id}`.

### Agent chat endpoint

```http
POST /agent/chat
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

```json
{
  "message": "Summarize the key points from my uploaded onboarding documents.",
   "thread_id": "user-123-thread-1"
}
```

Returns:

- answer
- tools_used
- iterations
- tool_calls
- blocked

## Guardrails and security

This project intentionally restricts the agent to safe patterns:

- SQL queries are not arbitrary; the agent must choose from a fixed, allowlisted database operation schema.
- Database access is scoped to the authenticated user ID.
- Document search is limited to the current user’s uploaded documents.
- Tool calls are capped by MAX_TOOL_CALLS.
- Response validation checks the final answer structure before returning it.

## Example conversation transcripts

The examples below show three different tool paths the agent may choose based on the request.

### Example 1: Retrieval path only

This path is chosen when the user asks about uploaded documents and not the database.

```text
User: I uploaded three policy documents. What does the onboarding guide say about required training before day 1?

Agent: I will check your uploaded documents for onboarding and training requirements.

Tool: document_retrieval(query="onboarding guide required training before day 1", user_id=42)

Tool result: [Source: onboarding-guide.pdf]
The employee must complete workplace safety training and compliance modules before their first day.
The HR orientation checklist must be completed within 48 hours of start.

Agent: Based on your onboarding guide, employees need to complete workplace safety training and compliance modules before day 1, and the HR orientation checklist must be completed within 48 hours of the start date.
```

Chosen path: retrieval

### Example 2: Database path only

This path is chosen when the question is about the user’s own posts/comments in the app database.

```text
User: Show my last 3 posts and tell me how many comments are on the newest one.

Agent: I’ll look up your recent posts and count comments for the most recent post.

Tool: database(operation="list_my_posts", limit=3, post_id=null, user_id=42)

Tool result:
Post ID: 15
Title: Launch checklist
Content: We are finalizing the launch workflow...

Post ID: 12
Title: Team updates
Content: This week’s sprint notes...

Post ID: 9
Title: Q3 planning
Content: Goals and milestones...

Tool: database(operation="count_comments", post_id=15, limit=10, user_id=42)

Tool result: Post 'Launch checklist' has 7 comment(s).

Agent: Your last 3 posts are Launch checklist, Team updates, and Q3 planning. The newest one, Launch checklist, has 7 comments.
```

Chosen path: database

### Example 3: Retrieval + database path

This path is chosen when the user asks for a comparison that needs both document facts and database facts.

```text
User: Compare my onboarding policy document to my latest post and tell me whether our launch checklist matches the new compliance rule.

Agent: I need to check both your documents and your recent database data to compare the policy and the launch checklist.

Tool: document_retrieval(query="onboarding policy compliance rule launch checklist", user_id=42)

Tool result: [Source: compliance-policy.pdf]
All launch activities must include a final compliance review before release.

Tool: database(operation="get_my_post", post_id=15, limit=10, user_id=42)

Tool result:
Post ID: 15
Title: Launch checklist
Content: Final sign-off with engineering, legal review, and release approval before launch.

Agent: The compliance policy requires a final compliance review before release, and your latest launch checklist includes final sign-off plus legal review before launch. That is consistent with the policy, though the wording is slightly different.
```

Chosen path: both

## Repository structure

```text
.
├── app/
│   ├── agent/
│   │   ├── graph.py
│   │   ├── memory.py
│   │   ├── nodes.py
│   │   ├── prompts.py
│   │   ├── reflection.py
│   │   ├── state.py
│   │   └── tools.py
│   ├── auth/
│   ├── config.py
│   ├── core/
│   ├── database/
│   ├── dependencies/
│   ├── exceptions/
│   ├── guardrails/
│   ├── middleware/
│   ├── models/
│   ├── rag/
│   ├── routers/
│   ├── schemas/
│   ├── services/
│   └── utils/
├── tests/
├── uploads/
├── .gitignore
├── docker-compose.yml
├── Dockerfile
├── README.md
├── requirements.txt
└── .env
```

## Typical development workflow

- Add or update document ingestion under app/rag/
- Extend agent routing in app/agent/graph.py when new tools are needed
- Add new safe read-only operations in app/agent/tools.py
- Validate behavior with pytest

```bash
pytest -q
```

## Summary

DocOps Agent API is a practical example of a secure, user-scoped agentic RAG application: it ingests and retrieves user documents, reads only allowed records from a relational store, and uses a reasoning loop to decide how to answer complex questions safely.
