'use client';

import type { FormEvent } from 'react';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { FilePlus2 } from 'lucide-react';
import AppShell from '../components/AppShell';
import { createIncident, getToken, type IncidentEvidence } from '../lib/api';

const defaultEvidence: IncidentEvidence[] = [
  {
    event_type: 'analyst_evidence',
    description: 'Suspicious activity observed by analyst.',
  },
];

export default function IntakePage() {
  const router = useRouter();
  const [title, setTitle] = useState('');
  const [severity, setSeverity] = useState('HIGH');
  const [sourceIp, setSourceIp] = useState('');
  const [summary, setSummary] = useState('');
  const [evidenceText, setEvidenceText] = useState(JSON.stringify(defaultEvidence, null, 2));
  const [recommendations, setRecommendations] = useState('Validate the evidence and scope affected systems.\nPreserve logs and isolate impacted assets if needed.');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const submit = async (event?: FormEvent<HTMLFormElement>) => {
    event?.preventDefault();
    if (!getToken()) {
      router.push('/login?next=/intake');
      return;
    }
    setLoading(true);
    setError('');
    try {
      const evidence = JSON.parse(evidenceText) as IncidentEvidence[];
      const incident = await createIncident({
        title,
        severity,
        source_ip: sourceIp || 'unknown',
        summary,
        evidence,
        recommendations: recommendations.split('\n').map((item) => item.trim()).filter(Boolean),
      });
      router.push(`/investigate?incident=${encodeURIComponent(incident.id)}`);
    } catch {
      setError('Could not create the incident. Check that the evidence is valid JSON, then try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <AppShell active="intake" statusText="Real incident intake">
      <section className="page-title-row">
        <div>
          <p className="section-label">Incident intake</p>
          <h1>Open a real investigation from analyst-submitted evidence.</h1>
        </div>
      </section>

      <form className="reports-layout" onSubmit={submit}>
        <article className="panel">
          <div className="auth-form">
            <label>
              Incident title
              <input value={title} onChange={(event) => setTitle(event.target.value)} placeholder="Suspicious privileged login on finance server" />
            </label>
            <label>
              Severity
              <select value={severity} onChange={(event) => setSeverity(event.target.value)}>
                <option>CRITICAL</option>
                <option>HIGH</option>
                <option>MEDIUM</option>
                <option>LOW</option>
              </select>
            </label>
            <label>
              Source IP or primary actor
              <input value={sourceIp} onChange={(event) => setSourceIp(event.target.value)} placeholder="10.0.0.45 or unknown" />
            </label>
            <label>
              Executive summary
              <textarea value={summary} onChange={(event) => setSummary(event.target.value)} placeholder="What happened, when, and why it matters." />
            </label>
            <label>
              Recommendations
              <textarea value={recommendations} onChange={(event) => setRecommendations(event.target.value)} />
            </label>
          </div>
        </article>

        <article className="panel">
          <p className="section-label">Evidence JSON</p>
          <textarea className="code-input" value={evidenceText} onChange={(event) => setEvidenceText(event.target.value)} />
          {error && <p className="form-error">{error}</p>}
          <button className="primary-button" type="submit" disabled={loading || !title || !summary}>
            <FilePlus2 size={16} />
            {loading ? 'Opening incident...' : 'Open real incident'}
          </button>
        </article>
      </form>
    </AppShell>
  );
}
