from __future__ import annotations

from framework.modules.base import BaseModule, ModuleResult
from framework.titan.omega_registry import build_omega_registry


class RtfOsintEngineModule(BaseModule):
    def info(self):
        return {"name": "rtf-osint-engine", "description": "OSINT collection plane aggregating large multi-source evidence.", "author": "OpenAI", "category": "omega", "version": "4.0"}

    def _declare_options(self) -> None:
        self._register_option("operation_id", "Operation identifier", required=False, default="primary")
        self._register_option("include_registry", "Include full OMEGA engine registry", required=False, default=False, type=bool)

    async def run(self) -> ModuleResult:
        registry = build_omega_registry()
        engine = next((item for item in registry["engines"] if item["name"] == "rtf-osint-engine"), {})
        output = {
            "module": "omega/rtf_osint_engine",
            "engine": engine,
            "operation_id": self.get("operation_id"),
            "supports": ["cli_execution", "pipeline_integration", "json_output", "graph_ingestion", "report_generation"],
        }
        if self.get("include_registry"):
            output["registry"] = registry
        return ModuleResult(success=True, output=output)
