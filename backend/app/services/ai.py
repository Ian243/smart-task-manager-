import json
import os
from typing import Optional
from uuid import UUID

import litellm
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.enums import TaskPriority
from app.models.user import User
from app.schemas.ai import (
    ParseTaskResponse,
    SuggestPriorityResponse,
    SummaryResponse,
)
from app.schemas.task import TaskCreate
from app.services import task as task_service
from app.services import dashboard as dashboard_service
from app.services import task_extras

settings = get_settings()

# Setup litellm API keys
os.environ["GEMINI_API_KEY"] = settings.gemini_api_key
os.environ["ANTHROPIC_API_KEY"] = settings.anthropic_api_key


async def parse_task_intent(text: str) -> ParseTaskResponse:
    """Uses LLM to parse a natural language string into a structured task definition."""
    prompt = f"""
    Parse the following natural language task description and extract the title, an optional detailed description, and a priority level (low, medium, or high).
    Return ONLY valid JSON matching this schema:
    {{
        "title": "string",
        "description": "string or null",
        "priority": "low" | "medium" | "high"
    }}

    Input text: {text}
    """
    
    try:
        response = await litellm.acompletion(
            model=settings.llm_model_name,
            fallbacks=["gemini/gemini-1.5-flash", "gemini/gemini-1.5-pro", "gemini/gemini-pro"],
            api_key=settings.gemini_api_key,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        content = response.choices[0].message.content
        data = json.loads(content)
        return ParseTaskResponse(**data)
    except Exception as e:
        print(f"LLM parsing failed: {e}. Falling back to mock data.")
        return ParseTaskResponse(title=f"Parsed: {text[:20]}...", description=text, priority="medium")


async def suggest_priority(title: str, description: Optional[str], due_date: Optional[str]) -> SuggestPriorityResponse:
    """Uses LLM to suggest a priority based on task context."""
    prompt = f"""
    Analyze the following task and suggest a priority (low, medium, high). Provide a brief reasoning.
    Return ONLY valid JSON matching this schema:
    {{
        "suggested_priority": "low" | "medium" | "high",
        "reasoning": "string"
    }}

    Task Title: {title}
    Task Description: {description or 'None'}
    Due Date: {due_date or 'None'}
    """
    
    try:
        response = await litellm.acompletion(
            model=settings.llm_model_name,
            fallbacks=["gemini/gemini-1.5-flash", "gemini/gemini-1.5-pro", "gemini/gemini-pro"],
            api_key=settings.gemini_api_key,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        content = response.choices[0].message.content
        data = json.loads(content)
        return SuggestPriorityResponse(**data)
    except Exception as e:
        print(f"LLM suggestion failed: {e}. Falling back to mock priority.")
        return SuggestPriorityResponse(suggested_priority="medium", reasoning="Fallback due to LLM rate limit.")


async def summarize_task(session: AsyncSession, task_id: UUID) -> SummaryResponse:
    """Fetches task details and uses LLM to generate a concise summary of its status and history."""
    task = await task_service.get_task(session, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    activities = await task_extras.get_activity_log(session, task_id)
    comments = await task_extras.get_comments(session, task_id)
    
    activity_text = "\n".join([f"- {a.created_at}: changed {a.field_changed} from {a.old_value} to {a.new_value}" for a in activities])
    comments_text = "\n".join([f"- {c.created_at}: {c.body}" for c in comments])
    
    prompt = f"""
    Summarize the following task's current status and history into a short, concise paragraph.
    
    Title: {task.title}
    Status: {task.status.value}
    Priority: {task.priority.value}
    
    Activity Log:
    {activity_text}
    
    Comments:
    {comments_text}
    """
    
    try:
        response = await litellm.acompletion(
            model=settings.llm_model_name,
            fallbacks=["gemini/gemini-1.5-flash", "gemini/gemini-1.5-pro", "gemini/gemini-pro"],
            api_key=settings.gemini_api_key,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that summarizes task management tickets."},
                {"role": "user", "content": prompt}
            ]
        )
        content = response.choices[0].message.content
        return SummaryResponse(summary=content)
    except Exception as e:
        print(f"LLM summarization failed: {e}. Falling back to mock summary.")
        return SummaryResponse(summary="This is a fallback summary because the LLM is currently rate limited.")


# For the Chat interface, we would define tools and map them to our python functions.
# To keep this phase clean and simple, we implement a basic RAG/Tool response loop.

# We will define basic tools that the agent can use.
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_task_status",
            "description": "Get the status of a specific task by ID",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {"type": "string", "description": "The UUID of the task"}
                },
                "required": ["task_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_dashboard_summary",
            "description": "Get the current team performance, workload, and analytics summary.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_task",
            "description": "Create a new task and optionally assign it to a team member.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "The title of the task"},
                    "description": {"type": "string", "description": "Detailed description of the task"},
                    "priority": {"type": "string", "description": "Priority: low, medium, or high"},
                    "assignee_name": {"type": "string", "description": "Name or email of the person to assign this task to"}
                },
                "required": ["title", "priority"]
            }
        }
    }
]

