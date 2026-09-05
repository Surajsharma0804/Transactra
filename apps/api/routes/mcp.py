"""
Transactra — MCP Tools API Route

Exposes the MCP tool registry for AI agents.
- GET  /mcp/tools — List tools available to an agent
- POST /mcp/tools/{name}/invoke — Invoke a tool (with capability check)
"""

from __future__ import annotations

from typing import Any
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.mcp.registry import create_default_registry

router = APIRouter(prefix="/mcp", tags=["mcp"])

_registry = create_default_registry()


class ToolInfo(BaseModel):
    name: str
    description: str
    required_capabilities: list[str]
    max_results: int
    timeout_seconds: int
    idempotent: bool
    destructive: bool
    parameters: list[dict[str, Any]]


class ToolListResponse(BaseModel):
    tools: list[ToolInfo]
    total: int
    agent_capabilities: list[str]


class InvokeRequest(BaseModel):
    agent_id: UUID
    agent_capabilities: list[str]
    parameters: dict[str, Any] = Field(default_factory=dict)


class InvokeResponse(BaseModel):
    invocation_id: UUID
    tool_name: str
    capability_check_passed: bool
    result_status: str
    error: str | None = None


@router.get("/tools", response_model=ToolListResponse)
async def list_tools(capabilities: str = "") -> ToolListResponse:
    """
    List MCP tools available to an agent with given capabilities.

    Pass capabilities as comma-separated string: ?capabilities=search,compare

    Complexity: O(n · k) where n = tools, k = capabilities.
    """
    caps = frozenset(c.strip() for c in capabilities.split(",") if c.strip()) if capabilities else frozenset()

    if caps:
        tools = _registry.list_for_agent(caps)
    else:
        tools = _registry.list_tools()

    return ToolListResponse(
        tools=[
            ToolInfo(
                name=t.name,
                description=t.description,
                required_capabilities=sorted(t.required_capabilities),
                max_results=t.max_results,
                timeout_seconds=t.timeout_seconds,
                idempotent=t.idempotent,
                destructive=t.destructive,
                parameters=[
                    {"name": p.name, "type": p.type, "description": p.description,
                     "required": p.required}
                    for p in t.parameters
                ],
            )
            for t in tools
        ],
        total=len(tools),
        agent_capabilities=sorted(caps),
    )


@router.post("/tools/{tool_name}/invoke", response_model=InvokeResponse)
async def invoke_tool(tool_name: str, req: InvokeRequest) -> InvokeResponse:
    """
    Invoke an MCP tool with capability verification.

    The agent must have all required capabilities for the tool.
    Failed capability checks are logged but return a structured error.

    Complexity: O(1) lookup + O(k) capability check.
    """
    caps = frozenset(req.agent_capabilities)
    allowed, reason = _registry.verify_access(tool_name, caps)

    invocation_id = uuid4()

    if not allowed:
        return InvokeResponse(
            invocation_id=invocation_id,
            tool_name=tool_name,
            capability_check_passed=False,
            result_status="denied",
            error=reason,
        )

    # In production, this dispatches to the actual tool implementation
    return InvokeResponse(
        invocation_id=invocation_id,
        tool_name=tool_name,
        capability_check_passed=True,
        result_status="success",
        error=None,
    )
