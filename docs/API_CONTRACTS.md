# API Contracts

The Smart Task Manager API is built with FastAPI and follows RESTful principles. All endpoints are prefixed with `/api/v1` except for `/auth`.

For the full interactive documentation, start the server and navigate to `/docs` (Swagger UI).

## 1. Authentication (`/auth`)
**`POST /auth/login`**
- **Purpose**: Authenticates a user and returns an access token.
- **Request (Form Data)**:
  - `username` (string, email format)
  - `password` (string)
- **Response (`200 OK`)**:
  ```json
  {
    "access_token": "eyJhbG...",
    "token_type": "bearer"
  }
  ```

## 2. Tasks (`/api/v1/tasks`)
**`POST /api/v1/tasks`**
- **Purpose**: Create a new task.
- **Payload**:
  ```json
  {
    "title": "Fix database indices",
    "description": "Optimize slow queries",
    "status": "TODO",
    "priority": "HIGH",
    "due_date": "2024-05-10T12:00:00Z",
    "assignee_id": "uuid"
  }
  ```

**`GET /api/v1/tasks`**
- **Purpose**: List tasks with optional filtering (status, priority, assignee, search, pagination).

**`GET /api/v1/tasks/overdue` & `GET /api/v1/tasks/due-soon`**
- **Purpose**: Polled by **n8n automation** for scheduled reminders and escalation workflows.

## 3. Task Extras (Comments & Attachments)
**`POST /api/v1/tasks/{task_id}/comments`**
- **Purpose**: Add a comment to a task.

**`GET /api/v1/tasks/{task_id}/activity`**
- **Purpose**: Retrieve the system-generated audit log of all changes made to a task (field updates, assignments, status changes).

## 4. Agentic AI Layer (`/api/v1/ai`)
**`POST /api/v1/ai/parse-task`**
- **Purpose**: Natural-language to structured task conversion.
- **Rate Limit**: 10 requests per minute.

**`POST /api/v1/ai/chat`**
- **Purpose**: Conversational interface equipped with task-querying tools.
- **Payload**: `{"message": "What is overdue?"}`
- **Rate Limit**: 20 requests per minute.

## 5. Dashboard (`/api/v1/dashboard`)
**`GET /api/v1/dashboard/stats`**
- **Purpose**: Returns aggregate analytics (tasks by status, priority, overdue count) for the React frontend widgets.
