from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List


@dataclass
class OmegaEngineSpec:
    name: str
    category: str
    purpose: str
    loader_module: str
    pipelines: List[str] = field(default_factory=list)
    integrations: List[str] = field(default_factory=list)
    output_modes: List[str] = field(default_factory=lambda: ["cli", "pipeline", "json", "graph", "report"])


@dataclass
class OmegaSourceCategory:
    name: str
    description: str
    estimated_sources: int
    examples: List[str] = field(default_factory=list)


ENGINE_SPECS: List[OmegaEngineSpec] = [
    OmegaEngineSpec("rtf-core", "omega", "Shared orchestration, compatibility, configuration, and registry services.", "omega/rtf_core", ["legacy_compatibility", "core_orchestration"], ["cli", "api", "scheduler"]),
    OmegaEngineSpec("rtf-osint-engine", "omega", "Primary OSINT collection and normalization plane for large source aggregation.", "omega/rtf_osint_engine", ["osint_collection", "multi_source_enrichment"], ["tool_registry", "source_registry", "search"]),
    OmegaEngineSpec("rtf-socmint-engine", "omega", "15-stage SOCMINT investigation execution with recursive pivots.", "omega/rtf_socmint_engine", ["socmint_15_stage", "identity_resolution", "recursive_pivot"], ["graph", "ai", "search", "scraping"]),
    OmegaEngineSpec("rtf-breach-engine", "omega", "Credential, combo-list, and breach evidence ingestion plus correlation.", "omega/rtf_breach_engine", ["breach_correlation", "credential_exposure"], ["credential_intel", "graph", "reporting"]),
    OmegaEngineSpec("rtf-scraper-engine", "omega", "Stealth search/social/document scraping and artifact harvesting.", "omega/rtf_scraper_engine", ["search_scraping", "artifact_collection"], ["browser_automation", "metadata", "osint"]),
    OmegaEngineSpec("rtf-casm-engine", "omega", "Continuous attack-surface monitoring and validation.", "omega/rtf_casm_engine", ["casm", "surface_monitoring"], ["recon", "reporting", "automation"]),
    OmegaEngineSpec("rtf-graph-engine", "omega", "Neo4j-backed graph ingestion, schema management, and entity traversal.", "omega/rtf_graph_engine", ["global_intelligence_graph", "graph_ingestion"], ["neo4j", "api", "reporting"]),
    OmegaEngineSpec("rtf-ai-engine", "omega", "AI correlation, stylometry, clustering, and threat scoring.", "omega/rtf_ai_engine", ["ai_correlation", "threat_scoring"], ["llm", "graph", "reporting"]),
    OmegaEngineSpec("rtf-credential-engine", "omega", "Credential analysis, password candidate generation, and breach pivoting.", "omega/rtf_credential_engine", ["credential_analysis", "password_generation"], ["breach", "automation", "workers"]),
    OmegaEngineSpec("rtf-report-engine", "omega", "Unified reporting for HTML, PDF, JSON, DOCX, and dashboard artifacts.", "omega/rtf_report_engine", ["report_generation", "timeline_reporting"], ["reporting", "graph", "dashboard"]),
    OmegaEngineSpec("rtf-monitoring-engine", "omega", "Service telemetry, queue health, agent health, and event streaming.", "omega/rtf_monitoring_engine", ["service_health", "telemetry"], ["metrics", "dashboard", "doctor"]),
    OmegaEngineSpec("rtf-automation-engine", "omega", "Scheduler-integrated automation, self-healing, and recurring jobs.", "omega/rtf_automation_engine", ["autonomous_development", "scheduled_workflows"], ["scheduler", "workers", "repair"]),
    OmegaEngineSpec("rtf-worker-cluster", "omega", "Distributed worker fanout for async pipelines and heavy tooling.", "omega/rtf_worker_cluster", ["fanout_execution", "parallel_pipeline"], ["queue", "scheduler", "compute"]),
]

SOURCE_CATEGORIES: List[OmegaSourceCategory] = [
    OmegaSourceCategory("username_intelligence", "Account and alias discovery across social, code, breach, and community properties.", 180, ["sherlock", "maigret", "nexfil", "blackbird"]),
    OmegaSourceCategory("email_intelligence", "Email exposure, account registration, and breach artifact correlation.", 110, ["holehe", "h8mail", "dehashed", "snusbase"]),
    OmegaSourceCategory("phone_intelligence", "Phone enrichment, carrier intelligence, messaging footprint, and leak monitoring.", 80, ["phoneinfoga", "numverify", "telecom directories"]),
    OmegaSourceCategory("domain_intelligence", "WHOIS, DNS, CT, ASN, PDNS, and web-surface intelligence.", 160, ["subfinder", "amass", "securitytrails", "urlscan"]),
    OmegaSourceCategory("organization_intelligence", "Company, employee, office, brand, and supply-chain intelligence.", 90, ["OpenCorporates", "LinkedIn", "Crunchbase"]),
    OmegaSourceCategory("breach_intelligence", "Credential, combo, paste, and darknet breach monitoring.", 120, ["dehashed", "intelx", "HIBP", "paste feeds"]),
    OmegaSourceCategory("ip_intelligence", "Network ownership, reputation, geolocation, and infrastructure telemetry.", 90, ["Shodan", "Censys", "AbuseIPDB"]),
    OmegaSourceCategory("document_intelligence", "Document metadata, OCR, indexing, and relationship extraction.", 70, ["exiftool", "FOCA", "OCR pipelines"]),
    OmegaSourceCategory("image_intelligence", "Reverse-image, EXIF, media fingerprinting, and visual correlation.", 100, ["exiftool", "TinEye", "Perceptual hash"]),
]


def build_omega_registry() -> Dict[str, Any]:
    total_sources = sum(category.estimated_sources for category in SOURCE_CATEGORIES)
    return {
        "engines": [asdict(spec) for spec in ENGINE_SPECS],
        "source_categories": [asdict(category) for category in SOURCE_CATEGORIES],
        "source_capacity": {
            "estimated_total_sources": total_sources,
            "design_goal": "1000+ pluggable OSINT, SOCMINT, breach, infrastructure, and artifact sources",
            "integration_contract": ["module_loader", "pipeline_v2", "json_output", "graph_ingestion", "report_generation"],
        },
    }


def build_self_healing_actions() -> Dict[str, Dict[str, Any]]:
    return {
        "doctor": {"purpose": "Run framework health diagnostics", "checks": ["tool_registry", "module_loader", "omega_engines", "graph_schema", "api_contract"]},
        "fix": {"purpose": "Repair common dependency and registration issues", "checks": ["missing_tools", "engine_registration", "workflow_registry"]},
        "validate": {"purpose": "Validate module, pipeline, and graph contracts", "checks": ["module_metadata", "pipeline_structure", "neo4j_schema"]},
        "repair": {"purpose": "Rebuild automation metadata and queue-safe defaults", "checks": ["scheduler_defaults", "service_catalog", "event_stream"]},
        "upgrade": {"purpose": "Generate OMEGA-BLACK architecture upgrade report", "checks": ["architecture_report", "source_registry", "engine_manifest"]},
    }
