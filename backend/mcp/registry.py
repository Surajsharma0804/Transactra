"""
Transactra — MCP Tool Registry

Model Context Protocol tool definitions for AI agents.
Each tool maps to a specific capability requirement.

AP2 Alignment:
- search → Capability.SEARCH
- compare → Capability.COMPARE
- negotiate → Capability.NEGOTIATE
- propose_cart → Capability.PROPOSE_CART
- request_authorization → Capability.REQUEST_AUTHORIZATION
- view_proof → Capability.VIEW_PROOF

Security:
- Every tool invocation requires capability verification O(1)
- Tool execution is bounded (max results, timeouts)
- No tool can bypass the authorization gate

Complexity:
- Tool lookup: O(1) dict-based registry
- Capability check: O(1) frozenset membership
- Registration: O(1)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Awaitable
from uuid import UUID


@dataclass(frozen=True, slots=True)
class ToolParameter:
    """Schema for a tool parameter."""
    name: str
    type: str  # "string", "integer", "boolean", "object", "array"
    description: str
    required: bool = True
    default: Any = None
    enum: list[str] | None = None
    min_value: int | None = None
    max_value: int | None = None


@dataclass(frozen=True, slots=True)
class ToolDefinition:
    """
    MCP tool definition with capability binding.

    Each tool requires specific capabilities from the calling agent.
    The capability check is O(1) via frozenset membership.
    """
    name: str
    description: str
    parameters: tuple[ToolParameter, ...]
    required_capabilities: frozenset[str]
    max_results: int = 50
    timeout_seconds: int = 30
    idempotent: bool = False
    destructive: bool = False

    def agent_has_access(self, agent_capabilities: frozenset[str]) -> bool:
        """
        Check if agent has all required capabilities.
        O(k) where k = len(required_capabilities).
        """
        return self.required_capabilities.issubset(agent_capabilities)


@dataclass(frozen=True, slots=True)
class ToolInvocation:
    """Record of a tool invocation for audit."""
    tool_name: str
    agent_id: UUID
    parameters: dict[str, Any]
    capability_check_passed: bool
    result_status: str = "pending"
    error: str | None = None


class MCPToolRegistry:
    """
    Registry of all available MCP tools.

    Lookup: O(1) dict-based.
    Registration: O(1).
    Capability verification: O(k) per check.
    """

    def __init__(self) -> None:
        self._tools: dict[str, ToolDefinition] = {}

    def register(self, tool: ToolDefinition) -> None:
        """Register a tool. O(1)."""
        if tool.name in self._tools:
            raise ValueError(f"Tool already registered: {tool.name}")
        self._tools[tool.name] = tool

    def get(self, name: str) -> ToolDefinition | None:
        """Get tool by name. O(1)."""
        return self._tools.get(name)

    def list_tools(self) -> list[ToolDefinition]:
        """List all registered tools. O(n)."""
        return list(self._tools.values())

    def list_for_agent(self, agent_capabilities: frozenset[str]) -> list[ToolDefinition]:
        """
        List tools accessible to an agent based on capabilities.
        O(n · k) where n = tools, k = max capabilities per tool.
        """
        return [
            tool for tool in self._tools.values()
            if tool.agent_has_access(agent_capabilities)
        ]

    def verify_access(
        self, tool_name: str, agent_capabilities: frozenset[str]
    ) -> tuple[bool, str]:
        """
        Verify agent access to a tool. O(1) lookup + O(k) check.
        Returns (allowed, reason).
        """
        tool = self._tools.get(tool_name)
        if tool is None:
            return False, f"Tool not found: {tool_name}"
        if not tool.agent_has_access(agent_capabilities):
            missing = tool.required_capabilities - agent_capabilities
            return False, f"Missing capabilities: {missing}"
        return True, "Access granted"

    @property
    def tool_count(self) -> int:
        """Number of registered tools. O(1)."""
        return len(self._tools)


# ═══════════════════════════════════════════════════════
# Default Tool Definitions
# ═══════════════════════════════════════════════════════

def create_default_registry() -> MCPToolRegistry:
    """
    Create the default MCP tool registry with all Transactra tools.

    AP2 alignment: each tool maps to a specific agent capability.
    """
    registry = MCPToolRegistry()

    registry.register(ToolDefinition(
        name="search_products",
        description="Search the product catalog with filters and natural language query",
        parameters=(
            ToolParameter("query", "string", "Natural language search query", required=False),
            ToolParameter("categories", "array", "Category filter", required=False),
            ToolParameter("max_price_paise", "integer", "Maximum price in paise", required=False),
            ToolParameter("min_price_paise", "integer", "Minimum price in paise", required=False),
            ToolParameter("in_stock_only", "boolean", "Only show in-stock items", required=False, default=True),
            ToolParameter("limit", "integer", "Max results", required=False, default=20, min_value=1, max_value=100),
        ),
        required_capabilities=frozenset({"search"}),
        max_results=100,
        idempotent=True,
    ))

    registry.register(ToolDefinition(
        name="compare_products",
        description="Compare multiple products side-by-side on price, warranty, shipping",
        parameters=(
            ToolParameter("product_ids", "array", "List of product IDs to compare"),
        ),
        required_capabilities=frozenset({"compare"}),
        max_results=10,
        idempotent=True,
    ))

    registry.register(ToolDefinition(
        name="negotiate_offers",
        description="Start or continue a negotiation session with merchant agents",
        parameters=(
            ToolParameter("product_id", "string", "Product to negotiate for"),
            ToolParameter("max_total_paise", "integer", "Maximum acceptable total in paise"),
            ToolParameter("quantity", "integer", "Desired quantity", required=False, default=1),
        ),
        required_capabilities=frozenset({"negotiate"}),
        timeout_seconds=120,
    ))

    registry.register(ToolDefinition(
        name="propose_cart",
        description="Create a priced cart from selected products",
        parameters=(
            ToolParameter("items", "array", "List of {product_id, quantity} objects"),
        ),
        required_capabilities=frozenset({"propose_cart"}),
        destructive=True,
    ))

    registry.register(ToolDefinition(
        name="request_authorization",
        description="Submit cart for authorization through the 16-predicate gate",
        parameters=(
            ToolParameter("cart_id", "string", "Cart ID to authorize"),
            ToolParameter("mandate_id", "string", "Mandate ID to use"),
            ToolParameter("consent_id", "string", "Consent ID to consume"),
        ),
        required_capabilities=frozenset({"request_authorization"}),
        destructive=True,
    ))

    registry.register(ToolDefinition(
        name="view_proof",
        description="View the evidence chain and authorization proof for a transaction",
        parameters=(
            ToolParameter("order_id", "string", "Order ID to view proof for"),
        ),
        required_capabilities=frozenset({"view_proof"}),
        idempotent=True,
    ))

    registry.register(ToolDefinition(
        name="manage_catalog",
        description="Add, update, or remove products from merchant catalog",
        parameters=(
            ToolParameter("action", "string", "Action: add, update, remove", enum=["add", "update", "remove"]),
            ToolParameter("product_data", "object", "Product data object"),
        ),
        required_capabilities=frozenset({"manage_catalog"}),
        destructive=True,
    ))

    registry.register(ToolDefinition(
        name="approve_offer",
        description="Approve or reject a negotiation offer from buyer",
        parameters=(
            ToolParameter("negotiation_id", "string", "Negotiation session ID"),
            ToolParameter("offer_id", "string", "Offer ID to approve/reject"),
            ToolParameter("approved", "boolean", "Whether to approve"),
            ToolParameter("counter_price_paise", "integer", "Counter-offer price", required=False),
        ),
        required_capabilities=frozenset({"approve_offer"}),
    ))

    return registry
