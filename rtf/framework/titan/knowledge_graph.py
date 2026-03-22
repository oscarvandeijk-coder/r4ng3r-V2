from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


ENTITY_TYPES = [
    "Person", "Username", "Email", "Phone", "Domain", "Organization", "Account",
    "Repository", "IP", "Location", "Device", "Website", "Document", "Media",
]
RELATIONSHIP_TYPES = [
    "REGISTERED_WITH", "CONNECTED_TO", "OWNS", "POSTED_FROM", "MENTIONED_IN",
    "FOLLOWS", "USES_EMAIL", "USES_PHONE", "USES_USERNAME", "ASSOCIATED_WITH",
    "HOSTED_ON", "INTERACTED_WITH",
]


@dataclass
class GraphNode:
    entity_type: str
    value: str
    properties: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GraphEdge:
    source: str
    relationship: str
    target: str
    properties: Dict[str, Any] = field(default_factory=dict)


class TitanKnowledgeGraph:
    def __init__(self) -> None:
        self.nodes: Dict[str, GraphNode] = {}
        self.edges: List[GraphEdge] = []

    def add_entity(self, entity_type: str, value: str, **properties: Any) -> GraphNode:
        if entity_type not in ENTITY_TYPES:
            raise ValueError(f"Unsupported entity type: {entity_type}")
        key = f"{entity_type}:{value}"
        node = self.nodes.get(key) or GraphNode(entity_type=entity_type, value=value)
        node.properties.update(properties)
        self.nodes[key] = node
        return node

    def relate(self, source: GraphNode, relationship: str, target: GraphNode, **properties: Any) -> GraphEdge:
        if relationship not in RELATIONSHIP_TYPES:
            raise ValueError(f"Unsupported relationship type: {relationship}")
        edge = GraphEdge(f"{source.entity_type}:{source.value}", relationship, f"{target.entity_type}:{target.value}", properties)
        self.edges.append(edge)
        return edge

    def ingest_identity(self, seed: Dict[str, Any]) -> Dict[str, Any]:
        person = self.add_entity("Person", seed.get("subject", seed.get("username", "unknown")), confidence=seed.get("confidence", 0.5))
        if seed.get("username"):
            self.relate(person, "USES_USERNAME", self.add_entity("Username", seed["username"]))
        if seed.get("email"):
            self.relate(person, "USES_EMAIL", self.add_entity("Email", seed["email"]))
        if seed.get("phone"):
            self.relate(person, "USES_PHONE", self.add_entity("Phone", seed["phone"]))
        if seed.get("domain"):
            self.relate(person, "ASSOCIATED_WITH", self.add_entity("Domain", seed["domain"]))
        return self.export()

    def export(self) -> Dict[str, Any]:
        return {
            "nodes": [vars(node) for node in self.nodes.values()],
            "edges": [vars(edge) for edge in self.edges],
            "entity_types": list(ENTITY_TYPES),
            "relationship_types": list(RELATIONSHIP_TYPES),
        }
