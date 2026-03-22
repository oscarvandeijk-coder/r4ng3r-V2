from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from framework.titan import build_titan_manifest
from framework.titan.wrappers import StaticToolCatalog


@dataclass
class OmegaEngine:
    name: str
    purpose: str
    loader_path: str
    pipelines: List[str] = field(default_factory=list)
    interfaces: List[str] = field(default_factory=list)
    storage: List[str] = field(default_factory=list)
    categories: List[str] = field(default_factory=list)
    enabled: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "purpose": self.purpose,
            "loader_path": self.loader_path,
            "pipelines": list(self.pipelines),
            "interfaces": list(self.interfaces),
            "storage": list(self.storage),
            "categories": list(self.categories),
            "enabled": self.enabled,
        }


class OmegaEngineRegistry:
    """Compatibility-preserving service registry for Omega-Black engines."""

    def __init__(self) -> None:
        manifest = build_titan_manifest()
        self._engines: Dict[str, OmegaEngine] = {}
        category_map = {
            "rtf-core": ["core", "compatibility", "scheduler"],
            "rtf-osint-engine": ["osint", "username", "email", "phone", "domain"],
            "rtf-socmint-engine": ["socmint", "social", "recursive-pivoting"],
            "rtf-breach-engine": ["breach", "credential", "email"],
            "rtf-scraper-engine": ["search", "scraping", "metadata"],
            "rtf-casm-engine": ["recon", "casm", "surface-management"],
            "rtf-graph-engine": ["graph", "neo4j", "correlation"],
            "rtf-ai-engine": ["ai", "resolution", "scoring"],
            "rtf-credential-engine": ["credential", "vault", "replay"],
            "rtf-report-engine": ["reporting", "timeline", "artifact-rendering"],
            "rtf-monitoring-engine": ["monitoring", "health", "telemetry"],
            "rtf-automation-engine": ["automation", "workflow", "scheduler"],
            "rtf-worker-cluster": ["parallelism", "distributed-jobs", "fanout"],
        }
        loader_map = {
            "rtf-core": "framework.core",
            "rtf-osint-engine": "framework.modules.osint",
            "rtf-socmint-engine": "framework.titan.socmint_pipeline",
            "rtf-breach-engine": "framework.modules.osint.breach_correlation",
            "rtf-scraper-engine": "framework.modules.osint.web_search_scraper",
            "rtf-casm-engine": "framework.modules.recon.casm_pipeline",
            "rtf-graph-engine": "framework.titan.knowledge_graph",
            "rtf-ai-engine": "framework.ai.autonomous_agent",
            "rtf-credential-engine": "framework.modules.post_exploitation.credential_intelligence",
            "rtf-report-engine": "framework.reporting.engine",
            "rtf-monitoring-engine": "framework.scheduler.scheduler",
            "rtf-automation-engine": "framework.automation.pipeline_v2",
            "rtf-worker-cluster": "framework.titan.distributed",
        }

        for service in manifest["services"]:
            self._engines[service["name"]] = OmegaEngine(
                name=service["name"],
                purpose=service["purpose"],
                loader_path=loader_map.get(service["name"], "framework.titan"),
                pipelines=list(service.get("pipelines", [])),
                interfaces=list(service.get("interfaces", [])),
                storage=list(service.get("storage", [])),
                categories=category_map.get(service["name"], []),
            )

        if "rtf-breach-engine" not in self._engines:
            self._engines["rtf-breach-engine"] = OmegaEngine(
                name="rtf-breach-engine",
                purpose="Breach intelligence fusion, leak normalization, and credential exposure correlation.",
                loader_path="framework.modules.osint.breach_correlation",
                pipelines=["breach_intel", "credential_exposure"],
                interfaces=["queue:breach", "api"],
                storage=["ElasticSearch", "MinIO", "Neo4j"],
                categories=["breach", "credential", "identity"],
            )

    def list_engines(self) -> List[Dict[str, Any]]:
        return [engine.to_dict() for engine in sorted(self._engines.values(), key=lambda item: item.name)]

    def get(self, name: str) -> Dict[str, Any]:
        return self._engines[name].to_dict()

    def module_loader_extensions(self) -> List[Dict[str, Any]]:
        return [
            {
                "engine": engine.name,
                "module_prefix": engine.categories[0] if engine.categories else "generic",
                "loader_path": engine.loader_path,
                "integration_mode": "existing-module-loader-compatible",
            }
            for engine in self._engines.values()
        ]

    def summary(self) -> Dict[str, Any]:
        return {
            "engine_count": len(self._engines),
            "engines": self.list_engines(),
            "module_loader_extensions": self.module_loader_extensions(),
            "tool_families": {
                "username_discovery": len(StaticToolCatalog.USERNAME_DISCOVERY),
                "social_scrapers": len(StaticToolCatalog.SOCIAL_SCRAPERS),
                "search_engines": len(StaticToolCatalog.SEARCH_ENGINES),
                "email_breach": len(StaticToolCatalog.EMAIL_BREACH),
                "domain_intel": len(StaticToolCatalog.DOMAIN_INTEL),
                "code_intel": len(StaticToolCatalog.CODE_INTEL),
            },
        }


omega_engine_registry = OmegaEngineRegistry()
