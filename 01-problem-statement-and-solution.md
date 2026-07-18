# Smart Task Manager — Problem Statement & Solution Overview

*Document 1 of the DPR series — establishes the problem, prior-art research, and the chosen direction before architecture/DB/API design.*

---

## 1. Problem Statement

Teams managing day-to-day work across email, chat, and spreadsheets lose visibility into **who is doing what, by when, and at what priority**. Common pain points:

- Tasks get created but never followed up — no automatic reminders or escalation when a due date is missed.
- Status updates require manual chasing (managers ping people on WhatsApp/Slack for "where are we").
- No single dashboard shows workload, overdue items, or team throughput.
- Recurring work (weekly reports, monthly reviews) is re-created by hand every cycle.
- Assigning priority is subjective and inconsistent across team members.

**Goal:** build a task management application that is not just a CRUD to-do list, but one where **automation and AI actively reduce manual follow-up work** — reminders, escalations, notifications, recurring tasks, and summary reports run on their own, and users can create/query tasks in natural language.

This is being built as a skills-demonstration project, so the emphasis is on:
1. Clean, defensible software engineering (auth, REST API, DB design, error handling).
2. **Automation depth** (n8n-driven workflows) — this is the primary differentiator to showcase.
3. Practical AI features layered on top, not a research project.

---

## 2. Prior Art Review (so we don't reinvent something that already exists)

Before designing our own system, existing tools were reviewed for overlap:

| Project | What it does | Why it's not a full match |
|---|---|---|
| **n8n Task Manager** (open-source, community project) | An n8n-workflow-only orchestration layer for tracking long-running *async jobs* (ML training, video rendering) with a Supabase backend and React monitoring dashboard | Solves *job/queue monitoring*, not human task/project management — no auth, assignment, comments, or priority concepts |
| **Taskosaur** | Self-hosted, open-source PM tool with conversational AI task execution ("create sprint with high-priority bugs"), Kanban, sprints, dependencies | Closest conceptually (conversational AI + self-host + modular architecture), but it's a full multi-tenant Agile PM suite (BSL-licensed) — far heavier than a demonstrable take-home build |
| **Leantime** | Open-source PM tool with an AI-boosted personal dashboard, mood-based prioritization | Aimed at ADHD/neurodivergent-friendly personal productivity, not team assignment + escalation workflows |
| **Focalboard / Taskcafe** | Self-hosted Kanban tools | Good UI inspiration, but no automation engine or AI layer |
| **Todoist / Motion / Trevor AI (commercial)** | Natural-language task capture, auto-scheduling, AI prioritization | Proprietary SaaS, not self-buildable/inspectable — useful only as UX inspiration for NLP task creation |

**Conclusion:** No existing open-source project fully matches the brief (secure multi-user task app **+** n8n-style event-driven automation **+** lightweight AI layer, built as a clean demonstrable codebase). We'll take inspiration rather than adopt an existing one wholesale:

- From **n8n Task Manager** → the pattern of using n8n purely as an external automation/orchestration layer talking to our app via REST webhooks, instead of building a custom cron/notification system by hand.
- From **Taskosaur** → the idea of a natural-language command layer on top of standard CRUD APIs, and keeping the "AI" and "core app" as separate, swappable modules.
- From **Todoist-style NLP capture** → parsing free text like *"remind John to submit the report by Friday, high priority"* into structured task fields.

We will **build our own solution**, purpose-fit to the assignment, rather than fork/extend any of the above.

---

## 3. Proposed Solution — Summary

A **modular monolith** (not microservices — unnecessary complexity for this scope, but designed so pieces could be split later):

```
[ React Frontend ] ⇄ [ REST API (Python/FastAPI) ] ⇄ [ PostgreSQL ]
                              │
                              ├──► [ n8n (automation engine) ] ──► Email / WhatsApp (Twilio) / Webhooks
                              │
                              └──► [ Agentic AI Layer (Python, Claude/OpenAI API) ] — NL task parsing,
                                     summaries, priority suggestion, chat-query, agent tool-use
```

- **App backend** owns the source of truth (tasks, users, comments, attachments) and exposes a clean REST API + webhooks.
- **n8n** is *not* embedded logic — it's an external orchestrator that polls/receives webhooks from our API to handle reminders, escalation, recurring task generation, and notifications. This is the part we'll go deepest on, since it's the explicit differentiator asked for.
- **AI layer** is a thin service sitting beside the API (own module/router), written in the same language as the backend, calling an LLM for: natural-language task creation, task summarization, priority recommendation, and a chat-style "ask about my tasks" interface — with room to grow into a proper agent (tool-use over the task API) without a rewrite.

### Why this shape
- Keeps the core CRUD app simple and testable (good engineering practices are easy to demonstrate).
- Pushes complex time-based/event-based logic (reminders, escalation, recurring generation, digest emails) into n8n, which is *visual, inspectable, and exactly the tool the interviewer already knows I use* — a natural way to showcase automation skill.
- AI features are additive and isolated, so the core app still works if the AI layer is disabled (good resilience story to mention in the discussion).
- Backend and AI/agentic layer share one language (Python), so the agent can call internal service functions directly instead of hopping across a language boundary — simpler to build and easier to reason about in a live walkthrough.

---

