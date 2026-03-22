"""RedTeam Framework v2.0 - Web Dashboard"""
from __future__ import annotations
import json
from typing import Any, Dict

try:
    from flask import Flask, render_template_string, jsonify, request
    _HAS_FLASK = True
except ImportError:
    _HAS_FLASK = False

from framework.core.config import config
from framework.core.logger import get_logger
from framework.db.database import db
from framework.modules.loader import module_loader
from framework.registry.tool_registry import tool_registry
from framework.titan import TitanOrchestrator
from framework.workflows.engine import BUILTIN_WORKFLOWS

log = get_logger("rtf.dashboard")

_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>RTF Dashboard v2.0</title>
<script src="https://cdn.tailwindcss.com"></script>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>body{background:#0a0a0a;color:#e0e0e0;font-family:'Courier New',monospace;}</style>
</head><body>
<nav style="background:#111;border-bottom:3px solid #dc2626;padding:12px 24px;display:flex;align-items:center;justify-content:space-between;">
  <div style="display:flex;align-items:center;gap:12px;">
    <span style="color:#dc2626;font-size:24px;font-weight:bold;">⚔</span>
    <span style="color:#dc2626;font-weight:bold;font-size:16px;letter-spacing:3px;">REDTEAM FRAMEWORK v2.0</span>
  </div>
  <div style="font-size:12px;color:#4cc9f0;">API: http://{{ api_host }}:{{ api_port }}</div>
</nav>
<div style="max-width:1200px;margin:0 auto;padding:24px;">
  <section style="margin-bottom:32px;">
    <h2 style="color:#dc2626;font-size:18px;margin-bottom:16px;">System Overview</h2>
    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:16px;">
      {% for card in stats_cards %}
      <div style="background:#111;border:1px solid #333;border-radius:8px;padding:16px;text-align:center;">
        <div style="font-size:32px;font-weight:bold;color:#dc2626;">{{ card.value }}</div>
        <div style="font-size:11px;color:#888;margin-top:4px;">{{ card.label }}</div>
      </div>{% endfor %}
    </div>
  </section>
  <section style="margin-bottom:32px;display:grid;grid-template-columns:1fr 1fr;gap:24px;">
    <div style="background:#111;border:1px solid #333;border-radius:8px;padding:20px;">
      <h3 style="color:#dc2626;margin-bottom:12px;">Tools by Category</h3>
      <canvas id="toolsChart" height="220"></canvas>
    </div>
    <div style="background:#111;border:1px solid #333;border-radius:8px;padding:20px;">
      <h3 style="color:#dc2626;margin-bottom:12px;">Installation Status</h3>
      <canvas id="installChart" height="220"></canvas>
    </div>
  </section>
  <section style="margin-bottom:32px;">
    <h2 style="color:#dc2626;font-size:18px;margin-bottom:16px;">RTF TITAN Service Health</h2>
    <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px;">
      {% for svc in titan_health.services %}
      <div style="background:#111;border:1px solid #333;border-radius:8px;padding:14px;">
        <div style="color:#4cc9f0;font-weight:bold;">{{ svc.name }}</div>
        <div style="color:#16a34a;font-size:11px;margin-top:4px;">{{ svc.status|upper }}</div>
        <div style="color:#888;font-size:11px;margin-top:6px;">Queue depth: {{ svc.queue_depth }}</div>
      </div>{% endfor %}
    </div>
  </section>
  <section style="margin-bottom:32px;">
    <h2 style="color:#dc2626;font-size:18px;margin-bottom:16px;">Modules ({{ modules|length }})</h2>
    <input id="mod-search" placeholder="Search modules…" onkeyup="filterTable('modules-table',this.value)" style="background:#1a1a1a;border:1px solid #333;border-radius:4px;padding:6px 12px;color:#e0e0e0;margin-bottom:12px;width:280px;">
    <div style="overflow-x:auto;">
      <table id="modules-table" style="width:100%;font-size:12px;border-collapse:collapse;">
        <thead><tr style="border-bottom:1px solid #333;color:#888;">
          <th style="text-align:left;padding:8px;">Path</th><th style="text-align:left;padding:8px;">Category</th>
          <th style="text-align:left;padding:8px;">Description</th><th style="padding:8px;">Action</th>
        </tr></thead>
        <tbody>{% for m in modules %}
          <tr style="border-bottom:1px solid #1a1a1a;">
            <td style="padding:8px;color:#4cc9f0;font-weight:bold;">{{ m.path }}</td>
            <td style="padding:8px;"><span style="background:#333;padding:2px 8px;border-radius:10px;font-size:10px;">{{ m.category }}</span></td>
            <td style="padding:8px;color:#888;font-size:11px;">{{ m.description[:60] }}</td>
            <td style="padding:8px;text-align:center;"><button onclick="runModule('{{ m.path }}')" style="background:#dc2626;color:white;border:none;padding:3px 10px;border-radius:4px;cursor:pointer;font-size:10px;">Run</button></td>
          </tr>{% endfor %}
        </tbody>
      </table>
    </div>
  </section>
  <section style="margin-bottom:32px;">
    <h2 style="color:#dc2626;font-size:18px;margin-bottom:16px;">Findings ({{ findings|length }})</h2>
    <div style="overflow-x:auto;">
      <table style="width:100%;font-size:12px;border-collapse:collapse;">
        <thead><tr style="border-bottom:1px solid #333;color:#888;"><th style="text-align:left;padding:8px;">Severity</th><th style="text-align:left;padding:8px;">Title</th><th style="text-align:left;padding:8px;">Target</th><th style="text-align:left;padding:8px;">Date</th></tr></thead>
        <tbody>{% for f in findings %}
          {% set sev_colors = {"critical":"#dc2626","high":"#ea580c","medium":"#d97706","low":"#16a34a","info":"#2563eb"} %}
          <tr style="border-bottom:1px solid #1a1a1a;">
            <td style="padding:8px;"><span style="background:{{ sev_colors.get(f.severity,'#888') }};color:white;padding:2px 8px;border-radius:10px;font-size:10px;font-weight:bold;">{{ f.severity|upper }}</span></td>
            <td style="padding:8px;color:#e0e0e0;">{{ f.title[:55] }}</td>
            <td style="padding:8px;color:#4cc9f0;font-size:11px;">{{ f.target[:25] }}</td>
            <td style="padding:8px;color:#555;font-size:11px;">{{ f.created_at[:16] if f.created_at else '' }}</td>
          </tr>{% endfor %}
          {% if not findings %}<tr><td colspan="4" style="padding:24px;text-align:center;color:#555;">No findings yet.</td></tr>{% endif %}
        </tbody>
      </table>
    </div>
  </section>
  <section style="margin-bottom:32px;">
    <h2 style="color:#dc2626;font-size:18px;margin-bottom:16px;">Workflows</h2>
    <div style="display:grid;grid-template-columns:repeat(2,1fr);gap:16px;">
      {% for wf_name, wf_class in workflows.items() %}
      <div style="background:#111;border:1px solid #333;border-radius:8px;padding:20px;">
        <div style="font-weight:bold;color:#4cc9f0;font-size:14px;margin-bottom:4px;">{{ wf_name }}</div>
        <div style="color:#888;font-size:12px;margin-bottom:12px;">{{ wf_class().description }}</div>
        <button onclick="launchWorkflow('{{ wf_name }}')" style="background:#dc2626;color:white;border:none;padding:6px 16px;border-radius:4px;cursor:pointer;font-size:12px;width:100%;">Launch</button>
      </div>{% endfor %}
    </div>
  </section>
  <section>
    <h2 style="color:#dc2626;font-size:18px;margin-bottom:16px;">Recent Jobs</h2>
    {% for j in jobs %}
    {% set status_color = {"completed":"#16a34a","failed":"#dc2626","running":"#d97706"}.get(j.status,"#888") %}
    <div style="background:#111;border:1px solid #333;border-radius:4px;padding:10px 16px;margin-bottom:6px;display:flex;justify-content:space-between;align-items:center;">
      <div><span style="font-weight:bold;color:#e0e0e0;">{{ j.name }}</span> <span style="color:#555;font-size:11px;">{{ j.id[:8] }}…</span></div>
      <div style="display:flex;gap:16px;align-items:center;">
        <span style="color:#555;font-size:11px;">{{ j.created_at[:16] if j.created_at else '' }}</span>
        <span style="color:{{ status_color }};font-size:11px;font-weight:bold;">{{ j.status|upper }}</span>
      </div>
    </div>{% endfor %}
    {% if not jobs %}<p style="color:#555;text-align:center;padding:24px;">No jobs yet.</p>{% endif %}
  </section>
</div>
<div id="modal" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,0.85);display:flex;align-items:center;justify-content:center;z-index:50;">
  <div style="background:#111;border:1px solid #dc2626;border-radius:8px;padding:24px;width:100%;max-width:480px;">
    <div style="display:flex;justify-content:space-between;margin-bottom:16px;"><h3 id="modal-title" style="color:#dc2626;font-size:16px;"></h3><button onclick="closeModal()" style="color:#888;background:none;border:none;cursor:pointer;font-size:20px;">&times;</button></div>
    <textarea id="modal-opts" rows="6" style="width:100%;background:#1a1a1a;border:1px solid #333;border-radius:4px;padding:8px;color:#e0e0e0;font-family:monospace;font-size:12px;" placeholder='{ "target": "example.com" }'></textarea>
    <button id="modal-submit" onclick="submitModal()" style="background:#dc2626;color:white;width:100%;margin-top:12px;padding:8px;border:none;border-radius:4px;cursor:pointer;font-weight:bold;">Execute</button>
    <div id="modal-result" style="margin-top:8px;font-size:12px;color:#16a34a;display:none;"></div>
  </div>
