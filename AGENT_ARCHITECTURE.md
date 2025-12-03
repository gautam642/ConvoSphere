Goal: convert this into a **product-ready multi-session outbound sales intelligence system** in which the salesperson initiates new conversations via Streamlit (or API), OSINT runs automatically, Local LLM provides rolling analysis, Gemini is called with structured JSON, alerts are triggered, all data stored in a DB (not file folders), and Telegram is used to send/receive messages.

---

# 1 — High level system overview (one paragraph)

User fills a “Start conversation” form in Streamlit (name, phone, short context, goal). Backend creates a new **session** in the DB, triggers automated OSINT enrichment (SERP, LinkedIn, GitHub, Numverify, Firecrawl) and stores results under the session. Then the backend asks the **Local LLM** (running locally) to initialize short/long contexts and produce the first outbound message. The message is sent to the customer via Telegram (or other channel). Incoming replies are routed to the session, appended to rolling short memory (last 10–20 messages), and each new message triggers Local LLM analysis. When certain thresholds / intent shifts occur, an **alert** is emitted (Telegram, dashboard). Periodically or on trigger, structured JSON is sent to Gemini for high-level strategy; Gemini output is saved and surfaced in the UI.

---

# 2 — Component diagram (textual, for code agent)

* **Frontend**

  * Streamlit app (`app.py`) — Start conversation form, Sessions list, Chat center, Intelligence panel (Local LLM + Gemini outputs), Alerts panel.
* **API Backend**

  * FastAPI app (`api/`) with endpoints for starting sessions, sending messages, retrieving session state, webhook for Telegram inbound messages.
* **Orchestrator**

  * `orchestrator.py` refactored into a callable service class `PersonOrchestrator` that runs enrichment pipeline asynchronously (job queue).
* **OSINT Tool Wrappers**

  * `tool_wrappers.py` and fetchers `numverify_fetcher.py`, `serpapi_tester.py`, `twitter_info_fetcher.py`, `linkedin_info_fetcher.py`, `firecrawler_linkcrawler.py`.
* **Local LLM Service**

  * `local_llm_service.py` (wraps llama.cpp/ollama or chosen runtime) that accepts structured JSON and returns `local_llm_output`.
* **Gemini Client**

  * `gemini_client.py` accepts structured JSON and returns `gemini_output`.
* **Message Router**

  * `telegram_router.py` (wraps Telethon or python-telegram-bot) to send outbound messages and receive inbound via webhook or long polling; routes messages to sessions.
* **State Store (DB)**

  * Postgres or MongoDB for persistent sessions; Redis for cache/queue. A single table/collection holds sessions and messages — no per-customer folders.
* **Background Worker / Queue**

  * Celery / RQ / fastapi-background-tasks to run OSINT fetches, Local LLM analysis, and Gemini calls.
* **Alerting**

  * Notification service that can push: Streamlit notifications, Telegram messages to salesperson, email.
* **Testing**

  * Unit tests and integration tests in `tests/`.
* **Deployment**

  * Dockerfile(s) for local dev and for production containerization.

---

# 3 — Data model / JSON schemas (copy-paste ready)

## `Session` (primary unit)

```json
{
  "session_id": "uuid",
  "created_at": "ISO8601",
  "updated_at": "ISO8601",
  "owner": "sales_agent_id",
  "customer": {
    "name": "Rahul Verma",
    "phone": "+919876543210",
    "context": "2nd year B.Tech, wants internships",
    "goal": "Sell DSA course"
  },
  "osint": {
    "numverify": {...},
    "linkedin": {...},
    "github": {...},
    "serp": [...],
    "firecrawl": {...},
    "confidence": 0.92
  },
  "messages": [
    {
      "message_id": "uuid",
      "session_id":"uuid",
      "timestamp":"ISO8601",
      "sender":"agent|customer|system",
      "channel":"telegram|streamlit",
      "text":"..."
    }
  ],
  "local_llm": {
    "last_analysis_at":"ISO8601",
    "short_context":"string",
    "long_summary":"string",
    "sentiment":"neutral-positive",
    "emotion":"curious",
    "buying_intent_score":62,
    "intent_shift": true,
    "intent_shift_at":"ISO8601",
    "risks":["price"],
    "opportunities":["trial module"]
  },
  "gemini": {
    "last_call_at":"ISO8601",
    "payload_sent": {...}, 
    "response": {...}
  },
  "alerts": [
    {
      "alert_id":"uuid",
      "type":"high_intent|risk|info",
      "created_at":"ISO8601",
      "message":"Rahul showed interest"
    }
  ],
  "status": "initialized|active|closed"
}
```

