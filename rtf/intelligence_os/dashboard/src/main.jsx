import React from 'react'
import { createRoot } from 'react-dom/client'
import './styles.css'

const layers = [
  'Data Acquisition', 'Tool Integration', 'Processing', 'Entity Intelligence', 'Graph (Neo4j)', 'Correlation & AI', 'Pipeline Engine', 'Workflow Engine', 'Automation Engine', 'API Layer', 'Dashboard Layer'
]

function App() {
  return (
    <div className="app-shell">
      <header>
        <h1>Intelligence OS Control Plane</h1>
        <p>Analyst-facing control surface for pipelines, autonomous investigations, graph intelligence, alerts, and reporting.</p>
      </header>
      <section className="grid">
        {layers.map((layer) => (
          <article key={layer} className="card">
            <h2>{layer}</h2>
            <p>Operationally linked into the Intelligence OS execution fabric.</p>
          </article>
        ))}
      </section>
    </div>
  )
}

createRoot(document.getElementById('root')).render(<App />)
