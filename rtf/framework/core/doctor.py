from __future__ import annotations

from typing import Any, Dict, List

from framework.modules.loader import ModuleLoader
from framework.registry.tool_registry import ToolRegistry
from framework.titan import TitanKnowledgeGraph
from framework.titan.omega_registry import build_omega_registry, build_self_healing_actions


class OmegaDoctor:
    def __init__(self) -> None:
        self.registry = ToolRegistry()
        self.loader = ModuleLoader()

    def run(self, action: str) -> Dict[str, Any]:
        omega = build_omega_registry()
        self.registry.refresh()
        self.loader.load_all()
        modules = self.loader.list_modules(category="omega")
        graph_schema = TitanKnowledgeGraph().schema()
        checks: List[Dict[str, Any]] = [
            {
                "name": "module_loader",
                "success": len(modules) >= len(omega["engines"]),
                "details": {"omega_modules": len(modules), "required_engines": len(omega["engines"])}
            },
            {
                "name": "tool_registry",
                "success": self.registry.summary()["total_tools"] > 0,
                "details": self.registry.summary(),
            },
            {
                "name": "graph_schema",
                "success": "Person" in graph_schema["entity_types"] and "USES_EMAIL" in graph_schema["relationship_types"],
                "details": graph_schema,
            },
            {
                "name": "source_registry",
                "success": omega["source_capacity"]["estimated_total_sources"] >= 1000,
                "details": omega["source_capacity"],
            },
        ]
        requested = build_self_healing_actions().get(action, {"purpose": "Unknown action", "checks": []})
        return {
            "action": action,
            "purpose": requested["purpose"],
            "requested_checks": requested["checks"],
            "success": all(item["success"] for item in checks),
            "checks": checks,
            "repair_plan": self._repair_plan(action, checks),
        }

    @staticmethod
    def _repair_plan(action: str, checks: List[Dict[str, Any]]) -> List[str]:
        plan: List[str] = []
        if not next((c for c in checks if c["name"] == "module_loader"), {}).get("success", False):
            plan.append("Reload module registry and verify OMEGA engine modules are importable.")
        if not next((c for c in checks if c["name"] == "source_registry"), {}).get("success", False):
            plan.append("Expand source registry weights until aggregate source capacity exceeds 1000.")
        if action in {"fix", "repair"}:
            plan.append("Refresh tool registry and regenerate workflow metadata for automation-safe defaults.")
        if action == "validate":
            plan.append("Validate graph schema, module metadata, and pipeline contracts before release.")
        if action == "upgrade":
            plan.append("Regenerate the OMEGA-BLACK upgrade report and service manifest artifacts.")
        return plan