## `Local LLM Payload` (what you send to local LLM)

```json
{
  "session_id":"uuid",
  "customer": {...},         // sanitized customer info (NO PII raw if you want to avoid)
  "osint": {...},
  "short_context": [ /* last 10-20 messages */ ],
  "long_context_summary":"string",  // optional existing
  "goal":"Sell DSA course",
  "task":"analyze_and_summarize"
}
```

## `Gemini Payload` (what you send to Gemini)

```json
{
  "session_id":"uuid",
  "customer": {...},
  "osint": {...},
  "short_context": [...],
  "long_context_summary":"string",
  "local_llm_analysis": {...},
  "task":"recommend_next_action"
}
```

---

# 4 — API endpoints (FastAPI) to implement next

* `POST /api/sessions`
  Body: `{ name, phone, context, goal, owner_id }`
  Behavior: create session, return `session_id`, enqueue `osint_enrichment(session_id)` job, enqueue `local_llm_init(session_id)`

* `GET /api/sessions/{session_id}`
  Returns full session JSON (messages, osint, llm, gemini, alerts)

* `POST /api/sessions/{session_id}/messages`
  Body: `{ sender: "agent|customer", text, channel }`
  Behavior: append message to DB, update short_context queue, enqueue `local_llm_analyze(session_id)` job, possibly send message to channel if channel == "agent_to_customer"

* `POST /api/sessions/{session_id}/send`
  Body: `{ text }`
  Behavior: send outbound message via `telegram_router.send_message(phone, text)` and append message as `agent`.

* `POST /webhook/telegram`  (if using webhook)
  Behavior: route inbound messages to the appropriate session by phone mapping (or create session stub if none), then append and enqueue LLM analysis.

* `GET /api/sessions/{session_id}/alerts`
  Returns alerts.

* `POST /api/sessions/{session_id}/trigger_gemini`
  Force a Gemini call using the current structured JSON.

---

# 5 — Background jobs & orchestration (worker tasks)

Implement worker tasks (Celery/RQ):

* `osint_enrichment(session_id)`
  Sequence: numverify → serp → linkedin → github → firecrawl (parallel where possible) → merge results → update session.osint → trigger `local_llm_analyze(session_id)`

* `local_llm_init(session_id)`
  Build payload and call local LLM to produce initial short_context, first outbound message suggestion. Save `local_llm` fields. Optionally auto-send first message or return to UI for agent approval.

* `local_llm_analyze(session_id)`
  On each new message: fetch last 10–20 messages, current long_summary, osint; call Local LLM service; update session.local_llm; if `intent_shift` or `buying_intent_score > threshold` create alert.

* `gemini_call(session_id)`
  Called on triggers or manually: builds gemini payload and calls Gemini client; store response.

* `alert_dispatcher(alert_id)`
  Sends notifications via Telegram to salesperson, and creates UI notifications.

---

# 6 — Storage & retention (strategy)

* Use **single DB (preferred: Postgres)** or **MongoDB**. Postgres works well for relational queries (sessions/messages). MongoDB might feel natural for session JSON.
* **Messages as rows/documents** — not files.
* Rolling memory: store last 20 message text in `local_llm.short_context` (string/array). For audit, keep full messages but paginate.
* **Retention policy**: archive messages older than 365 days to cold storage (S3 or zipped dumps). Implement TTL for ephemeral cache keys in Redis.
* **Backups**: DB nightly backups.

---

# 7 — Local LLM interface & runtime choices

* Provide a `local_llm_service.py` with these methods:

  * `analyze(session_payload: dict) -> local_llm_output: dict`
  * `suggest_first_message(session_payload: dict) -> str`
* Supported runtime adapters:

  * `llama.cpp` / `llama.cpp-python` for GGUF models (Phi-3, Mistral, Llama 3). OR
  * `ollama` if you prefer that management layer.