</div>
<script>
const API='http://{{ api_host }}:{{ api_port }}';
let _currentModule=null,_currentWorkflow=null;
function filterTable(id,q){document.querySelectorAll(`#${id} tbody tr`).forEach(r=>{r.style.display=r.textContent.toLowerCase().includes(q.toLowerCase())?'':' none';});}
function runModule(p){_currentModule=p;_currentWorkflow=null;document.getElementById('modal-title').textContent='Run: '+p;document.getElementById('modal').style.display='flex';document.getElementById('modal-result').style.display='none';}
function launchWorkflow(n){_currentWorkflow=n;_currentModule=null;document.getElementById('modal-title').textContent='Workflow: '+n;document.getElementById('modal').style.display='flex';document.getElementById('modal-result').style.display='none';}
function closeModal(){document.getElementById('modal').style.display='none';}
async function submitModal(){
  let opts={};try{opts=JSON.parse(document.getElementById('modal-opts').value||'{}');}catch(e){alert('Invalid JSON');return;}
  const el=document.getElementById('modal-result');el.style.display='block';
  try{
    let url,body;
    if(_currentModule){const[cat,name]=_currentModule.split('/');url=`${API}/modules/${cat}/${name}/run`;body={options:opts};}
    else{url=`${API}/workflows/${_currentWorkflow}/run`;body={options:opts};}
    const r=await fetch(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
    const d=await r.json();el.textContent='Job submitted: '+d.job_id;
  }catch(e){el.style.color='#dc2626';el.textContent='Error: '+e.message;}
}
const toolData={{ tool_chart_data|tojson }};
new Chart(document.getElementById('toolsChart'),{type:'bar',data:{labels:toolData.labels,datasets:[{label:'Total',data:toolData.total,backgroundColor:'#374151'},{label:'Installed',data:toolData.installed,backgroundColor:'#dc2626'}]},options:{responsive:true,plugins:{legend:{labels:{color:'#9ca3af'}}},scales:{x:{ticks:{color:'#9ca3af'},grid:{color:'#1f2937'}},y:{ticks:{color:'#9ca3af'},grid:{color:'#1f2937'}}}}});
const instData={{ install_chart_data|tojson }};
new Chart(document.getElementById('installChart'),{type:'doughnut',data:{labels:['Installed','Missing'],datasets:[{data:[instData.installed,instData.missing],backgroundColor:['#16a34a','#dc2626'],borderColor:'#111'}]},options:{responsive:true,plugins:{legend:{labels:{color:'#9ca3af'}}}}});
setInterval(async()=>{try{await fetch(`${API}/jobs?limit=5`);}catch{}},10000);
document.getElementById('modal').addEventListener('click',function(e){if(e.target===this)closeModal();});
</script>
</body></html>"""

def create_dashboard() -> "Flask":
    if not _HAS_FLASK:
        raise ImportError("flask is required: pip install flask")
    app = Flask(__name__)
    titan = TitanOrchestrator()
    db.init(config.get("db_path","data/framework.db"))
    tool_registry.refresh(); module_loader.load_all()

    @app.route("/")
    def index():
        modules = module_loader.list_modules()
        tools = [t.to_dict() for t in tool_registry.list_all()]
        findings = db.list_findings(limit=200)
        jobs = db.list_jobs(limit=30)
        tool_summary = tool_registry.summary()
        titan_health = titan.health()
        stats_cards = [{"label":"Modules Loaded","value":len(modules)},{"label":"Tools Registered","value":len(tools)},{"label":"Tools Installed","value":sum(1 for t in tools if t["installed"])},{"label":"TITAN Services","value":titan_health["service_count"]}]
        by_cat = tool_summary.get("by_category",{})
        tool_chart_data = {"labels":list(by_cat.keys()),"total":[v["total"] for v in by_cat.values()],"installed":[v["installed"] for v in by_cat.values()]}
        install_chart_data = {"installed":tool_summary.get("installed",0),"missing":tool_summary.get("missing",0)}
        return render_template_string(_TEMPLATE, modules=modules, tools=tools, findings=findings, jobs=jobs, workflows=BUILTIN_WORKFLOWS, stats_cards=stats_cards, tool_chart_data=tool_chart_data, install_chart_data=install_chart_data, titan_health=titan_health, api_host=config.get("api_host","localhost"), api_port=config.get("api_port",8000))

    @app.route("/api/jobs")
    def api_jobs(): return jsonify(db.list_jobs(limit=50))

    @app.route("/api/findings")
    def api_findings(): return jsonify(db.list_findings(limit=200))

    return app

def run_dashboard(host=None, port=None):
    _host=host or config.get("dashboard_host","0.0.0.0")
    _port=port or int(config.get("dashboard_port",5000))
    log.info(f"Starting dashboard on http://{_host}:{_port}")
    app=create_dashboard()
    app.run(host=_host, port=_port, debug=False)
