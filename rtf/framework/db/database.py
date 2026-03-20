"""RedTeam Framework - Database Layer (SQLite)"""
from __future__ import annotations
import json, sqlite3, threading
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional
from framework.core.logger import get_logger

log = get_logger("rtf.db")

_CREATE = """
CREATE TABLE IF NOT EXISTS jobs (
    id TEXT PRIMARY KEY, name TEXT NOT NULL, module_path TEXT,
    status TEXT NOT NULL DEFAULT 'pending', started_at DATETIME, finished_at DATETIME,
    options TEXT, result TEXT, error TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS findings (
    id INTEGER PRIMARY KEY AUTOINCREMENT, job_id TEXT REFERENCES jobs(id),
    target TEXT, severity TEXT DEFAULT 'info', category TEXT, title TEXT NOT NULL,
    description TEXT, evidence TEXT, tags TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS tool_registry (
    name TEXT PRIMARY KEY, category TEXT, install_type TEXT, binary TEXT,
    repo_url TEXT, installed INTEGER DEFAULT 0, version TEXT, last_checked DATETIME, metadata TEXT
);
CREATE TABLE IF NOT EXISTS targets (
    id INTEGER PRIMARY KEY AUTOINCREMENT, value TEXT NOT NULL UNIQUE,
    type TEXT, tags TEXT, notes TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS schedules (
    id TEXT PRIMARY KEY, name TEXT NOT NULL, module_path TEXT, cron_expr TEXT,
    interval_seconds INTEGER, options TEXT, enabled INTEGER DEFAULT 1,
    last_run DATETIME, next_run DATETIME, created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
"""

class Database:
    _instance: Optional["Database"] = None
    _lock = threading.Lock()

    def __new__(cls, db_path: Optional[str] = None) -> "Database":
        with cls._lock:
            if cls._instance is None:
                obj = super().__new__(cls)
                obj._db_path = db_path or ""
                obj._local = threading.local()
                cls._instance = obj
        return cls._instance

    def init(self, db_path: str) -> None:
        self._db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        with self._conn() as conn:
            conn.executescript(_CREATE)
        log.info(f"Database initialised at {db_path}")

    @contextmanager
    def _conn(self) -> Generator[sqlite3.Connection, None, None]:
        if not self._db_path:
            self._db_path = "data/framework.db"
            Path(self._db_path).parent.mkdir(parents=True, exist_ok=True)
        if not hasattr(self._local, "conn") or self._local.conn is None:
            self._local.conn = sqlite3.connect(
                self._db_path, detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES,
                check_same_thread=False
            )
            self._local.conn.row_factory = sqlite3.Row
            self._local.conn.execute("PRAGMA journal_mode=WAL")
            self._local.conn.execute("PRAGMA foreign_keys=ON")
        try:
            yield self._local.conn
            self._local.conn.commit()
        except Exception:
            self._local.conn.rollback()
            raise

    def execute(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        with self._conn() as conn:
            return conn.execute(sql, params)

    def fetchall(self, sql: str, params: tuple = ()) -> List[Dict[str, Any]]:
        with self._conn() as conn:
            rows = conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]

    def fetchone(self, sql: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
        with self._conn() as conn:
            row = conn.execute(sql, params).fetchone()
        return dict(row) if row else None

    def create_job(self, job_id: str, name: str, module_path: str, options: Dict) -> None:
        self.execute("INSERT INTO jobs (id,name,module_path,status,options) VALUES (?,?,?,?,?)",
                     (job_id, name, module_path, "pending", json.dumps(options)))

    def start_job(self, job_id: str) -> None:
        self.execute("UPDATE jobs SET status='running',started_at=? WHERE id=?",
                     (datetime.utcnow().isoformat(), job_id))

    def finish_job(self, job_id: str, result: Any, error: Optional[str] = None) -> None:
        status = "failed" if error else "completed"
        self.execute("UPDATE jobs SET status=?,finished_at=?,result=?,error=? WHERE id=?",
                     (status, datetime.utcnow().isoformat(),
                      json.dumps(result) if result is not None else None, error, job_id))

    def get_job(self, job_id: str) -> Optional[Dict]:
        return self.fetchone("SELECT * FROM jobs WHERE id=?", (job_id,))

    def list_jobs(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        return self.fetchall("SELECT * FROM jobs ORDER BY created_at DESC LIMIT ? OFFSET ?", (limit, offset))

    def count_jobs(self) -> int:
        row = self.fetchone("SELECT COUNT(*) AS count FROM jobs")
        return int(row["count"]) if row else 0

    def add_finding(self, job_id: str, target: str, title: str, category: str = "general",
                    severity: str = "info", description: str = "", evidence: Optional[Dict] = None,
                    tags: Optional[List[str]] = None) -> int:
        cur = self.execute(
            "INSERT INTO findings (job_id,target,severity,category,title,description,evidence,tags) VALUES (?,?,?,?,?,?,?,?)",
            (job_id, target, severity, category, title, description,
             json.dumps(evidence) if evidence else None,
             ",".join(tags) if tags else None))
        return cur.lastrowid

    def list_findings(self, job_id: Optional[str] = None, severity: Optional[str] = None,
                      limit: int = 500, offset: int = 0) -> List[Dict]:
        clauses, params = [], []
        if job_id: clauses.append("job_id=?"); params.append(job_id)
        if severity: clauses.append("severity=?"); params.append(severity)
        where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
        params.extend([limit, offset])
        return self.fetchall(f"SELECT * FROM findings {where} ORDER BY created_at DESC LIMIT ? OFFSET ?", tuple(params))

    def count_findings(self, job_id: Optional[str] = None, severity: Optional[str] = None) -> int:
        clauses, params = [], []
        if job_id: clauses.append("job_id=?"); params.append(job_id)
        if severity: clauses.append("severity=?"); params.append(severity)
        where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
        row = self.fetchone(f"SELECT COUNT(*) AS count FROM findings {where}", tuple(params))
        return int(row["count"]) if row else 0

    def add_target(self, value: str, type_: str = "domain", tags: str = "") -> None:
        self.execute("INSERT OR IGNORE INTO targets (value,type,tags) VALUES (?,?,?)", (value, type_, tags))

    def list_targets(self, limit: int = 500, offset: int = 0) -> List[Dict]:
        return self.fetchall("SELECT * FROM targets ORDER BY created_at DESC LIMIT ? OFFSET ?", (limit, offset))

    def count_targets(self) -> int:
        row = self.fetchone("SELECT COUNT(*) AS count FROM targets")
        return int(row["count"]) if row else 0

    def upsert_tool(self, name: str, **kwargs: Any) -> None:
        kwargs["name"] = name
        cols = ", ".join(kwargs.keys())
        placeholders = ", ".join(["?"] * len(kwargs))
        updates = ", ".join(f"{k}=excluded.{k}" for k in kwargs if k != "name")
        self.execute(
            f"INSERT INTO tool_registry ({cols}) VALUES ({placeholders}) ON CONFLICT(name) DO UPDATE SET {updates}",
            tuple(kwargs.values()))

    def get_tool(self, name: str) -> Optional[Dict]:
        return self.fetchone("SELECT * FROM tool_registry WHERE name=?", (name,))

    def list_tools(self, category: Optional[str] = None) -> List[Dict]:
        if category:
            return self.fetchall("SELECT * FROM tool_registry WHERE category=? ORDER BY name", (category,))
        return self.fetchall("SELECT * FROM tool_registry ORDER BY name")

db = Database()
