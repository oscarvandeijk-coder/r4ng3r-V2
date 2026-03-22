from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from framework.automation.pipeline_v2 import PipelineEngineV2, PipelineStepV2
from framework.titan.architecture import build_titan_manifest
from framework.titan.socmint_pipeline import TitanSOCMINTPipeline


@dataclass
class QueueMessage:
    topic: str
    payload: Dict[str, Any]


@dataclass
class ServiceHealth:
    name: str
    status: str = "ready"
    queue_depth: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


class TitanMessageBus:
    def __init__(self) -> None:
        self.messages: List[QueueMessage] = []

    async def publish(self, topic: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        self.messages.append(QueueMessage(topic, payload))
        return {"topic": topic, "queued": len(self.messages)}

    def drain(self, topic: Optional[str] = None) -> List[Dict[str, Any]]:
        selected = [m for m in self.messages if topic in (None, m.topic)]
        self.messages = [m for m in self.messages if m not in selected]
        return [{"topic": m.topic, "payload": m.payload} for m in selected]


class TitanOrchestrator:
    def __init__(self) -> None:
        self.bus = TitanMessageBus()
        self.pipeline = TitanSOCMINTPipeline()

    def health(self) -> Dict[str, Any]:
        manifest = build_titan_manifest()
        services = [ServiceHealth(name=s["name"], queue_depth=sum(1 for m in self.bus.messages if m.topic.endswith(s["name"].split("rtf-")[-1]))) for s in manifest["services"]]
        return {
            "architecture": manifest["name"],
            "service_count": len(services),
            "services": [service.__dict__ for service in services],
            "queued_messages": len(self.bus.messages),
        }

    async def run_investigation(self, seed: Dict[str, Any]) -> Dict[str, Any]:
        engine = PipelineEngineV2(concurrency=6)
        engine.add_step(PipelineStepV2("queue-seed", lambda ctx: self.bus.publish("ingestion", {"seed": seed})))
        engine.add_step(PipelineStepV2("socmint", lambda ctx: asyncio.to_thread(self.pipeline.run, seed)))
        engine.add_step(PipelineStepV2("queue-report", lambda ctx: self.bus.publish("report", {"risk": ctx.get("identity_resolution", {}).get("risk_score", 0)})))
        result = await engine.run()
        return {
            "success": result.success,
            "context": result.context,
            "history": result.history,
            "queues": self.bus.drain(),
        }
