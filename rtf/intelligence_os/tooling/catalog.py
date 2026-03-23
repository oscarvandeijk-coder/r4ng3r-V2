from __future__ import annotations
import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List

@lru_cache(maxsize=1)
def load_tool_catalog() -> List[Dict[str, Any]]:
    path = Path(__file__).with_name('tool_catalog.json')
    return json.loads(path.read_text())
