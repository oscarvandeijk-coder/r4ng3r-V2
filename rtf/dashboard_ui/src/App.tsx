import { useEffect, useMemo, useState } from 'react';
import { GraphPanel } from './components/GraphPanel';

type DashboardSummary = any;
type ModuleRegistry = any[];
type WorkflowRegistry = { workflows: Record<string, any> };
type GraphData = { nodes: any[]; edges: any[]; schema: { entity_types: string[]; relationship_types: string[] } };
type SocmintData = any;
type VaultData = any;
type HealthData = any;
type ReportItem = any[];

const API = (import.meta.env.VITE_RTF_API as string | undefined) ?? 'http://127.0.0.1:8000';

async function fetchJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API}${path}`);
  if (!response.ok) throw new Error(`Failed to load ${path}`);
  return response.json();
}

function StatCard({ label, value, accent = 'blue' }: { label: string; value: string | number; accent?: 'blue' | 'red' | 'green' | 'amber' }) {
  return (
    <div className={`stat-card accent-${accent}`}>
      <div className="stat-value">{value}</div>
      <div className="stat-label">{label}</div>
    </div>
  );
}

function Section({ title, subtitle, children }: { title: string; subtitle?: string; children: React.ReactNode }) {
  return (
    <section className="panel section-panel">
      <div className="section-header">
        <div>
          <h2>{title}</h2>
          {subtitle && <p>{subtitle}</p>}
        </div>
      </div>
      {children}
    </section>
  );
}

export default function App() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [modules, setModules] = useState<ModuleRegistry>([]);
  const [workflowData, setWorkflowData] = useState<WorkflowRegistry | null>(null);
  const [graph, setGraph] = useState<GraphData | null>(null);
  const [socmint, setSocmint] = useState<SocmintData | null>(null);
  const [vault, setVault] = useState<VaultData | null>(null);
  const [health, setHealth] = useState<HealthData | null>(null);
  const [reports, setReports] = useState<ReportItem>([]);
  const [eventFeed, setEventFeed] = useState<any[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [selectedNodeType, setSelectedNodeType] = useState<string>('all');
  const [moduleFilter, setModuleFilter] = useState('');
  const [terminalInput, setTerminalInput] = useState('help');
  const [terminalTranscript, setTerminalTranscript] = useState('');
  const [reportFormat, setReportFormat] = useState('html');

  useEffect(() => {
    void Promise.all([
      fetchJson<DashboardSummary>('/dashboard/summary'),
      fetchJson<ModuleRegistry>('/modules'),
      fetchJson<WorkflowRegistry>('/dashboard/workflows'),
      fetchJson<GraphData>('/dashboard/graph'),
      fetchJson<SocmintData>('/dashboard/socmint'),
      fetchJson<VaultData>('/dashboard/vault'),
      fetchJson<HealthData>('/dashboard/health'),
      fetchJson<ReportItem>('/dashboard/reports'),
      fetchJson<any[]>('/dashboard/events'),
    ]).then(([summaryData, modulesData, workflowRegistry, graphData, socmintData, vaultData, healthData, reportData, eventsData]) => {
      setSummary(summaryData);
      setModules(modulesData);
      setWorkflowData(workflowRegistry);
      setGraph(graphData);
      setSocmint(socmintData);
      setVault(vaultData);
      setHealth(healthData);
      setReports(reportData);
      setEventFeed(eventsData);
    });
  }, []);

  useEffect(() => {
    const socket = new WebSocket(`${API.replace('http', 'ws')}/ws/events`);
    socket.onmessage = (event) => {
      const payload = JSON.parse(event.data);
      if (payload.type === 'snapshot') {
        setEventFeed(payload.events);
      }
      if (payload.type === 'event') {
        setEventFeed((current) => [payload.data, ...current].slice(0, 200));
      }
    };
    return () => socket.close();
  }, []);

  const filteredModules = useMemo(() => modules.filter((module) => {
    const categoryOk = selectedCategory === 'all' || module.category === selectedCategory;
    const searchOk = JSON.stringify(module).toLowerCase().includes(moduleFilter.toLowerCase());
    return categoryOk && searchOk;
  }), [modules, selectedCategory, moduleFilter]);

  const graphNodes = useMemo(() => {
    if (!graph) return [];
    return selectedNodeType === 'all' ? graph.nodes : graph.nodes.filter((node) => node.entity_type === selectedNodeType);
  }, [graph, selectedNodeType]);

  async function runModule(path: string) {
    await fetch(`${API}/modules/${path}/run`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ operation_id: 'primary', options: { target: 'example.com' } }),
    });
  }

  async function runWorkflow(name: string) {
    await fetch(`${API}/workflows/${name}/run`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ operation_id: 'primary', options: { target: 'example.com' } }),
    });
  }

  async function sendTerminal() {
    const response = await fetch(`${API}/dashboard/terminal/command`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ command: terminalInput, workspace: 'default' }),
    });
    const data = await response.json();
    setTerminalTranscript(data.transcript);
  }

  async function generateReport() {
    const response = await fetch(`${API}/dashboard/reports`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title: 'RTF Operations Summary', format: reportFormat, operation_id: 'primary', metadata: { operator: 'dashboard' } }),
    });
    const data = await response.json();
    setReports((current) => [data, ...current]);
  }

  const categories = summary?.module_categories ?? [];

  return (
    <div className="app-shell">
      <aside className="sidebar panel">
        <div className="brand">
          <div className="brand-mark">RTF</div>
          <div>
            <strong>Operations Grid</strong>
            <span>Palantir-style command surface</span>
          </div>
        </div>
        <div className="sidebar-section">
          <span className="sidebar-label">Mission Controls</span>
          <button>⌘ Command Center</button>
          <button>⌥ Graph Intel</button>
          <button>⇧ Pipelines</button>
          <button>⌃ Vault & Reports</button>
        </div>
        <div className="sidebar-section">
          <span className="sidebar-label">Keyboard</span>
          <p>G Graph focus</p>
          <p>M Module search</p>
          <p>W Workflow launch</p>
          <p>T Terminal command</p>
        </div>
      </aside>

      <main className="main-grid">
        <Section title="Operation Command Center" subtitle="Real framework telemetry mapped into an operator-first layout.">
          <div className="stats-grid">
            <StatCard label="Loaded Modules" value={summary?.metrics.modules ?? '--'} accent="blue" />
            <StatCard label="Categories" value={summary?.metrics.categories ?? '--'} accent="green" />
            <StatCard label="Findings" value={summary?.metrics.findings_total ?? '--'} accent="red" />
            <StatCard label="Graph Nodes" value={summary?.metrics.graph_nodes ?? '--'} accent="amber" />
            <StatCard label="Graph Edges" value={summary?.metrics.graph_edges ?? '--'} accent="blue" />
            <StatCard label="Queue Depth" value={summary?.metrics.scheduler_queue_depth ?? '--'} accent="red" />
          </div>
          <div className="two-column">
            <div>
              <h3>Active Operations</h3>
              <div className="list-stack">
                {(summary?.operations ?? []).map((operation: any) => (
                  <div key={operation.id} className="list-item">
                    <div>
                      <strong>{operation.name}</strong>
                      <span>{operation.summary}</span>
                    </div>
                    <span className={`pill pill-${operation.status}`}>{operation.status}</span>
                  </div>
                ))}
              </div>
            </div>
            <div>
              <h3>Recent Jobs</h3>
              <div className="list-stack scrollable">
                {(summary?.recent_jobs ?? []).map((job: any) => (
                  <div key={job.id} className="list-item mono">
                    <div>
                      <strong>{job.name}</strong>
                      <span>{job.module_path}</span>
                    </div>
                    <span className={`pill pill-${job.status}`}>{job.status}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </Section>

        <Section title="Graph Intelligence View" subtitle="Digital twin of targets, identities, infrastructure, and artifacts.">
          <div className="toolbar">
            <select value={selectedNodeType} onChange={(event) => setSelectedNodeType(event.target.value)}>
              <option value="all">All entity types</option>
              {(graph?.schema.entity_types ?? []).map((entityType) => <option key={entityType}>{entityType}</option>)}
            </select>
            <div className="hint">Right-click actions, provenance, and expansion are backed by the graph API schema.</div>
          </div>
          <GraphPanel nodes={graphNodes} edges={graph?.edges ?? []} />
          <div className="timeline-strip">
            {(summary?.recent_events ?? []).slice(0, 6).map((event: any) => (
              <div key={event.id} className="timeline-item">
                <span>{event.event_type}</span>
                <strong>{event.message}</strong>
              </div>
            ))}
          </div>
        </Section>

        <Section title="Module Control Center" subtitle="Registry auto-loaded from framework/modules/loader.py with live options.">
          <div className="toolbar">
            <select value={selectedCategory} onChange={(event) => setSelectedCategory(event.target.value)}>
              <option value="all">All categories</option>
              {categories.map((category: string) => <option key={category}>{category}</option>)}
            </select>
            <input value={moduleFilter} onChange={(event) => setModuleFilter(event.target.value)} placeholder="Search modules, descriptions, options" />
          </div>
          <div className="module-grid">
            {filteredModules.map((module) => (
              <div key={module.path} className="module-card">
                <div className="module-topline">
                  <span className="pill pill-neutral">{module.category}</span>
                  <span className="small-code">{module.path}</span>
                </div>
                <h3>{module.info.name}</h3>
                <p>{module.description}</p>
                <div className="option-list">
                  {module.options.slice(0, 4).map((option: any) => (
                    <span key={option.name} className="option-chip">{option.name}</span>
                  ))}
                </div>
                <div className="card-actions">
                  <button onClick={() => runModule(module.path)}>Run Once</button>
                  <button className="secondary">Schedule</button>
                  <button className="secondary">Attach</button>
                </div>
              </div>
            ))}
          </div>
        </Section>

        <div className="split-grid">
          <Section title="Workflow / Pipeline Builder" subtitle="Built around the framework’s real workflows and step DAGs.">
            <div className="workflow-list">
              {Object.values(workflowData?.workflows ?? {}).map((workflow: any) => (
                <div key={workflow.name} className="workflow-card">
                  <div className="workflow-header">
                    <strong>{workflow.name}</strong>
                    <button onClick={() => runWorkflow(workflow.name)}>Launch</button>
                  </div>
                  <p>{workflow.description}</p>
                  <div className="workflow-steps">
                    {workflow.steps.map((step: any) => <span key={step.name}>{step.name}</span>)}
                  </div>
                </div>
              ))}
            </div>
          </Section>

          <Section title="SOCMINT Investigation Panel" subtitle="15-stage pipeline with AI identity fusion, stylometry, and cluster formation.">
            <div className="socmint-stages">
              {(socmint?.stages ?? []).map((stage: any) => (
                <div key={stage.code} className="stage-row">
                  <span className="pill pill-neutral">{stage.code}</span>
                  <div>
                    <strong>{stage.name}</strong>
                    <p>{JSON.stringify(stage.summary)}</p>
                  </div>
                </div>
              ))}
            </div>
            <div className="cluster-box">
              {(socmint?.identity_clusters ?? []).map((cluster: any) => (
                <div key={cluster.cluster_id} className="cluster-card">
                  <strong>{cluster.cluster_id}</strong>
                  <span>Confidence {Math.round(cluster.confidence * 100)}%</span>
                  <p>{cluster.entities.join(' • ')}</p>
                </div>
              ))}
            </div>
          </Section>
        </div>

        <div className="split-grid">
          <Section title="Live Terminal" subtitle="Metasploit-style sessions, creds, notes, and resource scripts surfaced inside the UI.">
            <div className="terminal-box">
              <pre>{terminalTranscript || 'Awaiting command...'}</pre>
            </div>
            <div className="toolbar">
              <input value={terminalInput} onChange={(event) => setTerminalInput(event.target.value)} placeholder="sessions | creds | notes | resource ops.rc" />
              <button onClick={() => void sendTerminal()}>Execute</button>
            </div>
          </Section>

          <Section title="Event Stream" subtitle="SIEM-style stream from modules, workflows, scheduler, and terminal actions.">
            <div className="event-stream">
              {eventFeed.slice(0, 18).map((event: any, index) => (
                <div key={event.id ?? index} className={`event-row sev-${event.severity ?? 'info'}`}>
                  <span>{event.event_type}</span>
                  <strong>{event.message}</strong>
                  <small>{event.source}</small>
                </div>
              ))}
            </div>
          </Section>
        </div>

        <div className="split-grid">
          <Section title="Data Vault" subtitle="Entities, credentials, findings, and artifacts linked back to graph nodes.">
            <div className="vault-grid">
              <div>
                <h3>Credentials</h3>
                {(vault?.credentials ?? []).slice(0, 6).map((cred: any) => <div key={cred.id} className="list-item"><strong>{cred.username}</strong><span>{cred.kind}</span></div>)}
              </div>
              <div>
                <h3>Artifacts</h3>
                {(vault?.artifacts ?? []).slice(0, 6).map((artifact: any) => <div key={artifact.id} className="list-item"><strong>{artifact.name}</strong><span>{artifact.artifact_type}</span></div>)}
              </div>
              <div>
                <h3>Findings</h3>
                {(vault?.findings ?? []).slice(0, 6).map((finding: any) => <div key={finding.id} className="list-item"><strong>{finding.title}</strong><span>{finding.severity}</span></div>)}
              </div>
            </div>
          </Section>

          <Section title="Reporting + Health" subtitle="Generate multi-format reports and verify tool, worker, scheduler, and database health.">
            <div className="toolbar">
              <select value={reportFormat} onChange={(event) => setReportFormat(event.target.value)}>
                <option value="html">HTML</option>
                <option value="pdf">PDF</option>
                <option value="xlsx">XLSX</option>
                <option value="md">Markdown</option>
                <option value="json">JSON</option>
              </select>
              <button onClick={() => void generateReport()}>Generate Report</button>
            </div>
            <div className="report-list">
              {reports.slice(0, 5).map((report: any, index: number) => (
                <div key={report.id ?? index} className="list-item">
                  <strong>{report.title ?? report.path}</strong>
                  <span>{report.format ?? 'generated'}</span>
                </div>
              ))}
            </div>
            <div className="health-grid">
              <StatCard label="Installed Tools" value={health?.tool_summary?.installed ?? '--'} accent="green" />
              <StatCard label="Missing Tools" value={health?.tool_summary?.missing ?? '--'} accent="red" />
              <StatCard label="Scheduler Total Jobs" value={health?.worker_status?.total ?? '--'} accent="amber" />
              <StatCard label="DB Status" value={health?.database?.status ?? '--'} accent="blue" />
            </div>
          </Section>
        </div>
      </main>
    </div>
  );
}
