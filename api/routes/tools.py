"""Dynamic tools routes."""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from shared.database import get_db, DynamicTool

router = APIRouter()


class DynamicToolResponse(BaseModel):
    """Dynamic tool response."""

    id: int
    task_id: str
    tool_name: str
    tool_description: str
    created_at: str
    used_count: int

    class Config:
        from_attributes = True


class CreateToolRequest(BaseModel):
    """Create dynamic tool request."""

    task_id: str
    tool_name: str
    agent_metadata: Dict[str, Any]
    tool_spec: Dict[str, Any]


class ExecuteToolRequest(BaseModel):
    """Execute tool request."""

    parameters: Dict[str, Any]


@router.get("/{tool_id}", response_model=DynamicToolResponse)
async def get_tool(tool_id: int, db: Session = Depends(get_db)):
    """Get dynamic tool by ID."""
    tool = db.query(DynamicTool).filter(DynamicTool.id == tool_id).first()

    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")

    return DynamicToolResponse(
        id=tool.id,
        task_id=tool.task_id,
        tool_name=tool.tool_name,
        tool_description=tool.tool_description,
        created_at=tool.created_at.isoformat(),
        used_count=tool.used_count,
    )


@router.get("/", response_model=List[DynamicToolResponse])
async def list_tools(task_id: Optional[str] = None, db: Session = Depends(get_db)):
    """List dynamic tools."""
    query = db.query(DynamicTool)

    if task_id:
        query = query.filter(DynamicTool.task_id == task_id)

    tools = query.order_by(DynamicTool.created_at.desc()).all()

    return [
        DynamicToolResponse(
            id=tool.id,
            task_id=tool.task_id,
            tool_name=tool.tool_name,
            tool_description=tool.tool_description,
            created_at=tool.created_at.isoformat(),
            used_count=tool.used_count,
        )
        for tool in tools
    ]


@router.post("/")
async def create_tool(request: CreateToolRequest):
    """Create a dynamic tool using meta-tooling."""
    from agents.executor import create_executor_agent

    agent = create_executor_agent()

    prompt = f"""
    Create a dynamic tool with the following specification:

    Task ID: {request.task_id}
    Tool Name: {request.tool_name}
    Agent Metadata: {request.agent_metadata}
    Tool Spec: {request.tool_spec}
    """

    result = await agent.run(prompt)

    return {"message": "Dynamic tool created", "result": result}


@router.post("/{tool_name}/execute")
async def execute_tool(tool_name: str, request: ExecuteToolRequest):
    """Execute a dynamic tool."""
    from agents.executor import create_executor_agent

    agent = create_executor_agent()

    prompt = f"""
    Execute tool: {tool_name}
    Parameters: {request.parameters}
    """

    result = await agent.run(prompt)

    return {"tool_name": tool_name, "result": result}
