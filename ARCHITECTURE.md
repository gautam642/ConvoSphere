# ConvoSphere Application Architecture (with Gemini Flow & OSINT)

This document provides a detailed diagram of the application's architecture and data flow, including the OSINT enrichment phase and the planned integration of the Gemini API.

## Component Diagram & Data Flow

This diagram illustrates the complete, end-to-end data flow, from session creation and OSINT enrichment to real-time messaging and multi-layered AI analysis.

```
+-----------------------------+
|      Sales Agent (User)     |
+-----------------------------+
             |
             | 1. Fills out "Start Session" form in UI
             v
+-----------------------------+      +--------------------------------+      +-----------------------------+
|    React Frontend (UI)      |<--+--|     FastAPI Backend (Server)   |----->|     MongoDB (Database)      |
| (localhost:5173)            |   |  |      (localhost:8000)        |      | (mongodb://localhost:27017) |
+-----------------------------+   |  +--------------------------------+      +-----------------------------+
    |         ^         ^         |            |           ^                       |
    | 2.      | 6.      | 12.       | 11.        | 2.        | 3. 4. 5. 7. 10.       | 2b.
    | POST    | Render  | Render    | Push       | Creates   | Read/Write            | Save
    | /api/   | Message | Gemini    | Update     | Session,  | Session Data          | OSINT
    | sessions|         | Analysis  | via WS     | Triggers  |                       | Data
    v         |         |           |            | Tasks     v                       |
+-----------------------------+   |            |  +-----------------------------+      |
|      WebSocket Connection   |   |            |  | [BACKGROUND TASK]           |      |
|    (/ws/{session_id})       |   |            |  | run_osint_enrichment        |------+
+-----------------------------+   |            |  +-----------------------------+
    ^         ^         ^         |            |              | 2a.
    | 6.      | 8.      | 11.       |            |              | Fetches data from
    | Push    | Push    | Push      |            |              v
    | Msg     | LLM     | Gemini    |            |  +-----------------------------+
    | Update  | Update  | Update    |            |  |   External OSINT APIs       |
    |         |         |           |            |  | (SerpAPI, Firecrawl, etc.)  |
    |         |         |           |            |  | (Currently Mocked w/ JSON)  |
    +---------+---------+-----------+            |  +-----------------------------+
                                                 |
             +-----------------------------------+
             | 3.
             | Agent sends message via UI -> POST /api/sessions/{id}/send
             v
+-----------------------------+      +-----------------------------+
|     Telethon (Sender)       |----->|      Telegram Network       |
+-----------------------------+  4.  +-----------------------------+
                                                 ^
                                                 | 5.
                                                 | Customer Replies
                                                 v
+-----------------------------+      +-----------------------------+
|   Telethon Listener         |----->| [BACKGROUND TASK]           |
| (in TelegramRouter)         |  7.  | run_local_llm_analyze       |
+-----------------------------+      +-----------------------------+
                                                 |
                                                 | 8.
                                                 | Sends Prompt to
                                                 v
+-----------------------------+      +-----------------------------+
|    Ollama (Local LLM)       |<-----| [BACKGROUND TASK]           |
|     (phi3:3.8b)             |  9.  | gemini_call (Triggered)     |
+-----------------------------+      +-----------------------------+
                                                 |
                                                 | 10.
                                                 | Sends Payload to
                                                 v
                                       +-----------------------------+
                                       |      Google Gemini API      |
                                       +-----------------------------+
```

## Step-by-Step Data Flow Explanation

1.  **Session Creation:** A **Sales Agent** fills out the new session form in the **React UI**.

2.  **Backend Initialization:**
    *   The UI sends a `POST` request to `/api/sessions`.
    *   The **FastAPI Backend** creates a new session document in **MongoDB**.
    *   Crucially, it triggers the `run_osint_enrichment` **Background Task**.
    *   **(2a) OSINT Enrichment:** This task is responsible for calling all **External OSINT APIs** (SerpAPI, Firecrawl, LinkedIn, etc.) to gather data about the customer. After fetching the data, it saves it to the `osint` field in the session document in **MongoDB**. 
        *   ***Note:*** *This step is currently simulated by our temporary fix, which loads the data from the `profiles_by_url (1).json` file.*
    *   **(2b)** The frontend establishes a **WebSocket Connection** to receive real-time updates for the new session.

3.  **Agent Sends First Message:** The agent sends the first message from the UI. This calls `POST /api/sessions/{id}/send`.

4.  **Message Delivery:** The backend uses **Telethon** to send the message over the **Telegram Network** to the customer. The sent message is saved to the database, and the UI is updated via WebSocket.

5.  **Customer Replies:** The customer sends a message back.

6.  **Backend Receives Reply:** The **Telethon Listener** on the backend catches the incoming message and calls the `POST /api/sessions/{id}/messages` endpoint to save it to **MongoDB**. The UI is updated via WebSocket to show the new message.

7.  **Local LLM Analysis Triggered:** Saving the new message (from either the agent or the customer) triggers the `run_local_llm_analyze` **Background Task**.

8.  **Tactical Analysis (Local LLM):** The task sends the conversation history and OSINT data to the **Ollama (Local LLM)**. The LLM returns its `Tactical_JSON` (sentiment, summary, state). This analysis is saved to the database. The UI is updated again via WebSocket to show the new tactical insights.

9.  **Gemini Call is Triggered:** After the local LLM analysis is saved, the backend checks for trigger conditions. If met, it enqueues a `gemini_call` **Background Task**.

10. **Strategic Analysis (Gemini):** The `gemini_call` task assembles a detailed payload (OSINT profile, tactical analysis, conversation history, etc.) and sends it to the **Google Gemini API**.

11. **Save and Push Gemini Response:** The backend receives the strategic JSON from Gemini, saves it to the database, and **pushes** the final update to the **React UI** via the WebSocket.

12. **UI Displays Final Insights:** The UI's "Intelligence Panel" is updated with the strategic coaching from Gemini, providing the agent with a complete, multi-layered view of the conversation.