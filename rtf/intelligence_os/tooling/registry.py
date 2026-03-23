from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Type

from intelligence_os.tooling.base import BaseModule
from intelligence_os.tooling.catalog import load_tool_catalog
from intelligence_os.tooling.wrappers import MODULE_CLASSES

@dataclass
class ToolDefinition:
    name: str
    category: str
    input_types: List[str]
    output_types: List[str]
    mode: str
    command_template: str
    pipeline_compatible: bool
    rate_limit_per_minute: int
    parser: str
    api_required: bool = False
    display_name: str | None = None
    validation: str | None = None

class ToolRegistry:
    def __init__(self) -> None:
        self._catalog = [ToolDefinition(**entry) for entry in load_tool_catalog()]
        self._modules: Dict[str, Type[BaseModule]] = MODULE_CLASSES.copy()

    def list_tools(self) -> List[ToolDefinition]:
        return list(self._catalog)

    def summary(self) -> Dict[str, Any]:
        categories: Dict[str, int] = {}
        for entry in self._catalog:
            categories[entry.category] = categories.get(entry.category, 0) + 1
        return {'total_tools': len(self._catalog), 'categories': categories, 'wrapped_modules': sorted(self._modules)}

    def get(self, name: str) -> ToolDefinition | None:
        return next((entry for entry in self._catalog if entry.name == name), None)

    def resolve_module(self, name: str) -> Type[BaseModule]:
        if name in self._modules:
            return self._modules[name]
        definition = self.get(name)
        if not definition:
            raise KeyError(name)
        return type(f"{name.title().replace('-', '')}Module", (BaseModule,), {'name': definition.name, 'category': definition.category, 'input_types': definition.input_types, 'output_types': definition.output_types, 'command_template': definition.command_template})

registry = ToolRegistry()
