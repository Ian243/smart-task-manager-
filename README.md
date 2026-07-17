# Smart Task Manager

A comprehensive, full-stack task tracker built with **FastAPI**, **React (Vite + Tailwind)**, **PostgreSQL**, and heavily augmented with an **n8n Automation Engine** and an **Agentic AI Layer**.

## Key Features
- **Task Management**: Create, assign, track, and filter tasks. Comments and file attachments are supported natively.
- **RBAC Security**: JWT-based Authentication with `Member` and `Manager` roles enforcing strict ownership access at the service layer.
- **Automation (n8n)**: Decoupled automation engine handling event-driven notifications (webhooks), recurring tasks, and scheduled due-date reminders.
- **Agentic AI Layer**: Native Python integration via `litellm` (running Groq/Llama-3.3) offering natural-language task creation, dashboard analytics, and an autonomous chat interface.
- **Hardened API**: In-memory rate-limiting (`slowapi`) and robust FastAPI dependencies.

## Core Features & Requirements Alignment

| Requirement | Implementation Status | Technical Details |
| --- | --- | --- |
| **Secure Login & Authentication** | ✅ Implemented | JWT-based auth with bcrypt hashing. Strictly enforced RBAC (`get_current_user` dependencies). |
| **Dashboard with task analytics** | ✅ Implemented | Aggregates tasks by status, priority, and upcoming due dates directly on the dashboard. |
| **Create, Update, Delete Tasks** | ✅ Implemented | Full CRUD API using SQLAlchemy 2.0 with Pydantic validation. Managers can delete; Members can only update their assigned tasks. |
| **Task Assignment** | ✅ Implemented | Managers can assign tasks to members during creation or editing. |
| **Priority (Low/Medium/High)** | ✅ Implemented | Tracked using PostgreSQL ENUM types. Highlighted with UI badging. |
| **Due Dates** | ✅ Implemented | Date tracking with validation. Overdue tasks are flagged in red on the frontend. |
| **Status Tracking** | ✅ Implemented | Kanban-style architecture tracking `to_do`, `in_progress`, and `completed`. |
| **Search, Filter & Sort** | ✅ Implemented | Client-side reactive searching by title/description, plus dropdown filtering for Assignees and Priority. |
| **Comments & Activity History** | ✅ Implemented | Independent PostgreSQL tables (`TaskComment`, `TaskActivity`) automatically record field changes and user comments. |
| **File Attachments** | ✅ Implemented | Multipart form upload allowing users to attach files (PDF, images, text) securely to specific tasks. |

## Advanced Automation (n8n Integration)

| Automation Workflow | Implementation Status | Technical Details |
| --- | --- | --- |
| **Automatic reminders (due soon)** | ✅ Implemented | Daily Cron (`0 8 * * *`) hits `/api/v1/tasks/due-soon` and sends Gmail reminders. |
| **Escalation for overdue tasks** | ✅ Implemented | Daily Cron (`0 9 * * *`) hits `/api/v1/tasks/overdue` and escalates via email. |
| **Notifications on Assignment/Completion** | ✅ Implemented | Event-driven Webhook architecture. Backend `update_task` fires non-blocking async hooks to n8n upon status changes. |
| **Recurring task generation** | ✅ Implemented | Managers create recurring blueprints. n8n Cron hits `/api/v1/recurring/generate` to spawn real tasks. |
| **Event-driven workflow** | ✅ Implemented | Completely decoupled using n8n. Internal API uses secure `X-API-Key` bypass for internal machine-to-machine auth. |

## AI Features

| AI Feature | Implementation Status | Technical Details |
| --- | --- | --- |
| **Chat interface to query tasks** | ✅ Implemented | Dedicated `/ai` interface in the React UI with markdown rendering. |
| **Agentic AI & Tool Calling** | ✅ Implemented | Uses `LiteLLM` pointing to Groq `llama-3.3-70b-versatile`. We implemented strict JSON Schema tools (`create_task`, `get_dashboard_summary`, etc.) that the LLM invokes directly to interact with the database on behalf of the user. |
| **Create tasks using natural language** | ✅ Implemented | Supported via the `create_task` tool. Example: *"Create a high priority task to review PRs and assign to Dave."* |
| **AI-generated summaries** | ✅ Implemented | AI can aggregate database contents and summarize the user's workload upon request. |

---

## Setup & Deployment Instructions (GitHub -> Docker)

The entire application is containerized and requires only Docker to run.

### 1. Push to GitHub (From Dev Machine)
Ensure your `.env` file is excluded (check `.gitignore`).
```bash
git init
git add .
git commit -m "Initial commit: Smart Task Manager"
git remote add origin https://github.com/YourUsername/smart-task-manager.git
git push -u origin main
```

### 2. Clone on Target Machine
```bash
git clone https://github.com/YourUsername/smart-task-manager.git
cd smart-task-manager
```

### 3. Create the Environment File
Create a `.env` file in the root folder with the following variables:
```ini
ENVIRONMENT=development
POSTGRES_USER=taskmanager
POSTGRES_PASSWORD=taskmanager
POSTGRES_DB=taskmanager
POSTGRES_SERVER=postgres
POSTGRES_PORT=5432

JWT_SECRET_KEY=generate_a_random_secure_string_here
# Must match the n8n workflows
N8N_SHARED_SECRET=replace-with-a-shared-secret

# Your Groq API Key
GROQ_API_KEY=gsk_your_real_api_key_here
LLM_MODEL_NAME=groq/llama-3.3-70b-versatile
```

### 4. Deploy using Docker Compose
```bash
docker compose up -d --build
```
This will build the Vite frontend, the FastAPI backend, and pull the PostgreSQL, Redis, and n8n images. The `api` container automatically runs `alembic upgrade head` and seeds the database on startup. 

### 5. Final N8N Setup & Access
- **React Frontend**: [http://localhost:5173](http://localhost:5173)
- **FastAPI Backend / Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **n8n Dashboard**: [http://localhost:5678](http://localhost:5678) 

Visit `localhost:5678`, import the 4 JSON workflow templates from the `n8n/workflows/` directory into n8n, add your Google OAuth2 credentials to enable the email nodes, and activate the workflows!