* Keep calls synchronous inside workers; include timeout and fallback (e.g., if local LLM is down, mark analysis failed).
* Important: sanitize PII before sending to any remote API (Gemini). The local LLM runs locally and may use PII, but Gemini is external — remove explicit phone numbers and exact emails unless necessary; instead send attributes.

---

# 8 — Gemini integration rules & payload

* Use **structured JSON** payload (as you requested). No freeform prompt text outside minimal instruction.
* Always attach `session_id`, `local_llm_analysis`, `short_context`, `osint` and `task`.
* Before calling Gemini, run a sanitization step that removes any explicit PII fields if policy or compliance demands.
* Save Gemini response under `session.gemini.response` and `session.gemini.last_call_at`.

---

# 9 — Streamlit UI changes (specific tasks)

* Right panel: the **Start New Conversation** form with fields: `name, phone, context, goal, owner`.

  * Calls `POST /api/sessions` and displays new session in center chat area.
* Center: Chat area acting on selected `session_id`:

  * Show messages (with pagination).
  * Input box: typing sends `POST /api/sessions/{session_id}/send`.
  * Show `local_llm` analysis panel (short & long summaries)
  * Show Gemini suggestions panel and an “Apply suggestion” button to auto-send or edit suggestion.
* Left: Sessions list with quick badges: `buy_intent_score`, `last_message_time`, `status`, `alerts`.

---

# 10 — Alerting / triggers

Define threshold rules (configurable):

* `buying_intent_score >= 80` → create HIGH_INTENT alert.
* `intent_shift` true AND buy score increased by >= 15 → create ALERT.
* Customer asks about `price|stock|warranty|delivery` keywords → create ALERT.
* Alerts saved in `session.alerts` and dispatched via `alert_dispatcher`.

UI: show toast/popover and highlight session row.

---

# 11 — Security & Privacy checklist (must-implement)

* Store API keys in `.env`, never in repo.
* Sanitize PII before sending to external APIs (Gemini). At minimum mask phone numbers and emails in payloads.
* Logging: redact PII in logs.
* Access control: require simple API `owner_id` and enforce that an agent only sees their sessions (Streamlit login or token).
* Rate limiting: queue OSINT calls to avoid API quotas; respect each provider’s rate limits.
* Opt-out & deletion: implement `DELETE /api/sessions/{session_id}` which removes PII and messages permanently per GDPR-like requirement.

---

# 12 — Testing & acceptance criteria (deliverable checklist)

For each item below, tests or manual checks must exist.

**Core functionality**

* [ ] `POST /api/sessions` creates session, enqueues OSINT job, returns `session_id`.
* [ ] OSINT fetchers run successfully and store `session.osint`.
* [ ] `local_llm_init` produces a valid `short_context` and a first message suggestion saved to DB.
* [ ] `POST /api/sessions/{id}/send` sends message to Telegram (mockable in tests) and appends message to DB.
* [ ] Incoming Telegram messages are routed to session and appended.
* [ ] Local LLM re-analyzes on each new message and updates `session.local_llm`.
* [ ] `gemini_call` receives valid JSON and stores `response`.
* [ ] Trigger thresholds create alerts and dispatch notifications.

**Data & schema**

* [ ] All DB schema fields exist and are filled per sample JSON.
* [ ] Messages paginated in UI, last 20 used as rolling context.

**Privacy**

* [ ] Test to ensure PII is redacted before any external API call (unit test mocks).

**Performance**

* [ ] Local LLM calls not blocking UI; operations done in background workers.
* [ ] Failover if LLM/Gemini are down — error field present in session.

---

# 13 — Implementation plan (priority order — next steps for a code agent)

1. **DB + API skeleton**

   * Add DB migrations / schema for `sessions`, `messages`, `alerts`, `osint`, `local_llm`, `gemini`.
   * Implement `POST /api/sessions`, `GET /api/sessions/{id}`, `POST /api/sessions/{id}/send`, `POST /api/sessions/{id}/messages`.
   * Add a simple auth stub for `owner_id`.

