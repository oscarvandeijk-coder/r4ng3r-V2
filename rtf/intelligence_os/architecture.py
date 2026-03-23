from dataclasses import dataclass
from typing import Dict, List

@dataclass(frozen=True)
class ArchitectureLayer:
    name: str
    responsibilities: List[str]

ARCHITECTURE_LAYERS: Dict[str, ArchitectureLayer] = {
    'data_acquisition': ArchitectureLayer('Data Acquisition Layer', ['Collect data from APIs, CLI tools, documents, archives, sensors, and queues.', 'Normalize raw acquisition envelopes into ingestion events.']),
    'tool_integration': ArchitectureLayer('Tool Integration Layer', ['Expose standardized tool wrappers for 500+ OSINT and red-team tools.', 'Handle CLI, API, rate-limiting, retries, parsers, and execution contracts.']),
    'processing': ArchitectureLayer('Processing Layer', ['Normalize artifacts into canonical entity payloads.', 'Perform deduplication, parsing, enrichment, and evidence attribution.']),
    'entity_intelligence': ArchitectureLayer('Entity Intelligence Layer', ['Manage canonical entities, confidence, evidence, and source lineage.', 'Drive entity-driven pivots for autonomous investigations.']),
    'graph': ArchitectureLayer('Graph Layer (Neo4j)', ['Persist nodes, relationships, and traversal metadata.', 'Provide graph projections and Cypher export contracts.']),
    'correlation_ai': ArchitectureLayer('Correlation & AI Layer', ['Fuse identities, score risk, detect patterns, and recommend pivots.', 'Generate analyst-facing summaries and automation decisions.']),
    'pipeline': ArchitectureLayer('Pipeline Engine', ['Execute YAML-defined, reusable, entity-driven pipelines.', 'Resolve stage dependencies and transformation hooks.']),
    'workflow': ArchitectureLayer('Workflow Engine', ['Chain pipelines into investigations with trigger-aware orchestration.', 'Track workflow state, outputs, and escalation points.']),
    'automation': ArchitectureLayer('Automation Engine', ['Autonomously trigger pivots for newly discovered entities.', 'Apply recursion limits, policies, rate budgets, and approvals.']),
    'api': ArchitectureLayer('API Layer', ['Expose investigation, module, workflow, graph, and reporting APIs.', 'Serve backend contracts for the dashboard, workers, and integrations.']),
    'dashboard': ArchitectureLayer('Dashboard Layer', ['Provide analyst control plane for modules, pipelines, graph, alerts, and reports.', 'Visualize investigations, telemetry, and autonomous activity.']),
}
