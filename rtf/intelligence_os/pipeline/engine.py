from __future__ import annotations
from pathlib import Path
from typing import Any, Dict
import yaml

from intelligence_os.ai.correlation import CorrelationEngine
from intelligence_os.graph.store import InMemoryGraphStore
from intelligence_os.models import PipelineExecutionResult
from intelligence_os.tooling.base import ModuleContext
from intelligence_os.tooling.registry import registry

class PipelineEngine:
    def __init__(self, graph_store: InMemoryGraphStore | None = None) -> None:
        self.graph_store = graph_store or InMemoryGraphStore()
        self.correlation = CorrelationEngine()

    def load_pipeline(self, path: str | Path) -> Dict[str, Any]:
        return yaml.safe_load(Path(path).read_text())

    def execute_pipeline(self, definition: Dict[str, Any], seed: Dict[str, Any], workspace: str = 'default') -> PipelineExecutionResult:
        context: Dict[str, Any] = {'seed': seed.copy(), 'transformations': []}
        result = PipelineExecutionResult(pipeline=definition['name'], success=True, context=context)
        entities = []
        relationships = []
        for stage in definition.get('stages', []):
            module_name = stage['module']
            module_cls = registry.resolve_module(module_name)
            module = module_cls()
            input_mapping = stage.get('input', {})
            module_input = {k: seed.get(v, context.get(v, seed.get(k, v))) for k, v in input_mapping.items()} if input_mapping else seed.copy()
            try:
                execution = module.execute(module_input, ModuleContext(seed=seed, workspace=workspace, telemetry=context))
            except Exception as exc:
                execution = type('ExecutionFailure', (), {'success': False, 'error': str(exc), 'entities': [], 'relationships': []})()
            result.executed_modules.append(module_name)
            if not execution.success:
                result.success = False
                result.errors.append(execution.error or f'{module_name} failed')
                if stage.get('required', True):
                    break
                continue
            entities.extend(execution.entities)
            relationships.extend(execution.relationships)
            for transform in stage.get('transformations', []):
                context['transformations'].append({'module': module_name, 'transform': transform})
                if transform == 'extract_domains':
                    context['domains'] = [e.value for e in execution.entities if e.entity_type == 'Domain']
                elif transform == 'extract_accounts':
                    context['accounts'] = [e.value for e in execution.entities if e.entity_type == 'Account']
        result.entities = entities
        result.relationships = relationships
        result.graph_writes = self.graph_store.ingest(entities, relationships)
        context['identity_fusions'] = self.correlation.fuse_identities(entities)
        context['risk_score'] = self.correlation.risk_score(entities)
        context['patterns'] = self.correlation.detect_patterns(entities)
        return result
