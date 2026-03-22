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
    storage: List[str] = field(default_factory=list)
    scalability: str = "horizontal"


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
            TitanService("rtf-core", "Shared config, auth, registry, orchestration entrypoint", ["Redis", "RabbitMQ"], ["cli", "api", "scheduler"], ["core_orchestration", "legacy_compatibility"], ["Redis"]),
            TitanService("rtf-osint-engine", "Large-scale OSINT collection and normalization", ["rtf-core", "rtf-ingestion-engine"], ["queue:osint", "http"], ["osint", "multi_search", "artifact_enrichment"], ["ElasticSearch", "MinIO"]),
            TitanService("rtf-socmint-engine", "15-stage SOCMINT pipeline execution", ["rtf-osint-engine", "rtf-ai-engine", "rtf-graph-engine"], ["queue:socmint"], ["socmint", "identity_resolution", "recursive_pivoting"], ["Neo4j", "ElasticSearch"]),
            TitanService("rtf-breach-engine", "Breach intelligence ingestion, credential exposure analysis, and leak correlation", ["rtf-osint-engine", "rtf-credential-engine", "rtf-graph-engine"], ["queue:breach"], ["breach_intelligence", "credential_exposure", "leak_monitoring"], ["ElasticSearch", "MinIO", "Neo4j"]),
            TitanService("rtf-casm-engine", "Continuous attack surface management", ["rtf-core", "rtf-report-engine"], ["queue:casm"], ["casm", "external_surface_monitoring"], ["ElasticSearch"]),
            TitanService("rtf-credential-engine", "Breach intel and distributed cracking coordination", ["rtf-core", "rtf-worker-cluster"], ["queue:credential"], ["credential_intel", "hashcat_cluster", "breach_correlation"], ["MinIO", "ElasticSearch"]),
            TitanService("rtf-graph-engine", "Knowledge graph ingestion and relationship queries", ["Neo4j", "rtf-ingestion-engine"], ["queue:graph", "bolt"], ["entity_correlation", "graph_materialization"], ["Neo4j"]),
            TitanService("rtf-ai-engine", "Identity resolution, summarization, stylometry, and risk scoring", ["rtf-graph-engine", "rtf-core"], ["queue:ai"], ["identity_resolution", "ai_summary", "profile_clustering"], ["Redis", "MinIO"]),
            TitanService("rtf-scraper-engine", "Search and social scraping with proxy rotation", ["rtf-osint-engine"], ["queue:scrape"], ["search_scraping", "social_scraping", "metadata_collection"], ["MinIO"]),
            TitanService("rtf-wireless-engine", "RF capture and wireless analysis coordination", ["rtf-core", "rtf-ingestion-engine"], ["queue:wireless"], ["sdr_intel", "wireless_capture"], ["MinIO"]),
            TitanService("rtf-report-engine", "HTML, PDF, JSON, Markdown, XLSX report generation", ["rtf-graph-engine", "rtf-ai-engine"], ["queue:report"], ["reporting", "timeline_rendering", "graph_visualization"], ["MinIO"]),
            TitanService("rtf-ingestion-engine", "Normalizes evidence into events, entities, and artifacts", ["MinIO", "ElasticSearch", "Neo4j"], ["queue:ingestion"], ["normalization", "evidence_tagging", "artifact_indexing"], ["ElasticSearch", "MinIO", "Neo4j"]),
            TitanService("rtf-automation-engine", "Workflow builder and template automation", ["rtf-core", "rtf-worker-cluster"], ["queue:automation"], ["workflow_builder", "scheduler_bridge"], ["Redis"]),
            TitanService("rtf-monitoring-engine", "Telemetry, metrics, and health aggregation", ["Prometheus", "Grafana"], ["queue:metrics", "prometheus"], ["observability", "slo_monitoring"], ["ElasticSearch"]),
            TitanService("rtf-worker-cluster", "Distributed worker execution for compute-heavy jobs", ["RabbitMQ", "Redis"], ["queue:worker"], ["parallel_jobs", "fanout_execution"], ["Redis", "MinIO"]),
        ]

    def dependency_map(self) -> Dict[str, List[str]]:
        return {service.name: list(service.dependencies) for service in self.services}

    def service_catalog(self) -> Dict[str, Dict[str, Any]]:
        return {
            service.name: {
                "purpose": service.purpose,
                "interfaces": list(service.interfaces),
                "pipelines": list(service.pipelines),
                "storage": list(service.storage),
                "scalability": service.scalability,
            }
            for service in self.services
        }

    def extension_points(self) -> Dict[str, List[str]]:
        return {
            "cli": ["Add titan subcommands without impacting legacy commands"],
            "api": ["Expose distributed service topology and queue status endpoints"],
            "dashboard": ["Add graph explorer, workflow monitor, live logs, and service health cards"],
            "workflow_engine": ["Register TITAN pipelines through the existing workflow registry"],
            "module_system": ["Wrap external tools with universal TITAN wrappers"],
            "reporting": ["Feed graph, AI, and evidence timelines into existing reporting engine"],
            "scheduler": ["Bridge local async jobs to queue-backed worker execution"],
            "configuration": ["Layer service topology and queue settings over current YAML/env config"],
        }

    def architecture_map(self) -> Dict[str, Any]:
        return {
            "entrypoints": {
                "cli": ["rtf console", "rtf module", "rtf workflow", "rtf titan"],
                "api": ["/health", "/stats", "/modules", "/workflows", "/graph/schema", "/titan/manifest"],
                "dashboard": ["investigation_manager", "graph_explorer", "module_execution_panel", "report_viewer"],
            },
            "pipelines": {
                "legacy": ["full_recon", "identity_fusion", "cloud_audit", "web_audit"],
                "omega": [
                    "socmint_15_stage",
                    "identity_resolution",
                    "global_intelligence_graph",
                    "recursive_pivot_engine",
                    "distributed_reporting",
                ],
            },
            "data_plane": {
                "queueing": [self.infrastructure.message_bus, self.infrastructure.cache],
                "storage": [self.infrastructure.graph_db, self.infrastructure.search, self.infrastructure.object_store],
                "observability": list(self.infrastructure.metrics),
            },
            "services": self.service_catalog(),
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": "RTF TITAN OMEGA",
            "version": "4.0.0-omega",
            "infrastructure": asdict(self.infrastructure),
            "services": [asdict(service) for service in self.services],
            "dependency_map": self.dependency_map(),
            "service_catalog": self.service_catalog(),
            "architecture_map": self.architecture_map(),
            "extension_points": self.extension_points(),
        }


def build_titan_manifest() -> Dict[str, Any]:
    return TitanArchitecture().to_dict()
