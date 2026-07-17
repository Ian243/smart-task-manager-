# Smart Task Manager (Simplified Jira) — Finalized Solution, Architecture & Implementation Plan

**Status: FINAL.** This document is the single source of truth for the build. Use this in every future session instead of re-deriving decisions — it supersedes the tentative choices in `01-problem-statement-and-solution.md` (kept for the reasoning/research trail only).

---

## 1. What We're Building — One-Liner

A **simplified Jira**: a multi-user work-tracking system (auth, tasks, assignment, priority, status, comments, attachments, dashboard, search/filter/sort) with a **mandatory n8n automation layer** (reminders, escalation, notifications, recurring tasks, summary reports) and a **Python agentic AI layer** (NL task creation, summaries, priority recommendation, chat-based status queries) — built to demonstrate software engineering, automation, and applied-AI skill in one cohesive, explainable codebase.

## 2. Scope Policy (what's mandatory vs. stretch)

| Bucket | Policy |
|---|---|
| **Core requirements** (auth, CRUD, assignment, priority, due dates, status tracking, search/filter/sort, comments/activity history, attachments) | **Mandatory.** All must be implemented and demoable. |
| **Advanced automation** (reminders, escalation, notifications, recurring tasks, daily/weekly summaries, event-driven workflows via n8n) | **Mandatory.** This is the explicit differentiator — goes deepest of all sections. |
| **AI features** (NL task creation, AI summaries, priority recommendation, chat query interface) | **Build in priority order below**, as time allows — all four are the target, none is skippable without reason. |
| **Stretch AI** (RAG over comments/attachments, MCP/A2A integration, browser-style agent actions) | **Optional.** Only attempted once the above is solid and working end-to-end. Not to be started early at the expense of core/automation work. |

---

## 3. Finalized Tech Stack

| Layer | Choice | Notes |
|---|---|---|
| Frontend | **React** (Vite) + Tailwind | SPA, calls the REST API directly |
| Backend | **Python + FastAPI** (async) | Primary language per preference; async I/O for DB + LLM calls; auto-generated OpenAPI docs (doubles as API design doc) |
| ORM / Migrations | SQLAlchemy (async) + Alembic | Schema versioned from day one |
| Database | **PostgreSQL** | Single relational store for all core entities |
| Auth | JWT (access + refresh), `passlib`/bcrypt for hashing, `python-jose` for tokens | Stateless — no server-side sessions |
| Automation engine | **n8n**, self-hosted via Docker | External orchestrator; talks to FastAPI purely over HTTP (webhooks in, REST calls out) |
| Notifications | Email via SMTP (`fastapi-mail`) + WhatsApp via Twilio WhatsApp API / WhatsApp Cloud API | Both triggered from n8n nodes, not hand-rolled in the backend |
| Agentic AI | Anthropic Claude API (Python SDK), dedicated `ai/` package with an agent loop (tool-use over internal task services) | Same language/process family as backend — no cross-language hop for tool calls |
| Caching (as needed) | Redis | Hot dashboard reads; also backs n8n queue mode if automation volume grows |
| File attachments | Local disk (dev) → S3-compatible bucket (prod path) behind one storage interface | Swappable via config, not code changes |
| Deployment | Docker Compose: `api`, `postgres`, `n8n`, `redis` (optional), `frontend` | One command spins up the full demo stack |

**Docker portability notes (for moving this to a different machine):** schema is fully reproducible on a fresh system via `alembic upgrade head` — data itself is not, since named volumes stay on the host that created them; moving actual rows requires an explicit `pg_dump`/`pg_restore`, not a `docker pull`. `.env` is gitignored on purpose and must be recreated with real secrets on every new system — a container starting successfully doesn't mean `.env` was filled in correctly. If the API image is built on Apple Silicon and deployed to a standard amd64 host, use `docker buildx build --platform linux/amd64,linux/arm64` rather than a plain build, or build directly on the target machine for a demo. Networking assumes the whole `docker-compose.yml` stack moves together — the API reaches Postgres via the Docker-internal service name `postgres`, not `localhost`, so bring up the full stack together on any new system.

---

## 4. Finalized Architecture

