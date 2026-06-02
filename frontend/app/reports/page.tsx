'use client';

import { useEffect, useState } from 'react';
import { Download, FileText, RefreshCcw, X } from 'lucide-react';
import AppShell from '../components/AppShell';
import { fetchIncidentReport, fetchIncidents, type Incident } from '../lib/api';

const severityColor: Record<string, string> = {
  CRITICAL: '#ef4444',
  HIGH: '#f97316',
  MEDIUM: '#eab308',
  LOW: '#22c55e',
};

export default function Reports() {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [selected, setSelected] = useState<Incident | null>(null);
  const [report, setReport] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const load = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await fetchIncidents();
      setIncidents(data);
      const active = selected ? data.find((incident) => incident.id === selected.id) ?? data[0] : data[0];
      setSelected(active ?? null);
      if (active) setReport(await fetchIncidentReport(active.id));
    } catch {
      setError('Reports are ready once an incident has been opened.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    let active = true;
    fetchIncidents()
      .then(async (data) => {
        if (!active) return;
        setIncidents(data);
        const first = data[0] ?? null;
        setSelected(first);
        setReport(first ? await fetchIncidentReport(first.id) : '');
      })
      .catch(() => {
        if (active) setError('Reports are ready once an incident has been opened.');
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, []);

  const chooseIncident = async (incident: Incident) => {
    setSelected(incident);
    setLoading(true);
    try {
      setReport(await fetchIncidentReport(incident.id));
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = () => {
    if (!selected || !report) return;
    const blob = new Blob([report], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${selected.id}-SentinelX-Report.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <AppShell active="reports" statusText="Reports ready">
      <section className="page-title-row">
        <div>
          <p className="section-label">Incident reporting</p>
          <h1>Executive-ready reports generated from live incident evidence.</h1>
        </div>
        <button className="primary-button" onClick={load} disabled={loading}>
          <RefreshCcw size={16} />
          {loading ? 'Refreshing...' : 'Refresh reports'}
        </button>
      </section>

      {error && <div className="ticker">{error}</div>}

      <section className="reports-layout">
        <div className="report-list">
          {incidents.length ? incidents.map((incident) => (
            <button
              key={incident.id}
              className={`report-card ${selected?.id === incident.id ? 'selected' : ''}`}
              onClick={() => chooseIncident(incident)}
            >
              <div className="report-icon"><FileText size={20} /></div>
              <div>
                <div className="report-meta">
                  <span>{incident.id}</span>
                  <span className="status-pill" style={{ color: severityColor[incident.severity], borderColor: `${severityColor[incident.severity]}55` }}>{incident.severity}</span>
                  <span className="status-pill" style={{ color: '#eab308', borderColor: '#eab30855' }}>{incident.status}</span>
                </div>
                <h2>{incident.title}</h2>
                <p>{new Date(incident.updated_at).toLocaleString()} / Risk {incident.risk_score}</p>
              </div>
            </button>
          )) : (
            <article className="panel">
              <p className="section-label">Reports ready</p>
              <p>Open an incident from Intake to generate an executive-ready report.</p>
            </article>
          )}
        </div>

        {selected && (
          <article className="panel report-preview">
            <div className="panel-heading">
              <div>
                <p className="section-label">Report preview</p>
                <h2>{selected.id}</h2>
              </div>
              <div className="button-row">
                <button className="secondary-button" onClick={handleDownload}>
                  <Download size={15} />
                  Download
                </button>
                <button className="icon-button" onClick={() => setSelected(null)} aria-label="Close report preview">
                  <X size={16} />
                </button>
              </div>
            </div>
            <pre>{report || 'Generating report...'}</pre>
          </article>
        )}
      </section>
    </AppShell>
  );
}
