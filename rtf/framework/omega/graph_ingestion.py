from __future__ import annotations

from typing import Any, Dict, Iterable, List

from framework.db.database import db
from framework.titan.knowledge_graph import RELATIONSHIP_TYPES, TitanKnowledgeGraph


class OmegaGraphIngestionService:
    def __init__(self) -> None:
        self.graph = TitanKnowledgeGraph()

    def schema(self) -> Dict[str, Any]:
        schema = self.graph.schema()
        schema["ingestion"] = {
            "sinks": ["SQLite graph cache", "Neo4j"],
            "entity_pipeline": ["normalize", "upsert node", "upsert relationship", "report evidence"],
            "relationship_types": RELATIONSHIP_TYPES,
        }
        return schema

    def ingest_osint_result(self, operation_id: str, module_path: str, seed: Dict[str, Any]) -> Dict[str, Any]:
        export = self.graph.ingest_identity(seed)
        for node in export["nodes"]:
            node_id = f"{node['entity_type']}:{node['value']}"
            db.upsert_graph_node(
                node_id=node_id,
                entity_type=node["entity_type"],
                value=node["value"],
                label=node["value"],
                confidence=float(node.get("properties", {}).get("confidence", 0.75) or 0.75),
                source_module=module_path,
                source_job_id="omega-graph",
                operation_id=operation_id,
                properties=node.get("properties", {}),
                tags=[module_path.split("/")[0], "neo4j"],
            )
        for idx, edge in enumerate(export["edges"], 1):
            db.upsert_graph_edge(
                edge_id=f"{operation_id}:{module_path}:{idx}:{edge['source']}:{edge['relationship']}:{edge['target']}",
                source_node_id=edge["source"],
                relationship=edge["relationship"],
                target_node_id=edge["target"],
                confidence=float(edge.get("properties", {}).get("confidence", 0.7) or 0.7),
                source_module=module_path,
                source_job_id="omega-graph",
                operation_id=operation_id,
                properties=edge.get("properties", {}),
            )
        return {
            **export,
            "persisted": {
                "sqlite_graph_cache": True,
                "neo4j_ready": True,
                "node_count": len(export["nodes"]),
                "edge_count": len(export["edges"]),
            },
        }

    def cypher_statements(self, seed: Dict[str, Any]) -> List[str]:
        graph = TitanKnowledgeGraph()
        graph.ingest_identity(seed)
        return graph.cypher_preview()


omega_graph_ingestion_service = OmegaGraphIngestionService()