```
                         ┌─────────────────────┐
                         │   React Frontend     │
                         │ (auth, dashboard,    │
                         │  task board, chat UI)│
                         └──────────┬───────────┘
                                    │ REST (JWT)
                                    ▼
                    ┌───────────────────────────────┐
                    │        FastAPI Backend         │
                    │  ┌─────────────────────────┐   │
                    │  │ auth/                    │   │
                    │  │ tasks/  (CRUD, assign,   │   │
                    │  │          search/filter)  │   │
                    │  │ comments/ & activity/     │   │
                    │  │ attachments/              │   │
                    │  │ dashboard/ (analytics)    │   │
                    │  │ webhooks/ (for n8n)       │   │
                    │  │ ai/  (agentic layer)      │   │
                    │  └─────────────────────────┘   │
                    └───────┬───────────────┬────────┘
                            │               │
                     SQLAlchemy/asyncpg   Anthropic Claude API
                            │               (NL parsing, summaries,
                            ▼                priority rec, chat)
                    ┌───────────────┐
                    │  PostgreSQL   │
                    └───────────────┘
                            ▲
                            │ webhooks / REST calls
                            │
                    ┌───────────────────────────────┐
                    │              n8n                │
                    │ - due-date reminder workflow     │
                    │ - overdue escalation workflow     │
                    │ - assignment/completion notify     │
                    │ - recurring task generator          │
                    │ - daily/weekly summary report        │
                    └───────┬───────────────┬────────────┘
                            ▼               ▼
                     Email (SMTP)     WhatsApp (Twilio)
```

**Data flow for automation:** the backend never runs its own cron jobs or sends notifications directly. It either (a) exposes REST endpoints n8n polls/schedules against (e.g. "get tasks due in next 24h", "get overdue tasks"), or (b) fires a webhook to n8n on state changes (task assigned, task completed). n8n owns all timing, retries, and notification dispatch — this is the intentional design choice that showcases the automation skillset.

**Data flow for AI:** the `ai/` package is a normal FastAPI router but internally runs an agent loop — it calls Claude with the user's natural-language input plus tool definitions that map to the same internal task-service functions the REST routes use (create task, update priority, query tasks). This keeps one source of truth for business logic: both the human-facing REST API and the AI agent go through the same service layer, never duplicate logic.

---

## 5. Core Requirements → Architecture Mapping

| Requirement | Where it's satisfied |
|---|---|
| Secure login & authentication | `auth/` router — register/login, JWT access+refresh, bcrypt hashing |
| Dashboard with task analytics | `dashboard/` router — counts by status/priority, overdue count, per-user workload, completion trend |
| Create/Update/Delete tasks | `tasks/` router — standard REST CRUD, soft-delete for audit trail |
| Task assignment | `tasks.assignee_id` FK to `users`; reassignment fires an activity-log entry + n8n notify webhook |
| Priority (Low/Medium/High) | `tasks.priority` enum column; also settable/suggested by the AI layer |
| Due dates | `tasks.due_date`; drives the n8n reminder/escalation workflows |
| Status tracking (To Do/In Progress/Completed) | `tasks.status` enum; every change appended to `activity_log` |
| Search, filter & sort | Query params on `GET /tasks` (status, priority, assignee, due range, text search), indexed columns |
| Comments & activity history | `comments` table (user-authored) + `activity_log` table (system-authored, auto-generated on every field change) |
| File attachments | `attachments` table (metadata) + storage interface (disk/S3), linked to a task |

---

## 6. AI & Automation Workflows — Finalized List

### Automation (n8n) — mandatory, build in this order
1. **Due-date reminder** — scheduled workflow polls `GET /tasks/due-soon`, sends email/WhatsApp reminder X hours before due date.
2. **Overdue escalation** — scheduled workflow polls `GET /tasks/overdue`, notifies assignee first, then escalates to the task creator/manager after a grace period.
3. **Assignment / completion notifications** — webhook-triggered (backend calls n8n webhook on assignment or status→Completed) → email/WhatsApp to the relevant user.
4. **Recurring task generation** — scheduled workflow reads `recurring_task_templates`, creates new task instances on the defined cadence (daily/weekly/monthly).
5. **Daily/weekly summary report** — scheduled workflow calls `GET /dashboard/summary`, formats and emails a digest to managers.
6. **Event-driven workflow automation** — the general pattern above (webhook-in / REST-poll + webhook-out) *is* the event-driven architecture; no separate message broker needed at this scale.

### AI (Python agentic layer) — build in this order
1. **Natural-language task creation** — `POST /ai/parse-task` takes free text ("remind John to submit the report by Friday, high priority"), returns structured task fields; user confirms before it's created.
2. **AI-generated task summaries** — on demand or nightly, summarize a task's comment/activity thread into a short status blurb.
3. **AI-based priority recommendation** — suggest Low/Medium/High based on due-date proximity, task description, and historical patterns; user can accept or override.
4. **Chat interface to query task status** — `POST /ai/chat`, an agent with tool access to task-query functions ("what's overdue for the design team?", "summarize my open tasks").

