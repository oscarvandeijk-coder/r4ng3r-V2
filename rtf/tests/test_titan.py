from __future__ import annotations

import asyncio
import unittest


class TestTitanArchitecture(unittest.TestCase):
    def test_manifest_contains_required_services(self):
        from framework.titan import build_titan_manifest
        manifest = build_titan_manifest()
        services = {service["name"] for service in manifest["services"]}
        self.assertIn("rtf-core", services)
        self.assertIn("rtf-socmint-engine", services)
        self.assertIn("rtf-monitoring-engine", services)
        self.assertIn("architecture_map", manifest)
        self.assertEqual(manifest["version"], "4.0.0-omega")

    def test_graph_ingestion(self):
        from framework.titan import TitanKnowledgeGraph
        graph = TitanKnowledgeGraph().ingest_identity({"username": "alice", "email": "alice@example.com", "domain": "example.com"})
        self.assertGreaterEqual(len(graph["nodes"]), 3)
        self.assertGreaterEqual(len(graph["edges"]), 2)
        self.assertEqual(graph["backend"], "Neo4j")
        self.assertTrue(graph["cypher_preview"])

    def test_identity_resolution(self):
        from framework.titan import IdentityResolutionEngine
        result = IdentityResolutionEngine().resolve([
            {"username": "alice.ops", "email": "alice@example.com", "bio": "red team operator", "posting_hour": 8, "writing_sample": "hello from the red team"},
            {"username": "alice-ops", "email": "alice@example.com", "bio": "red team operator", "posting_hour": 9, "writing_sample": "hello from red team"},
        ])
        self.assertGreater(result["confidence"], 0.5)
        self.assertIn("models", result)


class TestTitanPipeline(unittest.IsolatedAsyncioTestCase):
    async def test_socmint_pipeline(self):
        from framework.titan import TitanSOCMINTPipeline
        result = TitanSOCMINTPipeline().run({"username": "alice.ops", "email": "alice@example.com", "domain": "example.com"})
        self.assertEqual(result["stage_count"], 16)
        self.assertIn("normalized_seed", result)
        self.assertIn("graph", result)
        self.assertIn("identity_resolution", result)

    async def test_orchestrator(self):
        from framework.titan import TitanOrchestrator
        orchestrator = TitanOrchestrator()
        result = await orchestrator.run_investigation({"username": "alice.ops", "email": "alice@example.com", "domain": "example.com"})
        self.assertTrue(result["success"])
        self.assertTrue(result["queues"])


if __name__ == "__main__":
    unittest.main(verbosity=2)


class TestTitanSchema(unittest.TestCase):
    def test_schema_contains_entities_and_relationships(self):
        from framework.titan import TitanKnowledgeGraph
        schema = TitanKnowledgeGraph().schema()
        self.assertIn("Person", schema["entity_types"])
        self.assertIn("USES_EMAIL", schema["relationship_types"])
        self.assertEqual(schema["backend"], "Neo4j")


class TestOmegaBlack(unittest.TestCase):
    def test_omega_registry_capacity(self):
        from framework.titan import build_omega_registry
        registry = build_omega_registry()
        engine_names = {engine["name"] for engine in registry["engines"]}
        self.assertIn("rtf-breach-engine", engine_names)
        self.assertIn("rtf-worker-cluster", engine_names)
        self.assertGreaterEqual(registry["source_capacity"]["estimated_total_sources"], 1000)

    def test_doctor_actions_present(self):
        from framework.titan import build_self_healing_actions
        actions = build_self_healing_actions()
        self.assertIn("doctor", actions)
        self.assertIn("repair", actions)
        self.assertIn("validate", actions)

    def test_omega_modules_load_through_module_loader(self):
        from framework.modules.loader import ModuleLoader
        loader = ModuleLoader()
        loader.load_all()
        modules = {module["path"] for module in loader.list_modules(category="omega")}
        self.assertIn("omega/rtf_graph_engine", modules)
        self.assertIn("omega/rtf_breach_engine", modules)

