from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


from fastapi.testclient import TestClient

from intelligence_os.api.app import create_app
from intelligence_os.automation.autonomous import AutonomousInvestigationEngine
from intelligence_os.pipeline.engine import PipelineEngine
from intelligence_os.tooling.registry import registry
from intelligence_os.workflow.engine import WorkflowEngine


def test_tool_registry_supports_500_plus_tools():
    assert registry.summary()['total_tools'] >= 500
    assert registry.get('amass') is not None
    assert registry.get('nmap') is not None


def test_pipeline_execution_graph_population():
    engine = PipelineEngine()
    definition = engine.load_pipeline(Path(__file__).resolve().parents[1] / 'pipelines' / 'email_intelligence_pipeline.yaml')
    result = engine.execute_pipeline(definition, {'email': 'analyst@example.com'})
    assert result.success
    assert 'holehe' in result.executed_modules
    assert result.graph_writes > 0
    assert result.context['risk_score'] >= 0.2


def test_workflow_and_autonomous_investigation():
    workflow_engine = WorkflowEngine()
    workflow_result = workflow_engine.run_workflow('target_profiling', {'username': 'alice', 'email': 'alice@example.com', 'domain': 'example.com'})
    assert len(workflow_result['executions']) == 3
    autonomous = AutonomousInvestigationEngine()
    auto_result = autonomous.investigate({'username': 'alice'}, max_depth=1)
    assert auto_result['runs']


def test_api_endpoints():
    client = TestClient(create_app())
    assert client.get('/intelligence-os/health').status_code == 200
    assert client.get('/intelligence-os/tools').json()['summary']['total_tools'] >= 500
    pipeline_resp = client.post('/intelligence-os/pipelines/email_intelligence_pipeline/run', json={'email': 'target@example.com'})
    assert pipeline_resp.status_code == 200