**n8n vs. LangChain/ADK — why both, not either/or:** n8n is the event/business-process orchestrator (reminders, escalation, notifications, recurring generation) — it is explicitly the tool the brief points to for that section, and it scales horizontally via queue mode (Redis + worker processes) for higher workflow volume; it is not a data-processing engine, so any heavy computation stays in the FastAPI backend, with n8n only orchestrating calls to it. LangChain/Google ADK/LangGraph solve a different problem — structuring an LLM's multi-step reasoning, tool-use, and memory — and would live *inside* the `ai/` package if the agent's reasoning grows complex enough to need them. The two are complementary layers, not competing choices.

### Stretch (only if the above is fully solid)
- RAG over comments/attachments for richer chat answers.
- MCP-style tool exposure so the agent could be driven from an external MCP client.

---

## 7. High-Level Data Model (entities — full ER diagram is the next session's deliverable)

- **users** (id, name, email, password_hash, role, created_at)
- **tasks** (id, title, description, status, priority, due_date, assignee_id→users, created_by→users, created_at, updated_at, deleted_at)
- **comments** (id, task_id→tasks, user_id→users, body, created_at)
- **activity_log** (id, task_id→tasks, actor_id→users, field_changed, old_value, new_value, created_at)
- **attachments** (id, task_id→tasks, uploaded_by→users, file_name, storage_path, mime_type, size, created_at)
- **recurring_task_templates** (id, title_template, description_template, priority, cadence, next_run_at, created_by→users)
- **notifications_log** (id, task_id→tasks, channel [email/whatsapp], recipient, event_type, sent_at, status) — for audit/debugging of the n8n-driven sends

---

## 8. High-Level API Surface (grouped — full contract is a later session)

- `auth/` → register, login, refresh, me
- `tasks/` → CRUD, list with filters/sort/search, `due-soon`, `overdue` (for n8n polling)
- `tasks/{id}/comments` → add/list comments
- `tasks/{id}/activity` → activity history
- `tasks/{id}/attachments` → upload/list/download
- `dashboard/` → analytics summary, per-user workload, `summary` (for n8n digest workflow)
- `webhooks/n8n/` → inbound endpoints n8n calls back into (if needed), outbound webhook triggers on assignment/completion
- `ai/parse-task`, `ai/summarize/{task_id}`, `ai/suggest-priority`, `ai/chat`

---

## 9. Security Considerations (high-level — detailed section comes later)

- JWT access/refresh tokens, short-lived access token, hashed refresh token storage.
- **Role-based authorization (finalized design):** two functional roles — `member` and `manager` (the `UserRole` enum also reserves `admin` for future user-management features, not built now). Role is embedded as a claim in the JWT payload at login. Permission rules, enforced server-side in the service layer (never only in the frontend):
  - **Member**: create tasks; update/comment on tasks they created or are assigned to; view their own workload on the dashboard.
  - **Manager**: everything a member can do, plus assign/reassign any task to anyone, delete any task, view team-wide dashboard analytics, and receives escalation notifications for overdue tasks.
  - Enforcement is role **+** ownership, not role alone — e.g. "can update this task" = `is_manager OR task.assignee_id == current_user.id OR task.created_by == current_user.id`. A FastAPI dependency (e.g. `require_role("manager")`) raises `403 Forbidden` before route logic runs for role-gated actions; ownership checks happen inside the service layer for the rest.
  - **Known trade-off, not a bug:** embedding role in the JWT means a role change (e.g. promoting a member to manager) doesn't take effect until their token refreshes/expires. Worth stating proactively if asked in the technical discussion.
  - **Demo plan:** seed 4 users in Phase 2 — 1 manager + 3 members — so the permission boundary can be demonstrated live (a member's reassign attempt gets a 403; the manager's succeeds), rather than just described.
