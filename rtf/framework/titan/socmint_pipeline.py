from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from framework.titan.identity_resolution import IdentityResolutionEngine
from framework.titan.knowledge_graph import TitanKnowledgeGraph
from framework.titan.wrappers import StaticToolCatalog


SOCMINT_STAGES = [
    ("A", "Seed normalization"),
    ("B", "Username discovery"),
    ("C", "Account scraping"),
    ("D", "Web search scraping"),
    ("E", "Email intelligence"),
    ("F", "Domain intelligence"),
    ("G", "Code repository analysis"),
    ("H", "Phone intelligence"),
    ("I", "Dark web monitoring"),
    ("J", "Metadata intelligence"),
    ("K", "Behavioral analysis"),
    ("L", "Correlation engine"),
    ("M", "Graph generation"),
    ("N", "Risk scoring"),
    ("O", "Investigation reporting"),
]


@dataclass
class StageResult:
    code: str
    name: str
    status: str
    summary: Dict[str, Any]


class TitanSOCMINTPipeline:
    def __init__(self) -> None:
        self.identity_engine = IdentityResolutionEngine()
        self.graph = TitanKnowledgeGraph()

    def run(self, seed: Dict[str, Any]) -> Dict[str, Any]:
        profile_a = {
            "username": seed.get("username", ""),
            "email": seed.get("email", ""),
            "bio": seed.get("bio", ""),
            "posting_hour": seed.get("posting_hour", 12),
            "writing_sample": seed.get("writing_sample", ""),
            "avatar_hash": seed.get("avatar_hash", ""),
        }
        profile_b = {
            "username": seed.get("candidate_username", seed.get("username", "")),
            "email": seed.get("candidate_email", seed.get("email", "")),
            "bio": seed.get("candidate_bio", seed.get("bio", "")),
            "posting_hour": seed.get("candidate_posting_hour", seed.get("posting_hour", 12)),
            "writing_sample": seed.get("candidate_writing_sample", seed.get("writing_sample", "")),
            "avatar_hash": seed.get("candidate_avatar_hash", seed.get("avatar_hash", "")),
        }
        correlation = self.identity_engine.resolve([profile_a, profile_b])
        graph = self.graph.ingest_identity(seed)
        stages: List[StageResult] = []
        for code, name in SOCMINT_STAGES:
            summary: Dict[str, Any] = {"seed_keys": sorted(seed.keys())[:8]}
            if code == "B":
                summary = {"tools": StaticToolCatalog.summary()["username_discovery"], "coverage": ">=500 websites"}
            elif code == "D":
                summary = {"engines": StaticToolCatalog.summary()["search_engines"], "extracts": ["profiles", "mentions", "documents", "images", "videos"]}
            elif code == "L":
                summary = correlation
            elif code == "M":
                summary = {"graph_nodes": len(graph["nodes"]), "graph_edges": len(graph["edges"])}
            elif code == "N":
                summary = {"risk_score": correlation["risk_score"], "confidence": correlation["confidence"]}
            elif code == "O":
                summary = {"formats": ["HTML", "PDF", "JSON", "Markdown", "XLSX"]}
            stages.append(StageResult(code, name, "ready", summary))
        return {
            "pipeline": "titan_socmint",
            "stage_count": len(stages),
            "stages": [stage.__dict__ for stage in stages],
            "graph": graph,
            "identity_resolution": correlation,
        }
