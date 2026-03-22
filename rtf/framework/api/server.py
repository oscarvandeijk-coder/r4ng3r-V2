"""RedTeam Framework v2.0 - REST API Server"""
from __future__ import annotations
import asyncio, uuid
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Dict, List, Optional, Set

try:
    from fastapi import APIRouter, FastAPI, HTTPException, BackgroundTasks, Depends, Header, Query
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
    _HAS_FASTAPI = True
except ImportError:
    _HAS_FASTAPI = False

from framework.core.config import config
from framework.core.logger import get_logger
from framework.db.database import db
from framework.modules.loader import module_loader
from framework.registry.tool_registry import tool_registry, ToolCategory
from framework.scheduler.scheduler import scheduler
from framework.titan import TitanOrchestrator, build_titan_manifest
from framework.workflows.engine import BUILTIN_WORKFLOWS, get_workflow

log = get_logger("rtf.api")

if _HAS_FASTAPI:
    class ModuleRunRequest(BaseModel):
        options: Dict[str, Any] = {}
    class WorkflowRunRequest(BaseModel):
        options: Dict[str, Any] = {}; output_dir: Optional[str] = None
    class TargetAddRequest(BaseModel):
        value: str; type: str = "domain"; tags: str = ""

def create_app() -> "FastAPI":
    if not _HAS_FASTAPI:
        raise ImportError("fastapi and pydantic are required: pip install fastapi uvicorn")

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator:
        log.info("API server starting")
        db.init(config.get("db_path", "data/framework.db"))
        module_loader.load_all(); tool_registry.refresh()
        await scheduler.start(); yield
        await scheduler.stop()
        log.info("API server stopped")

    app = FastAPI(title="RTF API", description="RedTeam Framework v2.0 REST API", version="2.0.0", lifespan=lifespan)
    app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

    def _api_keys() -> Set[str]:
        raw = config.get("api_keys", [])
        if isinstance(raw, str): return {k.strip() for k in raw.split(",") if k.strip()}
        if isinstance(raw, list): return {str(k).strip() for k in raw if str(k).strip()}
        return set()

    def require_api_key(x_api_key: Optional[str] = Header(default=None, alias="X-API-Key")) -> None:
        allowed = _api_keys()
        if not allowed: return
        if not x_api_key or x_api_key not in allowed:
            raise HTTPException(status_code=401, detail="Unauthorized")

    def paginated(items: List, limit: int, offset: int, total: int) -> Dict:
        return {"items":items,"pagination":{"limit":limit,"offset":offset,"total":total,"has_more":offset+len(items)<total}}

    v1 = APIRouter(prefix="/api/v1")
    titan = TitanOrchestrator()

    @app.get("/health", tags=["system"])
    @v1.get("/health", tags=["system"])
    async def health():
        return {"status":"ok","framework":"RTF v2.0"}

    @app.get("/stats", tags=["system"])
    @v1.get("/stats", tags=["system"])
    async def stats():
        return {"modules":len(module_loader.list_modules()),"tools":tool_registry.summary(),"jobs":scheduler.stats()}

    @app.get("/modules", tags=["modules"])
    @v1.get("/modules", tags=["modules"])
    async def list_modules(category: Optional[str]=Query(None), _auth: None=Depends(require_api_key)):
        return module_loader.list_modules(category=category)

    @app.get("/modules/search", tags=["modules"])
    @v1.get("/modules/search", tags=["modules"])
    async def search_modules(q: str=Query(..., min_length=1), _auth: None=Depends(require_api_key)):
        return module_loader.search(q)

    @app.get("/modules/{category}/{name}", tags=["modules"])
    @v1.get("/modules/{category}/{name}", tags=["modules"])
    async def get_module(category: str, name: str, _auth: None=Depends(require_api_key)):
        path = f"{category}/{name}"
        try:
            cls = module_loader.get(path); instance = cls()
            return {"path":path,"info":instance.info(),"options":instance.show_options()}
        except Exception as exc:
            raise HTTPException(status_code=404, detail=str(exc))

    @app.post("/modules/{category}/{name}/run", tags=["modules"])
    @v1.post("/modules/{category}/{name}/run", tags=["modules"])
    async def run_module(category: str, name: str, body: "ModuleRunRequest", background_tasks: "BackgroundTasks", _auth: None=Depends(require_api_key)):
        path = f"{category}/{name}"
        try:
            cls = module_loader.get(path)
        except Exception as exc:
            raise HTTPException(status_code=404, detail=str(exc))
        job_id = str(uuid.uuid4())
        async def _run():
            instance = cls(); result = await instance.execute(body.options)
            db.finish_job(job_id, result.to_dict(), result.error)
            for f in result.findings:
                db.add_finding(job_id=job_id, target=f.target, title=f.title, category=f.category, severity=f.severity.value, description=f.description, evidence=f.evidence, tags=f.tags)
        db.create_job(job_id, name, path, body.options); db.start_job(job_id)
        background_tasks.add_task(_run)
        return {"job_id":job_id,"status":"running","module":path}

    @app.get("/workflows", tags=["workflows"])
    @v1.get("/workflows", tags=["workflows"])
    async def list_workflows(_auth: None=Depends(require_api_key)):
        return [{"name":n,"description":cls().description} for n,cls in BUILTIN_WORKFLOWS.items()]

    @app.post("/workflows/{name}/run", tags=["workflows"])
    @v1.post("/workflows/{name}/run", tags=["workflows"])
    async def run_workflow(name: str, body: "WorkflowRunRequest", background_tasks: "BackgroundTasks", _auth: None=Depends(require_api_key)):
        try:
            wf = get_workflow(name, body.options)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc))
        job_id = str(uuid.uuid4())
        db.create_job(job_id, name, f"workflow/{name}", body.options); db.start_job(job_id)
        async def _run():
            result = await wf.run(output_dir=body.output_dir)
            db.finish_job(job_id, result.to_dict())
        background_tasks.add_task(_run)
        return {"job_id":job_id,"status":"running","workflow":name}

    @app.get("/jobs", tags=["jobs"])
    @v1.get("/jobs", tags=["jobs"])
    async def list_jobs(limit: int=Query(100,ge=1,le=1000), offset: int=Query(0,ge=0), _auth: None=Depends(require_api_key)):
        items = db.list_jobs(limit=limit, offset=offset)
        return paginated(items, limit=limit, offset=offset, total=db.count_jobs())

    @app.get("/jobs/{job_id}", tags=["jobs"])
    @v1.get("/jobs/{job_id}", tags=["jobs"])
    async def get_job(job_id: str, _auth: None=Depends(require_api_key)):
        job = db.get_job(job_id)
        if not job: raise HTTPException(status_code=404, detail="Job not found")
        return job

    @app.get("/findings", tags=["findings"])
    @v1.get("/findings", tags=["findings"])
    async def list_findings(job_id: Optional[str]=None, severity: Optional[str]=None, limit: int=Query(500,ge=1,le=5000), offset: int=Query(0,ge=0), _auth: None=Depends(require_api_key)):
        items = db.list_findings(job_id=job_id, severity=severity, limit=limit, offset=offset)
        return paginated(items, limit=limit, offset=offset, total=db.count_findings(job_id=job_id, severity=severity))

    @app.get("/targets", tags=["targets"])
    @v1.get("/targets", tags=["targets"])
    async def list_targets(limit: int=Query(500,ge=1,le=5000), offset: int=Query(0,ge=0), _auth: None=Depends(require_api_key)):
        items = db.list_targets(limit=limit, offset=offset)
        return paginated(items, limit=limit, offset=offset, total=db.count_targets())

    @app.post("/targets", tags=["targets"])
    @v1.post("/targets", tags=["targets"])
    async def add_target(body: "TargetAddRequest", _auth: None=Depends(require_api_key)):
        db.add_target(body.value, body.type, body.tags)
        return {"status":"added","target":body.value}

    @app.get("/tools", tags=["tools"])
    @v1.get("/tools", tags=["tools"])
    async def list_tools(category: Optional[str]=None, installed: Optional[bool]=None, _auth: None=Depends(require_api_key)):
        cat = ToolCategory(category) if category else None
        tools = tool_registry.list_all(category=cat)
        if installed is not None: tools = [t for t in tools if t.installed==installed]
        return [t.to_dict() for t in tools]

    @app.get("/tools/summary", tags=["tools"])
    @v1.get("/tools/summary", tags=["tools"])
    async def tools_summary(_auth: None=Depends(require_api_key)):
        return tool_registry.summary()

    @app.post("/tools/{name}/install", tags=["tools"])
    @v1.post("/tools/{name}/install", tags=["tools"])
    async def install_tool(name: str, background_tasks: "BackgroundTasks", _auth: None=Depends(require_api_key)):
        if not tool_registry.get(name): raise HTTPException(status_code=404, detail=f"Unknown tool: {name}")
        background_tasks.add_task(tool_registry.install, name)
        return {"status":"installing","tool":name}

    @app.post("/tools/refresh", tags=["tools"])
    @v1.post("/tools/refresh", tags=["tools"])
    async def refresh_tools(background_tasks: "BackgroundTasks", _auth: None=Depends(require_api_key)):
        background_tasks.add_task(tool_registry.refresh)
        return {"status":"refreshing"}

    @app.get("/scheduler/jobs", tags=["scheduler"])
    @v1.get("/scheduler/jobs", tags=["scheduler"])
    async def list_scheduler_jobs(_auth: None=Depends(require_api_key)):
        return [j.to_dict() for j in scheduler.list_jobs()]

    @app.get("/titan/manifest", tags=["titan"])
    @v1.get("/titan/manifest", tags=["titan"])
    async def titan_manifest(_auth: None=Depends(require_api_key)):
        return build_titan_manifest()

    @app.get("/titan/health", tags=["titan"])
    @v1.get("/titan/health", tags=["titan"])
    async def titan_health(_auth: None=Depends(require_api_key)):
        return titan.health()

    @app.post("/titan/investigate", tags=["titan"])
    @v1.post("/titan/investigate", tags=["titan"])
    async def titan_investigate(body: "ModuleRunRequest", _auth: None=Depends(require_api_key)):
        return await titan.run_investigation(body.options)

    app.include_router(v1)
    return app


def run_server(host: Optional[str]=None, port: Optional[int]=None) -> None:
    try:
        import uvicorn
    except ImportError:
        raise ImportError("uvicorn is required: pip install uvicorn")
    _host = host or config.get("api_host","0.0.0.0")
    _port = port or int(config.get("api_port",8000))
    log.info(f"Starting API server on http://{_host}:{_port}")
    app = create_app()
    uvicorn.run(app, host=_host, port=_port, log_level="info")