- Input validation via Pydantic models on every endpoint.
- Rate limiting on auth and AI endpoints (both are abuse-prone).
- Secrets (DB creds, JWT secret, Claude/Twilio keys) via environment variables / `.env`, never committed.
- Webhook endpoints called by n8n protected by a shared secret header, not left open.
- Structured logging (request id, user id, action) for traceability; no sensitive data (passwords, tokens, full attachment contents) in logs.
- **Auth provider stance:** custom JWT auth is built for this project deliberately, to demonstrate the underlying mechanism (hashing, signing, verification). Documented explicitly as a Future Enhancement that a production deployment would federate to an OIDC-based IdP (Okta / Azure AD / Auth0) for SSO, MFA, centralized user lifecycle, and compliance — same token-verification shape, just issued by the IdP instead of us.

## 10. Scalability Considerations (reference)

Already finalized in `01-problem-statement-and-solution.md` §5 — stateless FastAPI, Postgres pooling/indexing/read-replica path, n8n queue mode, decoupled event-driven notifications, isolated AI module, Redis caching, S3-path attachments. Carried forward unchanged; will be restated in the formal DPR architecture section rather than repeated here.

---

## 11. Implementation Plan — Session-by-Session Roadmap

Use this as the checklist for future build sessions. Each phase is designed to be a self-contained session.

- **Phase 0 — Scaffolding:** repo structure, Docker Compose (api/postgres/n8n/redis), env config, base FastAPI app with health check.
- **Phase 1 — Database:** SQLAlchemy models for all entities in §7, Alembic migrations, seed script.
- **Phase 2 — Auth:** register/login/refresh, JWT middleware (role embedded as a claim), password hashing, role-based dependency guards (`require_role`), ownership-based checks in the service layer. Seed 4 demo users (1 manager + 3 members) so the member/manager permission boundary can be demonstrated live, not just described.
- **Phase 3 — Core task CRUD:** tasks, assignment, priority, due dates, status, soft delete, search/filter/sort/pagination.
- **Phase 4 — Comments, activity log, attachments:** comment endpoints, auto-activity-logging on field changes, file upload/storage interface.
- **Phase 5 — Dashboard/analytics:** aggregate queries for the dashboard + the `due-soon`/`overdue`/`summary` endpoints n8n will consume.
- **Phase 6 — n8n automation workflows (narrowed scope):** Build **two workflows fully, end-to-end**: (1) assignment/completion notifications (webhook-triggered) and (2) due-date reminders (scheduled polling) — chosen because together they exercise both automation patterns (event-driven and scheduled) rather than picking two similar ones. The remaining four (escalation, recurring generation, daily/weekly summaries) are **designed but deferred** — same REST endpoints already listed in §8 support them, so adding them later is pure n8n configuration, not backend rework. **Build method:** provision these two workflows via n8n's REST API / JSON import rather than manual UI clicking, so the step is scriptable and reproducible by an autonomous coding agent; export the resulting workflow JSON into the repo (`n8n/workflows/*.json`) for version control. Open the n8n UI afterward to view/demo/tweak the workflow visually — the visual artifact still exists, it's just not how an agent builds it.
- Phase 7 — Agentic AI layer: `ai/` package, tool definitions over the task service layer, the four AI features in §6 in order.
- **Phase 8 — Frontend:** React app — login, dashboard, task board/list, task detail (comments/attachments/activity), chat widget for the AI interface. Built against the **full API surface** regardless of which n8n workflows are live yet, plus a notifications-log view, so adding the four deferred workflows later requires zero frontend changes — you'll be able to see automation firing as each one comes online.
- Phase 9 — Hardening: logging, error handling, rate limiting, security pass against §9.
- Phase 10 — Docs & deployment: remaining DPR sections (ER diagram, API contracts, formal automation/AI/security write-ups), README with setup instructions, final Docker Compose demo run-through.

### Definition of Done — per phase

Each phase is only "done" when all of these hold, not just when the code is written:

- [ ] Code follows `03-coding-conventions-and-file-structure-rules.md` (file consolidation + inline comment rules)
- [ ] Relevant model/relationship changes have a matching Alembic migration, reviewed before applying
- [ ] New endpoints are reachable and manually verified via `/docs` (or curl) — not just "should work"
- [ ] `configure_mappers()` / app import still succeeds with no errors (quick regression check after model changes)
- [ ] Any new env vars are added to `.env.example` with a comment explaining their purpose
- [ ] The phase's specific requirement(s) from §5/§6 are demonstrably satisfied, not just plausible

**Status as of this writing:** Phase 0 (scaffolding) and Phase 1 (database) are complete — verified via `configure_mappers()`, a compiled-DDL check against the ERD, and a clean FastAPI app import. Models are consolidated into `models/user.py` and `models/task_domain.py` per the coding conventions doc. Next up: **Phase 2 — Auth.**
