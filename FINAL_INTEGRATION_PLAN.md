# Final Integration Plan (New UI & AI Workflow)

This document outlines the definitive plan to refactor the new React-based frontend to make it fully compatible with our existing, advanced, session-based backend.

---

### **Phase 1: Frontend API Client & Data Model Refactoring**

**Goal:** Make the frontend speak the same language as the backend.

1.  **Update Data Models (`frontend/src/types.ts`):**
    *   **Action:** The existing `frontend/src/types.ts` file will be completely rewritten.
    *   **Logic:** The old `Chat`, `ChatSummary`, etc., types will be removed. They will be replaced with new TypeScript interfaces (`Session`, `Message`, `Customer`, `LocalLLMAnalysis`, `GeminiAnalysis`, etc.) that precisely match our backend's Pydantic schemas.

2.  **Update API Client (`frontend/src/api.ts`):**
    *   **Action:** The `frontend/src/api.ts` file will be rewritten to call our existing backend endpoints.
    *   **Logic:**
        *   `listChats` will become `listSessions` and will call `GET /api/sessions`.
        *   `createChat` will become `createSession` and will call `POST /api/sessions`.
        *   `getChat` will become `getSession` and will call `GET /api/sessions/{id}`.
        *   `sendTelegram` will become `sendMessage` and will call `POST /api/sessions/{id}/send`.
        *   The `pollTelegram` function will be **removed**, as our backend uses WebSockets for real-time updates.
        *   `sendGemini` will become `triggerGemini` and will call a new `POST /api/sessions/{id}/trigger_gemini` endpoint.

---

### **Phase 2: UI Component and AI Workflow Integration**

**Goal:** Refactor the React components to use the new API functions, implement the new AI workflow, and display all the data correctly.

1.  **Main App Component (`App.tsx`):**
    *   **Action:** Overhaul the component's state management.
    *   **Logic:** It will be updated to manage a list of `Session` objects and an `activeSession`. The existing polling logic will be completely removed and replaced with a **WebSocket connection** to our backend's `/ws/{session_id}` endpoint for real-time, push-based updates.

2.  **Sidebar Component (`Sidebar.tsx`):**
    *   **Action:** Update the form and list rendering.
    *   **Logic:** The "New Chat" form will be updated to collect all fields required for a `Session` (`name`, `phone`, `context`, `goal`, `owner_id`). The list will now display `Session` objects.

3.  **Telegram Chat Pane (`TelegramChatPane.tsx`):**
    *   **Action:** Connect the component to the main `activeSession` state.
    *   **Logic:** The chat history will be rendered directly from the `activeSession.messages` array. The "Send" button will now call the new `sendMessage()` function from our refactored `api.ts`.

4.  **Gemini Chat Pane (`GeminiChatPane.tsx`):**
    *   **Action:** This component will be refactored to serve a dual purpose.
    *   **Logic:**
        *   **Local LLM Display (Background):** A new, read-only section will be added to this pane to display the tactical analysis from the `activeSession.local_llm` object.
        *   **Interactive Gemini Chat:** The existing chat input in this pane will be connected to the new `triggerGemini()` API function to allow the agent to have a direct, interactive conversation with the Gemini "Strategic Coach".

---

### **Phase 3: Backend Gemini Implementation**

**Goal:** Implement the backend logic to support the interactive Gemini feature.

1.  **Create Gemini Trigger Endpoint:**
    *   **Action:** Create the new `POST /api/sessions/{session_id}/trigger_gemini` endpoint in `api.py`.

2.  **Implement Gemini Background Task (`run_gemini_call`):**
    *   **Action:** Implement the logic inside this existing background task.
    *   **Logic:** When triggered, it will assemble the payload as specified in the `Convo Sphere Sales Assistant Spec Mvp.docx.md`, call the Gemini API, save the response to the database, and push the update to the UI via the WebSocket.
