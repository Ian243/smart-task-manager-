import json
import os

os.makedirs("n8n/workflows", exist_ok=True)

# Shared HTTP Request properties
http_base = {
    "parameters": {
        "url": "http://api:8000/api/v1/tasks/due-soon",
        "authentication": "genericCredentialType",
        "genericAuthType": "httpHeaderAuth",
        "options": {}
    },
    "name": "HTTP Request",
    "type": "n8n-nodes-base.httpRequest",
    "typeVersion": 3,
    "position": [200, 0],
    "credentials": {
        "httpHeaderAuth": {
            "id": "1",
            "name": "Header Auth"
        }
    }
}

# 1. Due Date Reminders
wf1 = {
  "name": "1. Due Date Reminders",
  "nodes": [
    {
      "parameters": { "rule": { "interval": [{ "field": "cronExpression", "expression": "0 8 * * *" }] } },
      "name": "Schedule Trigger",
      "type": "n8n-nodes-base.scheduleTrigger",
      "typeVersion": 1,
      "position": [0, 0]
    },
    {
      "parameters": {
        "url": "http://api:8000/api/v1/tasks/due-soon",
        "sendHeaders": True,
        "headerParameters": { "parameters": [ { "name": "X-API-Key", "value": "replace-with-a-shared-secret" } ] },
        "options": {}
      },
      "name": "Get Due Tasks",
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 3,
      "position": [200, 0]
    },
    {
      "parameters": { "fieldToSplitOut": "items", "options": {} },
      "name": "Item Lists",
      "type": "n8n-nodes-base.itemLists",
      "typeVersion": 2.1,
      "position": [400, 0]
    },
    {
      "parameters": { "conditions": { "string": [ { "value1": "={{ $json.assignee.email }}", "operation": "isNotEmpty" } ] } },
      "name": "IF Assignee Exists",
      "type": "n8n-nodes-base.if",
      "typeVersion": 1,
      "position": [600, 0]
    },
    {
      "parameters": {
        "sendTo": "={{ $json.assignee.email }}",
        "subject": "=Reminder: Task '{{ $json.title }}' is due soon",
        "message": "=Hi {{ $json.assignee.name }},<br><br>Just a reminder that your task '{{ $json.title }}' is due on {{ $json.due_date }}.<br><br>Priority: {{ $json.priority }}<br><br>Please ensure it is completed on time.<br><br>Best,<br>Smart Task Manager",
        "options": {}
      },
      "name": "Gmail",
      "type": "n8n-nodes-base.gmail",
      "typeVersion": 2.1,
      "position": [800, -100]
    }
  ],
  "connections": {
    "Schedule Trigger": { "main": [ [ { "node": "Get Due Tasks", "type": "main", "index": 0 } ] ] },
    "Get Due Tasks": { "main": [ [ { "node": "Item Lists", "type": "main", "index": 0 } ] ] },
    "Item Lists": { "main": [ [ { "node": "IF Assignee Exists", "type": "main", "index": 0 } ] ] },
    "IF Assignee Exists": { "main": [ [ { "node": "Gmail", "type": "main", "index": 0 } ] ] }
  }
}

with open("n8n/workflows/due_date_reminders.json", "w") as f:
    json.dump(wf1, f, indent=2)

# 2. Assignment / Completion Notifications
wf2 = {
  "name": "2. Assignment & Completion Notifications",
  "nodes": [
    {
      "parameters": {
        "httpMethod": "POST",
        "path": "task-events",
        "options": {}
      },
      "name": "Webhook",
      "type": "n8n-nodes-base.webhook",
      "typeVersion": 1,
      "position": [0, 0]
    },
    {
      "parameters": {
        "url": "=http://api:8000/api/v1/tasks/{{ $json.body.task_id }}",
        "sendHeaders": True,
        "headerParameters": { "parameters": [ { "name": "X-API-Key", "value": "replace-with-a-shared-secret" } ] },
        "options": {}
      },
      "name": "Get Task Details",
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 3,
      "position": [200, 0]
    },
    {
      "parameters": {
        "conditions": {
          "string": [
            { "value1": "={{ $('Webhook').item.json.body.event }}", "operation": "equals", "value2": "ASSIGNED" },
            { "value1": "={{ $('Webhook').item.json.body.event }}", "operation": "equals", "value2": "COMPLETED" }
          ]
        }
      },
      "name": "Switch by Event",
      "type": "n8n-nodes-base.switch",
      "typeVersion": 1,
      "position": [400, 0]
    },
    {
      "parameters": {
        "sendTo": "={{ $json.assignee.email }}",
        "subject": "=New Task Assigned: {{ $json.title }}",
        "message": "=Hi {{ $json.assignee.name }},<br><br>You have been assigned to a new task '{{ $json.title }}'.<br><br>Due Date: {{ $json.due_date }}<br><br>Best,<br>Smart Task Manager",
        "options": {}
      },
      "name": "Gmail (Assigned)",
      "type": "n8n-nodes-base.gmail",
      "typeVersion": 2.1,
      "position": [600, -100]
    },
    {
      "parameters": {
        "sendTo": "={{ $json.assignee.email }}",
        "subject": "=Task Completed: {{ $json.title }}",
        "message": "=Hi {{ $json.assignee.name }},<br><br>Your task '{{ $json.title }}' has been marked as completed. Great job!<br><br>Best,<br>Smart Task Manager",
        "options": {}
      },
      "name": "Gmail (Completed)",
      "type": "n8n-nodes-base.gmail",
      "typeVersion": 2.1,
      "position": [600, 100]
    }
  ],
  "connections": {
    "Webhook": { "main": [ [ { "node": "Get Task Details", "type": "main", "index": 0 } ] ] },
    "Get Task Details": { "main": [ [ { "node": "Switch by Event", "type": "main", "index": 0 } ] ] },
    "Switch by Event": {
      "main": [
        [ { "node": "Gmail (Assigned)", "type": "main", "index": 0 } ],
        [ { "node": "Gmail (Completed)", "type": "main", "index": 0 } ]
      ]
    }
  }
}

