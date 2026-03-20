"""RTF v2.0 Test Suite"""
from __future__ import annotations
import asyncio, json, os, sys, tempfile, unittest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

class TestConfig(unittest.TestCase):
    def setUp(self):
        from framework.core.config import Config
        Config._instance = None
    def test_defaults_loaded(self):
        from framework.core.config import config
        config.load()
        self.assertIsNotNone(config.get("base_dir"))
        self.assertIsNotNone(config.get("api_port"))
    def test_set_and_get(self):
        from framework.core.config import config
        config.load()
        config.set("test_key","test_value")
        self.assertEqual(config.get("test_key"),"test_value")
    def test_env_override(self):
        os.environ["RTF_API_PORT"]="9999"
        from framework.core.config import Config; Config._instance=None
        from framework.core.config import config; config.load()
        self.assertEqual(config.get("api_port"),9999)
        del os.environ["RTF_API_PORT"]

class TestDatabase(unittest.TestCase):
    def setUp(self):
        from framework.db.database import Database; Database._instance=None
        self.tmp=tempfile.NamedTemporaryFile(suffix=".db",delete=False); self.tmp.close()
        from framework.db.database import db; db.init(self.tmp.name); self.db=db
    def tearDown(self): os.unlink(self.tmp.name)
    def test_job_lifecycle(self):
        self.db.create_job("j1","test","recon/test",{})
        self.db.start_job("j1"); j=self.db.get_job("j1")
        self.assertEqual(j["status"],"running")
        self.db.finish_job("j1",{"output":"done"})
        j=self.db.get_job("j1"); self.assertEqual(j["status"],"completed")
    def test_add_and_list_findings(self):
        self.db.create_job("j2","find_job","recon/test",{})
        self.db.add_finding("j2","example.com","Test Finding",severity="high")
        findings=self.db.list_findings(job_id="j2")
        self.assertEqual(len(findings),1); self.assertEqual(findings[0]["severity"],"high")
    def test_targets(self):
        self.db.add_target("example.com","domain")
        targets=self.db.list_targets()
        self.assertIn("example.com",[t["value"] for t in targets])

class TestBaseModule(unittest.TestCase):
    def _make_module(self):
        from framework.modules.base import BaseModule, ModuleResult
        class DummyModule(BaseModule):
            def info(self): return {"name":"dummy","description":"Test","category":"recon"}
            def _declare_options(self):
                self._register_option("target","Test target",required=True)
                self._register_option("count","A count",required=False,default=5,type=int)
            async def run(self) -> ModuleResult:
                return ModuleResult(success=True,output={"target":self.get("target"),"count":self.get("count")})
        return DummyModule()
    def test_defaults(self):
        mod=self._make_module(); self.assertEqual(mod.get("count"),5)
    def test_set_option(self):
        mod=self._make_module(); mod.set("target","example.com"); self.assertEqual(mod.get("target"),"example.com")
    def test_validate_raises_missing(self):
        from framework.core.exceptions import OptionValidationError
        mod=self._make_module()
        with self.assertRaises(OptionValidationError): mod.validate()
    def test_execute_success(self):
        mod=self._make_module()
        result=asyncio.get_event_loop().run_until_complete(mod.execute({"target":"test.com","count":"3"}))
        self.assertTrue(result.success); self.assertEqual(result.output["count"],3)

class TestModuleLoader(unittest.TestCase):
    def setUp(self):
        from framework.modules.loader import ModuleLoader; self.loader=ModuleLoader()
    def test_load_all_returns_count(self):
        count=self.loader.load_all(); self.assertGreater(count,0)
    def test_list_modules_not_empty(self):
        self.loader.load_all(); modules=self.loader.list_modules(); self.assertGreater(len(modules),0)
    def test_get_known_module(self):
        self.loader.load_all(); cls=self.loader.get("recon/subdomain_enum"); self.assertIsNotNone(cls)
    def test_search(self):
        self.loader.load_all(); results=self.loader.search("subdomain"); self.assertGreater(len(results),0)

class TestToolRegistry(unittest.TestCase):
    def setUp(self):
        from framework.registry.tool_registry import ToolRegistry; self.registry=ToolRegistry()
    def test_catalogue_loaded(self): self.assertGreater(len(self.registry.list_all()),0)
    def test_known_tool(self): entry=self.registry.get("nmap"); self.assertIsNotNone(entry)
    def test_summary(self):
        s=self.registry.summary(); self.assertIn("total_tools",s); self.assertIn("installed",s)

class TestWorkflowEngine(unittest.IsolatedAsyncioTestCase):
    def _make_wf(self, succeed=True):
        from framework.workflows.engine import Workflow, Step
        from framework.modules.base import BaseModule, ModuleResult
        class MockModule(BaseModule):
            _succeed=succeed
            def info(self): return {"name":"mock","description":"","category":"recon"}
            def _declare_options(self): self._register_option("target","T",required=False,default="test")
            async def run(self) -> ModuleResult:
                if not MockModule._succeed: return ModuleResult(success=False,error="Mock failure")
                return ModuleResult(success=True,output={"done":True})
        class TestWF(Workflow):
            name="test_wf"; description="Test"
            def steps(self): return [Step("step1",MockModule,required=False),Step("step2",MockModule,required=False)]
        return TestWF()
    async def test_successful_workflow(self):
        wf=self._make_wf(True); result=await wf.run({"target":"example.com"})
        self.assertTrue(result.success); self.assertEqual(len(result.steps),2)
    async def test_workflow_to_dict(self):
        wf=self._make_wf(); result=await wf.run(); d=result.to_dict()
        self.assertIn("workflow",d); self.assertIn("steps",d)
    async def test_builtin_workflows(self):
        from framework.workflows.engine import BUILTIN_WORKFLOWS
        self.assertIn("full_recon",BUILTIN_WORKFLOWS)
        self.assertIn("identity_fusion",BUILTIN_WORKFLOWS)
        self.assertIn("full_ad_compromise",BUILTIN_WORKFLOWS)
    async def test_workflow_builder(self):
        from framework.workflows.engine import WorkflowBuilder
        from framework.modules.base import BaseModule, ModuleResult
        class B(BaseModule):
            def info(self): return {"name":"b","description":"","category":"recon"}
            def _declare_options(self): pass
            async def run(self) -> ModuleResult: return ModuleResult(success=True)
        wf=(WorkflowBuilder("custom").with_options(target="example.com").add_step("step1",B).build())
        result=await wf.run(); self.assertTrue(result.success)

class TestScheduler(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        from framework.scheduler.scheduler import Scheduler; self.scheduler=Scheduler(max_workers=2); await self.scheduler.start()
    async def asyncTearDown(self): await self.scheduler.stop()
    async def test_submit_and_complete(self):
        async def noop(): return "done"
        job=self.scheduler.submit("test",noop); completed=await self.scheduler.wait_for(job.id,poll_interval=0.1)
        self.assertEqual(completed.result,"done")
    async def test_stats(self):
        stats=self.scheduler.stats(); self.assertIn("total",stats)

if __name__ == "__main__":
    unittest.main(verbosity=2)
