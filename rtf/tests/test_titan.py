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


class TestOmegaBlackArchitecture(unittest.TestCase):
    def test_engine_registry_and_sources(self):
        from framework.omega import omega_engine_registry, omega_source_catalog
        summary = omega_engine_registry.summary()
        self.assertGreaterEqual(summary["engine_count"], 13)
        self.assertIn("rtf-breach-engine", {engine["name"] for engine in summary["engines"]})
        self.assertGreaterEqual(omega_source_catalog.count(), 1000)

    def test_graph_ingestion_and_doctor(self):
        from framework.db.database import Database
        Database._instance = None
        import tempfile, os
        tmp = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        tmp.close()
        try:
            from framework.db.database import db
            db.init(tmp.name)
            from framework.omega import omega_doctor, omega_graph_ingestion_service
            report = omega_doctor.inspect()
            self.assertEqual(report["status"], "healthy")
            graph = omega_graph_ingestion_service.ingest_osint_result('primary', 'osint/username_enum', {"username": "alice.ops", "email": "alice@example.com", "domain": "example.com"})
            self.assertTrue(graph["persisted"]["sqlite_graph_cache"])
            self.assertGreaterEqual(graph["persisted"]["node_count"], 3)
        finally:
            os.unlink(tmp.name)