async def chat_with_agent(session: AsyncSession, message: str, current_user: User) -> str:
    """
    A simple agent loop that can answer questions or call tools.
    For this phase, it supports a basic 'get_task_status' tool.
    """
    messages = [
        {"role": "system", "content": f"You are a helpful task manager agent. The current user is {current_user.name}."},
        {"role": "user", "content": message}
    ]
    
    try:
        response = await litellm.acompletion(
            model=settings.llm_model_name,
            fallbacks=["gemini/gemini-1.5-flash", "gemini/gemini-1.5-pro", "gemini/gemini-pro"],
            api_key=settings.gemini_api_key,
            messages=messages,
            tools=TOOLS
        )
        
        message_obj = response.choices[0].message
        
        # If the LLM decided to call a tool
        if hasattr(message_obj, "tool_calls") and message_obj.tool_calls:
            for tool_call in message_obj.tool_calls:
                tool_result = ""
                args = json.loads(tool_call.function.arguments) if tool_call.function.arguments else {}
                
                if tool_call.function.name == "get_task_status":
                    task_id_str = args.get("task_id")
                    try:
                        task_id = UUID(task_id_str)
                        task = await task_service.get_task(session, task_id)
                        if task:
                            tool_result = f"Task '{task.title}' is currently {task.status.value}."
                        else:
                            tool_result = "Task not found."
                    except ValueError:
                        tool_result = "Invalid UUID format."
                
                elif tool_call.function.name == "get_dashboard_summary":
                    try:
                        summary = await dashboard_service.get_dashboard_summary(session, current_user)
                        tool_result = summary.model_dump_json()
                    except Exception as e:
                        tool_result = f"Error fetching dashboard summary: {str(e)}"
                        
                elif tool_call.function.name == "create_task":
                    try:
                        from sqlalchemy import select
                        assignee_id = None
                        if args.get("assignee_name"):
                            stmt = select(User).where(
                                (User.name.ilike(f"%{args['assignee_name']}%")) | 
                                (User.email.ilike(f"%{args['assignee_name']}%"))
                            )
                            result = await session.execute(stmt)
                            user_match = result.scalars().first()
                            if user_match:
                                assignee_id = user_match.id
                            else:
                                tool_result = f"Could not find a user matching '{args['assignee_name']}'."
                        
                        if not tool_result:
                            task_in = TaskCreate(
                                title=args.get("title"),
                                description=args.get("description"),
                                priority=args.get("priority", "medium").lower(),
                                assignee_id=assignee_id
                            )
                            new_task = await task_service.create_task(session, task_in, current_user)
                            tool_result = f"Successfully created task '{new_task.title}' with ID {new_task.id}."
                    except Exception as e:
                        tool_result = f"Error creating task: {str(e)}"
                        
                # Send tool result back to LLM
                messages.append(message_obj.model_dump())
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": tool_call.function.name,
                    "content": tool_result
                })
                    
            # Second call to LLM to formulate final response
            final_response = await litellm.acompletion(
                model=settings.llm_model_name,
                fallbacks=["gemini/gemini-1.5-flash", "gemini/gemini-1.5-pro", "gemini/gemini-pro"],
                api_key=settings.gemini_api_key,
                messages=messages
            )
            return final_response.choices[0].message.content
        
        # If no tool was called
        return message_obj.content
        
    except Exception as e:
        print(f"LLM chat failed: {e}. Falling back to mock chat response.")
        return f"Hello! The AI is currently experiencing rate limits or quota exhaustion. Here is a fallback response to your message: '{message}'"
