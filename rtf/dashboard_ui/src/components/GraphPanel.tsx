import { useEffect, useRef } from 'react';
import cytoscape from 'cytoscape';

export function GraphPanel({ nodes, edges }: { nodes: any[]; edges: any[] }) {
  const ref = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!ref.current) return;
    const cy = cytoscape({
      container: ref.current,
      elements: [
        ...nodes.map((node) => ({
          data: {
            id: node.id,
            label: node.label || node.value,
            type: node.entity_type,
            provenance: node.source_module,
          },
        })),
        ...edges.map((edge) => ({
          data: {
            id: edge.id,
            source: edge.source_node_id,
            target: edge.target_node_id,
            label: edge.relationship,
          },
        })),
      ],
      style: [
        {
          selector: 'node',
          style: {
            'background-color': '#2f81f7',
            'label': 'data(label)',
            'font-size': '10px',
            'color': '#dbeafe',
            'text-wrap': 'wrap',
            'text-max-width': '90px',
          },
        },
        {
          selector: 'edge',
          style: {
            'line-color': '#d14d72',
            'target-arrow-color': '#d14d72',
            'target-arrow-shape': 'triangle',
            'curve-style': 'bezier',
            'label': 'data(label)',
            'font-size': '8px',
            'color': '#9fb3c8',
          },
        },
      ],
      layout: { name: 'cose', animate: false },
    });

    cy.on('tap', 'node', (event) => {
      const data = event.target.data();
      const detail = `${data.type} • ${data.label} • ${data.provenance ?? 'manual seed'}`;
      ref.current?.setAttribute('data-selected', detail);
    });

    return () => cy.destroy();
  }, [nodes, edges]);

  return (
    <div className="graph-wrapper">
      <div ref={ref} className="graph-surface" />
    </div>
  );
}
