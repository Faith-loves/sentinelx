'use client';

import { useEffect, useMemo, useState } from 'react';
import { ArrowUpRight, Crosshair, X } from 'lucide-react';
import AppShell from '../components/AppShell';
import { fetchIncidents, type Incident } from '../lib/api';

const severityColor: Record<string, string> = {
  CRITICAL: '#ef4444',
  HIGH: '#f97316',
  MEDIUM: '#eab308',
  LOW: '#22c55e',
};

type PositionedNode = {
  id: string;
  label: string;
  type: string;
  risk?: number;
  x: number;
  y: number;
};

export default function Investigate() {
  const [incident, setIncident] = useState<Incident | null>(null);
  const [selectedNode, setSelectedNode] = useState<PositionedNode | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchIncidents()
      .then((incidents) => {
        const active = incidents[0] ?? null;
        setIncident(active);
        setSelectedNode(null);
      })
      .catch(() => setError('Portfolio preview is ready. Live incident data will appear after the backend is deployed.'));
  }, []);

  const nodes = useMemo<PositionedNode[]>(() => {
    const sourceNodes = incident?.graph?.nodes ?? [];
    const width = 700;
    const centerY = 205;
    return sourceNodes.map((node, index) => ({
      ...node,
      type: node.type || 'node',
      x: 70 + index * (width / Math.max(sourceNodes.length - 1, 1)),
      y: centerY + (index % 2 === 0 ? -62 : 62),
    }));
  }, [incident]);

  const nodeById = useMemo(() => new Map(nodes.map((node) => [node.id, node])), [nodes]);
  const edges = incident?.graph?.edges ?? [];
  const timeline = incident?.timeline ?? [];

  return (
    <AppShell active="investigate" statusText={incident ? `Active incident / ${incident.id}` : 'Investigation workspace'}>
      <section className="page-title-row">
        <div>
          <p className="section-label">Attack graph visualization</p>
          <h1>{incident ? incident.title : 'Ingest data to reconstruct an intrusion path.'}</h1>
        </div>
        <div className="summary-strip">
          <span>{timeline.length} events</span>
          <span>{nodes.length} nodes</span>
          <span>{incident ? `Risk ${incident.risk_score}` : 'Ready'}</span>
        </div>
      </section>

      {error && <div className="ticker">{error}</div>}

      {!incident ? (
        <article className="panel">
          <p className="section-label">Investigation ready</p>
          <h2>Deploy the backend or run the simulation to populate the live attack graph.</h2>
        </article>
      ) : (
        <section className="investigation-layout">
          <article className="panel graph-panel">
            <svg width="100%" viewBox="0 0 780 410" role="img" aria-label="Attack path graph">
              <defs>
                <marker id="arrow-active" markerWidth="9" markerHeight="9" refX="8" refY="4.5" orient="auto">
                  <path d="M0,0 L0,9 L9,4.5 z" fill="#38bdf8" />
                </marker>
              </defs>
              {edges.map((edge, index) => {
                const from = nodeById.get(edge.from);
                const to = nodeById.get(edge.to);
                if (!from || !to) return null;
                return (
                  <g key={`${edge.from}-${edge.to}-${index}`}>
                    <line x1={from.x} y1={from.y} x2={to.x} y2={to.y} stroke="#38bdf8" strokeWidth={2.2} markerEnd="url(#arrow-active)" />
                    <text x={(from.x + to.x) / 2} y={(from.y + to.y) / 2 - 14} textAnchor="middle" fill="#9fb3c8" fontSize="10">
                      {edge.label}
                    </text>
                  </g>
                );
              })}
              {nodes.map((node) => {
                const selected = selectedNode?.id === node.id;
                const color = node.type === 'alert' ? severityColor[incident.severity] : '#38bdf8';
                return (
                  <g key={node.id} className="graph-node" onClick={() => setSelectedNode(selected ? null : node)}>
                    <circle cx={node.x} cy={node.y} r={selected ? 36 : 31} fill={selected ? '#102033' : '#0b1423'} stroke={selected ? '#38bdf8' : color} strokeWidth={selected ? 3 : 2} />
                    <text x={node.x} y={node.y - 5} textAnchor="middle" fill="#f8fafc" fontSize="12" fontWeight="700">{node.label}</text>
                    <text x={node.x} y={node.y + 12} textAnchor="middle" fill="#94a3b8" fontSize="10">{node.type}</text>
                  </g>
                );
              })}
            </svg>
            {selectedNode && (
              <div className="node-detail">
                <div className="panel-heading compact">
                  <div>
                    <p className="section-label">{selectedNode.type}</p>
                    <h2>{selectedNode.label}</h2>
                  </div>
                  <button className="icon-button" onClick={() => setSelectedNode(null)} aria-label="Close node detail"><X size={16} /></button>
                </div>
                <div className="detail-grid">
                  <div><span>ID</span><strong>{selectedNode.id}</strong></div>
                  <div><span>Risk</span><strong>{selectedNode.risk ?? incident.risk_score}</strong></div>
                  <div><span>Incident</span><strong>{incident.id}</strong></div>
                  <div><span>Status</span><strong>{incident.status}</strong></div>
                </div>
              </div>
            )}
          </article>

          <aside className="steps-panel">
            {timeline.map((event, index) => (
              <article className="step-card" key={`${event.id}-${index}`}>
                <span><Crosshair size={14} /> Event {index + 1}</span>
                <strong>{event.event_type.replace(/_/g, ' ')}</strong>
                <small>{event.mitre_technique || event.timestamp}</small>
                <p>{event.description}</p>
              </article>
            ))}

            <article className="panel ai-verdict">
              <p className="section-label">AI verdict</p>
              <h2>{incident.severity} incident</h2>
              <p>{incident.summary}</p>
              <a className="text-link" href="/assistant">Investigate with AI <ArrowUpRight size={14} /></a>
            </article>
          </aside>
        </section>
      )}
    </AppShell>
  );
}