## 4. Recommended Tech Stack (simple, production-plausible, not over-engineered)

| Layer | Choice | Reasoning |
|---|---|---|
| Frontend | React + Vite, plain CSS/Tailwind | Fast to build, universally understood; staying with React rather than a Python UI alternative (e.g. Streamlit/Reflex) since React gives a proper production-grade SPA and is the safer default unless a specific Python-only constraint shows up |
| Backend | **Python + FastAPI** (REST, async) | Python as primary language (per preference), FastAPI gives async performance, automatic OpenAPI docs, and Pydantic request/response validation for free — also the natural home for the agentic AI code, so backend and AI live in one codebase/language |
| ORM / Migrations | SQLAlchemy (async) + Alembic | Standard, well-understood Python data layer with proper migration history |
| Database | PostgreSQL | Relational integrity for tasks/users/assignments/comments; easy ER modeling |
| Auth | JWT (access + refresh tokens) via `python-jose`, password hashing via `passlib`/bcrypt | Industry-standard, no need for a full identity provider at this scale |
| Automation engine | n8n (self-hosted via Docker) | Explicitly requested/expected; visual workflows are easy to demo live; talks to the FastAPI backend purely over HTTP/webhooks, so the backend's language is irrelevant to it |
| Notifications | `smtplib`/`fastapi-mail` (email) + Twilio WhatsApp API (or WhatsApp Cloud API) | Both integrate as simple n8n nodes/HTTP calls regardless of backend language |
| Agentic AI | Anthropic Claude API (Python SDK) via a dedicated `ai/` module — with an agent loop (tool-use over the task API) rather than a single-shot prompt | Same language as backend → the agent can call internal service/repository functions directly instead of crossing a network/language boundary; used for NL task parsing, summaries, priority suggestion, chat queries, and future tool-calling agents |
| File attachments | Local disk (dev) / S3-compatible bucket (prod-ready path) | Keep dev simple, but design the storage interface so swapping to S3 is a one-line config change |
| Deployment | Docker Compose (FastAPI app + Postgres + n8n) | One command to spin up the whole stack for a demo |

This intentionally avoids Kubernetes, microservices, message queues, or multiple databases — those would add complexity without adding to what's actually being evaluated (engineering fundamentals + automation + AI literacy).

---

## 5. Scalability Considerations

The stack above is intentionally simple, but every layer is chosen so it can scale **horizontally later without a rewrite** — that's the actual claim, rather than "it's just a demo, scalability doesn't matter" or over-engineering with Kubernetes/microservices from day one that would be hard to justify live.

**API layer (FastAPI)**
- Kept fully **stateless** — no in-memory sessions, JWT only — so N copies can run behind a load balancer with zero session-affinity issues.
- Async request handling (FastAPI + `async def` + async SQLAlchemy) means a single instance already handles concurrent I/O-bound requests (DB calls, LLM calls) efficiently before any scaling out is needed.
- Clean service/router separation so a hot path (e.g. search, or the AI module) could be pulled into its own deployable service later without touching the rest.

**Database (Postgres)**
- Indexes from day one on the columns that get filtered/sorted (`status`, `assignee_id`, `due_date`, `priority`) so search/filter/sort stays fast as data grows.
- Connection pooling (SQLAlchemy pool / PgBouncer) so connections aren't exhausted under load.
- Designed for **read replicas** later — dashboard/analytics queries are read-heavy and can be pointed at a replica, keeping writes fast on the primary.
- Pagination on every list endpoint (cursor or offset) — never an unbounded `SELECT *`.

**Automation (n8n)**
- n8n itself can scale horizontally via **queue mode** (Redis + multiple worker processes) instead of a single instance — worth naming explicitly, since it shows n8n's own scaling story, not just the app's.
- Notifications/reminders are **event-driven and decoupled**: the API fires a webhook/event and n8n picks it up asynchronously, so a spike in reminders never blocks a user-facing API request.

**Agentic AI layer**
- Isolated as its own module/router so LLM latency or provider rate limits never slow down core CRUD paths.
- Cache repeated/expensive AI calls where sensible (e.g. a daily summary generated once and reused, not recomputed per request).
- Because it's Python-native alongside the backend, it's also the easiest piece to peel out into its own deployable service first if it becomes the bottleneck.

**Caching**
- Redis in front of hot reads (dashboard analytics, task counts) — cheap to add, high impact, and pairs naturally with n8n's own Redis use in queue mode.

**Attachments**
- File contents stored in S3-compatible storage (not local disk) on the production path, so file storage isn't tied to a single app server's disk.

**Overall horizontal-scale story:** stateless FastAPI instances + JWT (no server-side session state) + Postgres with pooling/read replicas + Redis cache + queue-mode n8n = the path from "one container each" to "N containers behind a load balancer" requires configuration changes, not a redesign.

---

## 6. What's Next

The remaining DPR sections will be written in order, each building on this:
1. Functional requirements (detailed)
2. System architecture diagram
3. Database design (ER diagram)
4. API design (endpoint list + contracts)
5. Automation workflow design (the n8n flows, in detail)
6. AI / agentic feature design
7. Security considerations
8. Setup & deployment guide

(Scalability considerations are already captured above in Section 5 and will be referenced, not repeated, when we get to the architecture section.)

