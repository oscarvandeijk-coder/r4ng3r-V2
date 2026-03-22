from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List


@dataclass
class TitanService:
    name: str
    purpose: str
    dependencies: List[str] = field(default_factory=list)
    interfaces: List[str] = field(default_factory=list)
    pipelines: List[str] = field(default_factory=list)


@dataclass
class TitanInfrastructure:
    message_bus: str = "RabbitMQ"
    cache: str = "Redis"
    graph_db: str = "Neo4j"
    search: str = "ElasticSearch"
    object_store: str = "MinIO"
    api: str = "FastAPI"
    metrics: List[str] = field(default_factory=lambda: ["Prometheus", "Grafana"])
    orchestrators: List[str] = field(default_factory=lambda: ["Docker", "Kubernetes"])


class TitanArchitecture:
    def __init__(self) -> None:
        self.infrastructure = TitanInfrastructure()
        self.services: List[TitanService] = [
            TitanService("rtf-core", "Shared config, auth, registry, orchestration entrypoint", ["Redis", "RabbitMQ"], ["cli", "api"], ["core_orchestration"]),
            TitanService("rtf-osint-engine", "Large-scale OSINT collection and normalization", ["rtf-core", "rtf-ingestion-engine"], ["queue:osint"], ["osint", "multi_search"]),
            TitanService("rtf-socmint-engine", "15-stage SOCMINT pipeline execution", ["rtf-osint-engine", "rtf-ai-engine", "rtf-graph-engine"], ["queue:socmint"], ["socmint"]),
            TitanService("rtf-casm-engine", "Continuous attack surface management", ["rtf-core", "rtf-report-engine"], ["queue:casm"], ["casm"]),
            TitanService("rtf-credential-engine", "Breach intel and distributed cracking coordination", ["rtf-core", "rtf-worker-cluster"], ["queue:credential"], ["credential_intel", "hashcat_cluster"]),
            TitanService("rtf-graph-engine", "Knowledge graph ingestion and relationship queries", ["Neo4j", "rtf-ingestion-engine"], ["queue:graph"], ["entity_correlation"]),
            TitanService("rtf-ai-engine", "Identity resolution, summarization, risk scoring", ["rtf-graph-engine", "rtf-core"], ["queue:ai"], ["identity_resolution", "ai_summary"]),
            TitanService("rtf-scraper-engine", "Search and social scraping with proxy rotation", ["rtf-osint-engine"], ["queue:scrape"], ["search_scraping", "social_scraping"]),
            TitanService("rtf-wireless-engine", "RF capture and wireless analysis coordination", ["rtf-core", "rtf-ingestion-engine"], ["queue:wireless"], ["sdr_intel"]),
            TitanService("rtf-worker-cluster", "Distributed worker execution for compute-heavy jobs", ["RabbitMQ", "Redis"], ["queue:worker"], ["parallel_jobs"]),
            TitanService("rtf-report-engine", "HTML, PDF, JSON, Markdown, XLSX report generation", ["rtf-graph-engine", "rtf-ai-engine"], ["queue:report"], ["reporting"]),
            TitanService("rtf-ingestion-engine", "Normalizes evidence into events, entities, and artifacts", ["MinIO", "ElasticSearch", "Neo4j"], ["queue:ingestion"], ["normalization"]),
            TitanService("rtf-automation-engine", "Workflow builder and template automation", ["rtf-core", "rtf-worker-cluster"], ["queue:automation"], ["workflow_builder"]),
            TitanService("rtf-monitoring-engine", "Telemetry, metrics, and health aggregation", ["Prometheus", "Grafana"], ["queue:metrics"], ["observability"]),
        ]

    def dependency_map(self) -> Dict[str, List[str]]:
        return {service.name: list(service.dependencies) for service in self.services}

    def extension_points(self) -> Dict[str, List[str]]:
        return {
            "cli": ["Add titan subcommands without impacting legacy commands"],
            "api": ["Expose distributed service topology and queue status endpoints"],
            "dashboard": ["Add graph explorer, pipeline monitor, and service health cards"],
            "workflow_engine": ["Register TITAN pipelines through the existing workflow registry"],
            "module_system": ["Wrap external tools with universal TITAN wrappers"],
            "reporting": ["Feed graph, AI, and evidence timelines into existing reporting engine"],
            "scheduler": ["Bridge local async jobs to queue-backed worker execution"],
            "configuration": ["Layer service topology and queue settings over current YAML/env config"],
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": "RTF TITAN",
            "infrastructure": asdict(self.infrastructure),
            "services": [asdict(service) for service in self.services],
            "dependency_map": self.dependency_map(),
            "extension_points": self.extension_points(),
        }


def build_titan_manifest() -> Dict[str, Any]:
    return TitanArchitecture().to_dict()
