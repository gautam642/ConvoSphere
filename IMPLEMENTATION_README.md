# ConvoSphere Implementation Tracker

This document tracks the implementation progress of the ConvoSphere project, following the architecture and plan outlined in `AGENT_ARCHITECTURE.md`.

## Prerequisites

To run this project, you need to have **MongoDB** and **Redis** servers running locally or accessible via the provided connection URIs.

### MongoDB Installation & Setup

*   **Windows**: Follow the official guide to [Install MongoDB Community Edition on Windows](https://www.mongodb.com/docs/manual/tutorial/install-mongodb-on-windows/).
*   **macOS**: The easiest way is using Homebrew:
    ```bash
    brew tap mongodb/brew
    brew install mongodb-community@6.0
    # To start MongoDB:
    brew services start mongodb-community@6.0
    ```
*   **Linux**: Refer to the official guides for your distribution: [Install MongoDB Community Edition on Linux](https://www.mongodb.com/docs/manual/administration/install-on-linux/).

### Redis Installation & Setup

*   **Windows**: Installing Redis natively on Windows is complex; using [WSL2 (Windows Subsystem for Linux 2)](https://docs.microsoft.com/en-us/windows/wsl/install) is highly recommended. Once WSL2 is set up, follow the Linux instructions.
*   **macOS**:
    ```bash
    brew install redis
    # To start Redis:
    brew services start redis
    ```
*   **Linux (e.g., Debian/Ubuntu)**:
    ```bash
    sudo apt update
    sudo apt install redis-server
    # Redis usually starts automatically after installation.
    ```
Ensure both MongoDB and Redis are running on their default ports (MongoDB: 27017, Redis: 6379) or update your `.env` file accordingly.

## Installation

1.  **Clone the Repository**:
    ```bash
    git clone https://github.com/your-username/ConvoSphere.git
    cd ConvoSphere
    ```

2.  **Create a Virtual Environment (Recommended)**:
    ```bash
    python -m venv venv
    # On Windows
    .\venv\Scripts\activate
    # On macOS/Linux
    source venv/bin/activate
    ```

3.  **Install Python Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Environment Variables Configuration**:
    Create a `.env` file in the project root based on `.env.example` and fill in your API keys and database connection details.

## Implementation Plan (Priority Order)

Based on section 13 of the architecture document.

1.  **[In Progress]** **DB + API skeleton**
    *   [x] Updated `requirements.txt` with `pymongo`, `redis`, `fastapi`, `uvicorn`, `motor`.
    *   [x] Created `api/` directory and `api/main.py` with a basic FastAPI app.
    *   [x] Created `db/` directory and `db/database.py` for MongoDB and Redis connection logic.
    *   [x] Updated `.env.example` with MongoDB and Redis connection string placeholders.
    *   [x] Created `api/schemas.py` for Pydantic models.
    *   [x] Created `db/models.py` for database interaction functions.
    *   [x] Add DB migrations / schema for `sessions`, `messages`, `alerts`, `osint`, `local_llm`, `gemini`. (Implemented via Pydantic schemas and MongoDB)
    *   [x] Implement `POST /api/sessions`.
    *   [x] Implement `GET /api/sessions/{id}`.
    *   [x] Implement `POST /api/sessions/{id}/send`.
    *   [x] Implement `POST /api/sessions/{id}/messages`.
    *   [x] Add a simple auth stub for `owner_id`. (Implicitly handled by requiring `owner_id` in `CreateSessionRequest` for now)

2.  **[In Progress]** **Background worker + job definitions**
    *   [x] Add Celery/RQ and Redis (or FastAPI background-tasks). (Using FastAPI BackgroundTasks for now)
    *   [x] Implement `osint_enrichment(session_id)` and placeholder return values.

3.  **[In Progress]** **Local LLM service wrapper**
    *   [x] Implement `services/local_llm_service.py` with placeholder `analyze()` and `suggest_first_message()` methods.
    *   [ ] Hook `local_llm_init` and `local_llm_analyze` worker tasks.

4.  **[Completed]** **Telegram router**
    *   [x] Refactor `telegram_talker.py` to be session-aware (Implemented as `services/telegram_router.py`).
    *   [x] Implement `send_message`.
    *   [x] Implement webhook receiver.

5.  **[In Progress]** **Streamlit UI**
    *   [x] Add "Start Conversation" form.
    *   [x] Wire to `POST /api/sessions` and show session page.

6.  **[In Progress]** **Gemini client**
    *   [x] Implement `gemini_client.py` structured JSON call (via `GeminiClient` and `run_gemini_call`).
    *   [x] Implement `gemini_call` worker that stores result.

7.  **[In Progress]** **Alerting**
    *   [x] Implement triggers in `local_llm_analyze`.
    *   [x] Implement `alert_dispatcher`.

8.  **[In Progress]** **Testing**
    *   [x] Add tests for endpoints and workers (using mocks for external APIs).

9.  **[In Progress]** **Documentation**
    *   [x] Update README with new endpoints and dev run steps.

## Usage

To run the FastAPI application:

1.  Ensure MongoDB and Redis servers are running.
2.  Activate your virtual environment (`.\venv\Scripts\activate` or `source venv/bin/activate`).
3.  Navigate to the project root and run:
    ```bash
    uvicorn api.main:app --reload
    ```
    This will start the FastAPI server, typically at `http://127.00.1:8000`. You can then access the interactive API documentation at `http://127.0.0.1:8000/docs`.

To run the Streamlit application:

1.  Ensure the FastAPI application is running.
2.  Activate your virtual environment.
3.  Navigate to the project root and run:
    ```bash
    streamlit run ui/streamlit_app.py
    ```
    This will open the Streamlit app in your web browser.

## Core Functionality Acceptance Criteria

Based on section 12 of the architecture document.

*   [ ] `POST /api/sessions` creates session, enqueues OSINT job, returns `session_id`.
*   [ ] OSINT fetchers run successfully and store `session.osint`.
*   [ ] `local_llm_init` produces a valid `short_context` and a first message suggestion saved to DB.
*   [ ] `POST /api/sessions/{id}/send` sends message to Telegram (mockable in tests) and appends message to DB.
*   [ ] Incoming Telegram messages are routed to session and appended.
*   [ ] Local LLM re-analyzes on each new message and updates `session.local_llm`.
*   [ ] `gemini_call` receives valid JSON and stores `response`.
*   [ ] Trigger thresholds create alerts and dispatch notifications.