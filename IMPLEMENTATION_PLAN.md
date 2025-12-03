# ConvoSphere Integration Plan

This document outlines the plan to integrate the new React frontend with the previously developed, more robust FastAPI backend.

## Goal

To combine the user-friendly React frontend with the powerful, session-based backend, including the local LLM analysis and autonomous UI updates.

## Phase 1: Backend Unification

1.  **Replace Existing Backend:** The current simple `api.py` (file-based chat storage, direct Gemini, Redis pub/sub for Telegram) will be replaced by our previously developed, more advanced backend (`api/main.py` from the old context).
    *   **Action:**
        *   Delete the existing `api.py` in the root.
        *   Rename `api/main.py` (from the old context) to `api.py` and move it to the root directory.
        *   Verify all necessary files from the old backend (`db/database.py`, `db/models.py`, `api/schemas.py`, `services/local_llm_service.py`, `services/telegram_router.py`, `gemini_client.py`) are present and correctly configured.
    *   **Outcome:** The application will now run on a FastAPI backend with MongoDB for persistent session storage, Redis (for its intended role), and a functional local LLM.

## Phase 2: Frontend API Client Adaptation

1.  **Update API Client (`frontend/src/api.ts`):** The React frontend's API client will be completely rewritten to communicate with the new, session-based backend.
    *   **Action:**
        *   Modify `frontend/src/api.ts` to replace existing chat-related API calls (`listChats`, `createChat`, `getChat`, `sendTelegram`, `pollTelegram`, `sendGemini`) with new functions that interact with the session-based endpoints (e.g., `listSessions`, `createSession`, `getSession`, `sendMessage`, `pollMessages`, `triggerLLMAnalysis`).
        *   Update URL paths and request/response body structures to match the new backend's API.
    *   **Outcome:** The React frontend will be able to correctly send requests and receive responses from the refactored FastAPI backend.

## Phase 3: UI Overhaul for the "Agent Console"

1.  **Refactor Main App Component (`frontend/src/App.tsx`):**
    *   **Action:** Modify `App.tsx` to manage the active session ID, display main chat and intelligence panes, and orchestrate data fetching.
    *   **Outcome:** Centralized session state and control.
2.  **Implement Session Sidebar (`frontend/src/components/Sidebar.tsx`):**
    *   **Action:** Update the sidebar to list active sessions. The "Create Chat" form will be adapted to call the `createSession` function from the updated API client.
    *   **Outcome:** Sales agents can easily create and switch between customer sessions.
3.  **Develop Telegram Chat Pane (`frontend/src/components/TelegramChatPane.tsx`):**
    *   **Action:** This component will be adapted to display the messages from the currently active session (fetched via `GET /api/sessions/{id}`). The message input and send functionality will use the `sendMessage` function from the API client.
    *   **Outcome:** A functional chat interface within the UI.
4.  **Create "Intelligence Panel" (`frontend/src/components/GeminiChatPane.tsx`):**
    *   **Action:** Repurpose `GeminiChatPane.tsx` into a display-only panel. It will fetch the `local_llm` data from the active session and display the structured `Tactical_JSON` analysis (global summary, sentiment, conversation state, etc.). The manual Gemini chat input will be removed.
    *   **Outcome:** Real-time tactical insights from the local LLM are presented to the agent.

## Phase 4: Autonomous UI Updates (Polling Mechanism)

1.  **Implement Polling in Frontend:**
    *   **Action:** Integrate a polling mechanism (using `setInterval`) into `frontend/src/App.tsx` or a dedicated data fetching hook. This will periodically call `getSession` for the active session.
    *   **Outcome:** The UI will automatically refresh the chat history and the Intelligence Panel with the latest data (new messages, updated LLM analysis) without requiring manual interaction, providing a live and responsive user experience.

## Phase 5: Testing and Validation

1.  **Test Backend API:** Verify all new and modified backend endpoints are working correctly using `curl` or Swagger UI.
2.  **Test Frontend Functionality:** Ensure the UI correctly displays sessions, sends messages, and updates autonomously.
3.  **Validate Local LLM Integration:** Confirm the Intelligence Panel shows accurate `Tactical_JSON` output.

This comprehensive plan will transform the current components into a fully integrated and functional ConvoSphere application.
