# Architecture, Automation & Security

This document formalizes the design of the three most complex pillars of the Smart Task Manager: the n8n Automation Engine, the Agentic AI Layer, and the Security/RBAC model.

## 1. Automation Layer (n8n)

The application offloads all asynchronous workflows, notifications, and scheduled polling to a self-hosted **n8n** container. This keeps the core FastAPI backend stateless and strictly focused on business logic.

**Workflows Deployed (Phase 6)**:
Currently, there are two primary workflows fully deployed and active in the n8n engine:
1. **Assignment Notifications (Event-driven):** Triggered via a webhook from the FastAPI backend whenever a task is assigned or reassigned. It dispatches a Mock Email/WhatsApp notification.
2. **Due-Date Reminders (Scheduled):** A cron-based workflow that polls the `/api/v1/tasks/due-soon` endpoint every hour and notifies assignees if a deadline is approaching.

**Future Expandability**:
The backend already supports the endpoints required for additional workflows (e.g., Escalation for `/overdue`, Dashboard Digests for `/summary`). *Once these are configured visually through the n8n UI, they will seamlessly integrate with the existing backend without requiring code changes.* This document should be updated when new workflows are activated via the UI.

## 2. Agentic AI Layer

The AI layer is built natively in Python using the `litellm` and `anthropic` SDKs, directly sharing the SQLAlchemy service layer to avoid logic duplication.

**Features**:
1. **Natural Language Task Parsing (`/parse-task`)**: Translates unstructured human requests ("Remind bob to fix the server by tomorrow high priority") into a structured JSON payload for task creation.
2. **Priority Suggestion (`/suggest-priority`)**: Analyzes the semantic context of a task description and deadline to recommend `LOW`, `MEDIUM`, or `HIGH`.
3. **Thread Summarization (`/summarize`)**: Distills long comment threads and activity logs into a concise executive summary.
4. **Agentic Chat (`/chat`)**: A conversational interface powered by function-calling (Tool Use). The LLM is equipped with internal tools (e.g., `query_tasks`, `update_task`) allowing it to execute real database actions autonomously based on user prompts.

## 3. Security & RBAC (Role-Based Access Control)

**Authentication**:
- Stateless JWT (JSON Web Tokens).
- Passwords hashed using `bcrypt` via `passlib`.

**Authorization Model**:
- **Role Binding**: Users are assigned either `MEMBER` or `MANAGER`. The role is embedded as a claim within the JWT.
- **FastAPI Dependencies**: The `@require_role()` dependency enforces authorization at the HTTP layer, rejecting requests (HTTP 403) before they reach the service layer.
- **Ownership Verification**: Deeply nested permissions (e.g., "Can I delete this task?") are evaluated in the service layer against the `current_user` injected by the token verifier, ensuring that members can only mutate their own assets.

**Hardening (Phase 9)**:
- **Rate Limiting (`slowapi`)**: Memory-backed leaky-bucket rate limiting protects the `/auth/login` (5/min) and `/ai/*` (10-20/min) endpoints from brute-force and resource-exhaustion attacks.
- **Structured Logging**: A custom middleware injects a unique UUID (`X-Request-ID`) into every request lifecycle. This ID is appended to the logs and returned in the HTTP Response Headers, ensuring full traceability of errors without leaking sensitive stack traces to clients.
