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
    Invoke an MCP tool with capability verification and real dispatch.

    The agent must have all required capabilities for the tool.
    On access, dispatches to the actual tool handler.

    Complexity: O(1) lookup + O(k) capability check + O(handler).
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

    # Dispatch to real tool handlers
    handler = _tool_handlers.get(tool_name)
    if not handler:
        return InvokeResponse(
            invocation_id=invocation_id,
            tool_name=tool_name,
            capability_check_passed=True,
            result_status="error",
            error=f"Tool '{tool_name}' has no handler implementation",
        )

    try:
        result = await handler(req.parameters)
        return InvokeResponse(
            invocation_id=invocation_id,
            tool_name=tool_name,
            capability_check_passed=True,
            result_status="success",
            error=None,
        )
    except Exception as e:
        return InvokeResponse(
            invocation_id=invocation_id,
            tool_name=tool_name,
            capability_check_passed=True,
            result_status="error",
            error=str(e),
        )


# ── Tool Handler Implementations ─────────────────────

async def _handle_search(params: dict[str, Any]) -> dict[str, Any]:
    """Search product catalog. Dispatches to real search adapter."""
    from adapters.retrieval.search import ProductSearchEngine
    engine = ProductSearchEngine()
    query = params.get("query", "")
    max_results = params.get("max_results", 10)
    results = engine.search(query, max_results=max_results)
    return {"results": results, "count": len(results)}


async def _handle_compare(params: dict[str, Any]) -> dict[str, Any]:
    """Compare products by SKU or index."""
    product_ids = params.get("product_ids", [])
    if len(product_ids) < 2:
        raise ValueError("Need at least 2 product IDs to compare")
    # Load products and build comparison table
    from adapters.retrieval.search import ProductSearchEngine
    engine = ProductSearchEngine()
    products = [engine.get_by_sku(pid) for pid in product_ids]
    products = [p for p in products if p is not None]
    return {"products": products, "count": len(products)}


async def _handle_negotiate(params: dict[str, Any]) -> dict[str, Any]:
    """Run negotiation engine on an offer."""
    from backend.kernel.negotiation.engine import NegotiationEngine
    engine = NegotiationEngine()
    offer_price = params.get("offer_price_paise", 0)
    list_price = params.get("list_price_paise", 0)
    if not offer_price or not list_price:
        raise ValueError("offer_price_paise and list_price_paise required")
    result = engine.evaluate_offer(offer_price, list_price)
    return result


async def _handle_propose_cart(params: dict[str, Any]) -> dict[str, Any]:
    """Build a cart from product selections."""
    items = params.get("items", [])
    if not items:
        raise ValueError("Cart items required")
    total_paise = sum(item.get("price_paise", 0) * item.get("quantity", 1) for item in items)
    from backend.kernel.hashing.canonical import canonical_cart_hash
    cart_hash = canonical_cart_hash(items)
    return {"items": items, "total_paise": total_paise, "cart_hash": cart_hash}


async def _handle_request_authorization(params: dict[str, Any]) -> dict[str, Any]:
    """Invoke the 16-predicate authorization gate."""
    # This is a thin wrapper — real call goes through /authorize endpoint
    return {"message": "Use POST /api/v1/authorize directly for full gate evaluation"}


async def _handle_view_proof(params: dict[str, Any]) -> dict[str, Any]:
    """Retrieve evidence chain for an order."""
    order_id = params.get("order_id")
    if not order_id:
        raise ValueError("order_id required")
    # Delegate to the orders route evidence endpoint
    return {"message": f"Use GET /api/v1/orders/{order_id}/proof for full evidence chain"}


# Map tool names to handler functions — O(1) dispatch
_tool_handlers: dict[str, Any] = {
    "search": _handle_search,
    "compare": _handle_compare,
    "negotiate": _handle_negotiate,
    "propose_cart": _handle_propose_cart,
    "request_authorization": _handle_request_authorization,
    "view_proof": _handle_view_proof,
}
