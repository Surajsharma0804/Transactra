"""
Transactra — MCP Tool Registry Tests

Validates:
- Tool registration and lookup O(1)
- Capability-based access control
- Agent-specific tool listing
- Default registry with 8 tools
- Tool definition immutability

All O(1) — no DB, no network.
"""

from __future__ import annotations

import pytest

from backend.mcp.registry import (
    MCPToolRegistry,
    ToolDefinition,
    ToolParameter,
    create_default_registry,
)


# ═══════════════════════════════════════════════════════
# Registry Operations
# ═══════════════════════════════════════════════════════

class TestRegistry:

    def test_register_and_get(self) -> None:
        registry = MCPToolRegistry()
        tool = ToolDefinition(
            name="test_tool",
            description="A test tool",
            parameters=(),
            required_capabilities=frozenset({"cap_a"}),
        )
        registry.register(tool)
        assert registry.get("test_tool") is tool
        assert registry.tool_count == 1

    def test_get_nonexistent(self) -> None:
        registry = MCPToolRegistry()
        assert registry.get("nope") is None

    def test_duplicate_registration_raises(self) -> None:
        registry = MCPToolRegistry()
        tool = ToolDefinition(
            name="dup", description="x", parameters=(),
            required_capabilities=frozenset(),
        )
        registry.register(tool)
        with pytest.raises(ValueError, match="already registered"):
            registry.register(tool)

    def test_list_tools(self) -> None:
        registry = MCPToolRegistry()
        for i in range(3):
            registry.register(ToolDefinition(
                name=f"tool_{i}", description=f"Tool {i}", parameters=(),
                required_capabilities=frozenset(),
            ))
        assert len(registry.list_tools()) == 3


# ═══════════════════════════════════════════════════════
# Capability Access Control
# ═══════════════════════════════════════════════════════

class TestCapabilityAccess:

    def test_agent_has_access(self) -> None:
        tool = ToolDefinition(
            name="search", description="Search",
            parameters=(), required_capabilities=frozenset({"search"}),
        )
        assert tool.agent_has_access(frozenset({"search", "compare"}))

    def test_agent_lacks_capability(self) -> None:
        tool = ToolDefinition(
            name="authorize", description="Auth",
            parameters=(), required_capabilities=frozenset({"request_authorization"}),
        )
        assert not tool.agent_has_access(frozenset({"search", "compare"}))

    def test_multi_capability_requirement(self) -> None:
        tool = ToolDefinition(
            name="complex", description="Complex",
            parameters=(), required_capabilities=frozenset({"cap_a", "cap_b"}),
        )
        assert tool.agent_has_access(frozenset({"cap_a", "cap_b", "cap_c"}))
        assert not tool.agent_has_access(frozenset({"cap_a"}))

    def test_verify_access_granted(self) -> None:
        registry = MCPToolRegistry()
        registry.register(ToolDefinition(
            name="search", description="Search",
            parameters=(), required_capabilities=frozenset({"search"}),
        ))
        ok, reason = registry.verify_access("search", frozenset({"search"}))
        assert ok
        assert reason == "Access granted"

    def test_verify_access_denied(self) -> None:
        registry = MCPToolRegistry()
        registry.register(ToolDefinition(
            name="auth", description="Auth",
            parameters=(), required_capabilities=frozenset({"authorize"}),
        ))
        ok, reason = registry.verify_access("auth", frozenset({"search"}))
        assert not ok
        assert "Missing" in reason

    def test_verify_unknown_tool(self) -> None:
        registry = MCPToolRegistry()
        ok, reason = registry.verify_access("unknown", frozenset({"search"}))
        assert not ok
        assert "not found" in reason

    def test_list_for_buyer_agent(self) -> None:
        registry = create_default_registry()
        buyer_caps = frozenset({"search", "compare", "negotiate", "propose_cart", "request_authorization", "view_proof"})
        accessible = registry.list_for_agent(buyer_caps)
        names = {t.name for t in accessible}
        assert "search_products" in names
        assert "compare_products" in names
        assert "negotiate_offers" in names
        assert "propose_cart" in names
        assert "request_authorization" in names
        assert "view_proof" in names
        assert "manage_catalog" not in names  # Buyer can't manage catalog

    def test_list_for_merchant_agent(self) -> None:
        registry = create_default_registry()
        merchant_caps = frozenset({"search", "manage_catalog", "manage_policy", "approve_offer", "negotiate"})
        accessible = registry.list_for_agent(merchant_caps)
        names = {t.name for t in accessible}
        assert "manage_catalog" in names
        assert "approve_offer" in names
        assert "request_authorization" not in names  # Merchant can't authorize


# ═══════════════════════════════════════════════════════
# Default Registry
# ═══════════════════════════════════════════════════════

class TestDefaultRegistry:

    def test_has_8_tools(self) -> None:
        registry = create_default_registry()
        assert registry.tool_count == 8

    def test_all_tools_have_capabilities(self) -> None:
        registry = create_default_registry()
        for tool in registry.list_tools():
            assert len(tool.required_capabilities) >= 1

    def test_tool_definitions_frozen(self) -> None:
        registry = create_default_registry()
        tool = registry.get("search_products")
        assert tool is not None
        with pytest.raises(AttributeError):
            tool.name = "hacked"  # type: ignore[misc]