2. **Background worker + job definitions**

   * Add Celery/RQ and Redis (or FastAPI background-tasks if you want simpler dev).
   * Implement `osint_enrichment(session_id)` and placeholder return values.

3. **Local LLM service wrapper**

   * Implement `local_llm_service.py` with `analyze()` and `suggest_first_message()`. Use a mock model or small GGUF model while developing.
   * Hook `local_llm_init` and `local_llm_analyze` worker tasks.

4. **Telegram router**

   * Refactor `telegram_talker.py` to be session-aware: map phone→session (or session→phone). Implement `send_message` and webhook receiver that calls `POST /api/sessions/{session_id}/messages`.

5. **Streamlit UI**

   * Add Start Conversation form. Wire to `POST /api/sessions` and show session page.

6. **Gemini client**

   * Implement `gemini_client.py` structured JSON call and `gemini_call` worker that stores result.

7. **Alerting**

   * Implement triggers in `local_llm_analyze` and `alert_dispatcher`.

8. **Testing**

   * Add tests for endpoints and workers (use mocks for external APIs).

9. **Documentation**

   * Update README with new endpoints and dev run steps (Docker compose with redis/postgres).

---

# 14 — Example sequence (end-to-end) — exactly what the code agent should test

1. Streamlit form → `POST /api/sessions` → session created with `status=initialized`.
2. API enqueues `osint_enrichment(session_id)` and `local_llm_init(session_id)`.
3. `osint_enrichment` runs fetchers and saves `session.osint`.
4. `local_llm_init` builds payload and returns `first_message_suggestion`. Save to DB.
5. Salesperson clicks “Send suggestion” in UI → calls `POST /api/sessions/{id}/send`.
6. Backend `telegram_router.send_message(phone, text)` sends message and DB appends `agent` message.
7. Customer replies (simulate in tests) → webhook routes to `POST /api/sessions/{id}/messages` (or finds session by phone and appends).
8. Worker `local_llm_analyze` runs, updates `session.local_llm`, possibly creates an alert.
9. If alert created, `alert_dispatcher` pushes to salesperson via Telegram or UI.
10. Salesperson opens session, sees Gemini suggestion (if triggered) under Intelligence panel and proceeds.

---

# 15 — Deliverables for the code agent (exact files & functions to create/edit)

1. `api/main.py` — FastAPI app with required endpoints.
2. `api/schemas.py` — Pydantic models for Session, Message, OSINT, LocalLLM, Gemini, Alert.
3. `db/models.py` — SQLAlchemy / Mongo schema definitions.
4. `workers/tasks.py` — Celery tasks: `osint_enrichment`, `local_llm_init`, `local_llm_analyze`, `gemini_call`, `alert_dispatcher`.
5. `services/local_llm_service.py` — class `LocalLLMService` with `analyze` & `suggest_first_message`.
6. `services/gemini_service.py` — call Gemini with structured JSON.
7. `services/telegram_router.py` — send_message(), webhook handler.
8. `ui/streamlit_app.py` — UI modifications (Start Conversation form, Sessions list, Chat panel, Intelligence panel).
9. `tests/` — unit+integration tests for endpoints and workers with mocks.
10. `docker-compose.yml` — services: app, redis, postgres (or mongo), worker, local-llm runtime (optional).
11. `docs/` — architecture.md, api_spec.md, deployment.md.

---

# 16 — Additional engineering notes (practical guidance)

* Keep OSINT fetchers rate-limited and capable of partial failure — don’t block session creation on fetcher errors. Mark `osint.status = partial|failed|complete`.
* Use a **config file** to set thresholds (intent_score_threshold, messages_window_size).
* All workers must be idempotent — safe to re-run.
* Implement logging/metrics (Prometheus-friendly if you need later).
* Start with SQLite + RQ for minimal dev friction; migrate to Postgres + Celery in prod.

---

# 17 — Acceptance criteria to ship feature (short)

* Salesperson can create session via Streamlit and see session page.
* OSINT runs automatically and results appear in session.
* Local LLM produces first message suggestion and it can be sent via UI → delivered over Telegram.
* Replies from customer are routed back and show in UI.
* Local LLM analysis updates after each message and can trigger an alert.
* Gemini can be invoked with structured JSON and its response is displayed.

---