with open("n8n/workflows/assignment_notifications.json", "w") as f:
    json.dump(wf2, f, indent=2)

# 3. Recurring Task Generation
wf3 = {
  "name": "3. Recurring Task Generation",
  "nodes": [
    {
      "parameters": { "rule": { "interval": [{ "field": "cronExpression", "expression": "0 0 * * *" }] } },
      "name": "Schedule Trigger",
      "type": "n8n-nodes-base.scheduleTrigger",
      "typeVersion": 1,
      "position": [0, 0]
    },
    {
      "parameters": {
        "method": "POST",
        "url": "http://api:8000/api/v1/recurring/generate",
        "sendHeaders": True,
        "headerParameters": { "parameters": [ { "name": "X-API-Key", "value": "replace-with-a-shared-secret" } ] },
        "options": {}
      },
      "name": "Generate Tasks",
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 3,
      "position": [200, 0]
    },
    {
      "parameters": { "fieldToSplitOut": "body", "options": {} },
      "name": "Item Lists",
      "type": "n8n-nodes-base.itemLists",
      "typeVersion": 2.1,
      "position": [400, 0]
    },
    {
      "parameters": {
        "sendTo": "={{ $json.assignee.email }}",
        "subject": "=Recurring Task Generated: {{ $json.title }}",
        "message": "=Hi {{ $json.assignee.name }},<br><br>A new recurring task '{{ $json.title }}' has been generated for you.<br><br>Best,<br>Smart Task Manager",
        "options": {}
      },
      "name": "Gmail",
      "type": "n8n-nodes-base.gmail",
      "typeVersion": 2.1,
      "position": [600, 0]
    }
  ],
  "connections": {
    "Schedule Trigger": { "main": [ [ { "node": "Generate Tasks", "type": "main", "index": 0 } ] ] },
    "Generate Tasks": { "main": [ [ { "node": "Item Lists", "type": "main", "index": 0 } ] ] },
    "Item Lists": { "main": [ [ { "node": "Gmail", "type": "main", "index": 0 } ] ] }
  }
}

with open("n8n/workflows/recurring_task_generation.json", "w") as f:
    json.dump(wf3, f, indent=2)

# 4. Overdue Escalation
wf4 = {
  "name": "4. Overdue Escalation",
  "nodes": [
    {
      "parameters": { "rule": { "interval": [{ "field": "cronExpression", "expression": "0 9 * * *" }] } },
      "name": "Schedule Trigger",
      "type": "n8n-nodes-base.scheduleTrigger",
      "typeVersion": 1,
      "position": [0, 0]
    },
    {
      "parameters": {
        "url": "http://api:8000/api/v1/tasks/overdue",
        "sendHeaders": True,
        "headerParameters": { "parameters": [ { "name": "X-API-Key", "value": "replace-with-a-shared-secret" } ] },
        "options": {}
      },
      "name": "Get Overdue Tasks",
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 3,
      "position": [200, 0]
    },
    {
      "parameters": { "fieldToSplitOut": "items", "options": {} },
      "name": "Item Lists",
      "type": "n8n-nodes-base.itemLists",
      "typeVersion": 2.1,
      "position": [400, 0]
    },
    {
      "parameters": {
        "sendTo": "={{ $json.assignee.email }}",
        "subject": "=Action Required! Task Overdue: {{ $json.title }}",
        "message": "=Hi {{ $json.assignee.name }},<br><br>The task '{{ $json.title }}' is OVERDUE.<br><br>It was due on {{ $json.due_date }}. Please complete it immediately or update its status.<br><br>Best,<br>Smart Task Manager",
        "options": {}
      },
      "name": "Gmail",
      "type": "n8n-nodes-base.gmail",
      "typeVersion": 2.1,
      "position": [600, 0]
    }
  ],
  "connections": {
    "Schedule Trigger": { "main": [ [ { "node": "Get Overdue Tasks", "type": "main", "index": 0 } ] ] },
    "Get Overdue Tasks": { "main": [ [ { "node": "Item Lists", "type": "main", "index": 0 } ] ] },
    "Item Lists": { "main": [ [ { "node": "Gmail", "type": "main", "index": 0 } ] ] }
  }
}

with open("n8n/workflows/overdue_escalation.json", "w") as f:
    json.dump(wf4, f, indent=2)

print("Created 4 workflow JSON files successfully.")
