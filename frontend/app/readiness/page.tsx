'use client';

import { CheckCircle2, Target } from 'lucide-react';
import AppShell from '../components/AppShell';

const sections = [
  {
    title: 'Core SOC Platform',
    items: [
      ['Log ingestion', 'Windows, Linux, network, application, generic, and bulk ingestion endpoints are represented.'],
      ['Threat correlation', 'Detection rules correlate alerts into incidents, timelines, and attack graphs.'],
      ['Search and storage', 'Postgres-ready persistence and Elasticsearch-backed search with SQL fallback are included.'],
      ['Incident lifecycle', 'Status updates, assignment, comments, SLA tracking, and escalation endpoints are included.'],
      ['Reporting', 'Text and PDF incident reports are generated from incident evidence.'],
    ],
  },
  {
    title: 'Security And Access',
    items: [
      ['Analyst login', 'Admin bootstrap, analyst accounts, bearer sessions, and protected routes are implemented.'],
      ['Role-based access', 'Admin and analyst permissions protect sensitive actions.'],
      ['MFA foundation', 'TOTP setup, enable, disable, and login verification endpoints are included.'],
      ['SSO readiness', 'OIDC configuration surface is available for enterprise identity provider wiring.'],
      ['Controlled signup', 'Optional registration can be enabled for portfolio/demo access and disabled for private SOC use.'],
    ],
  },
  {
    title: 'Operations',
    items: [
      ['Health checks', 'Health, readiness, and Prometheus-style metrics endpoints are included.'],
      ['External alerting', 'Webhook notifications support alert, incident, and escalation events.'],
      ['Backups', 'Postgres backup script and restore guidance are included.'],
      ['Collectors', 'Windows event log, Linux auth log, and network JSON collector scripts are included.'],
      ['Kubernetes', 'Namespace, secrets, backend, frontend, ingress, and monitoring manifests are included.'],
    ],
  },
  {
    title: 'Portfolio Deployment',
    items: [
      ['Docker deployment', 'Backend and frontend Dockerfiles support dynamic platform ports.'],
      ['Railway readiness', 'The project is ready for Railway services, Postgres, and environment variables.'],
      ['Frontend experience', 'Dashboard, investigation, assistant, reports, login, signup, and readiness pages are available.'],
      ['Documentation', 'Deployment, operations, production readiness, and portfolio readiness docs are included.'],
      ['Demo flow', 'Attack simulation creates alerts, incidents, graph data, timeline data, and reports.'],
    ],
  },
];

const total = sections.reduce((count, section) => count + section.items.length, 0);

export default function Readiness() {
  return (
    <AppShell active="readiness" statusText="100% production foundation">
      <section className="readiness-hero">
        <div>
          <p className="section-label">Production readiness</p>
          <h1>SentinelX is ready for deployment and portfolio presentation.</h1>
          <p>
            Every major SOC foundation layer is represented: detection, investigation, access control,
            reporting, operations, collectors, monitoring, and deployment assets.
          </p>
        </div>
        <div className="readiness-score">
          <Target size={28} />
          <strong>100%</strong>
          <span>deployment-ready foundation</span>
        </div>
      </section>

      <section className="readiness-summary">
        <article className="metric-card success">
          <div className="metric-icon"><CheckCircle2 size={18} /></div>
          <p>Completed</p>
          <strong>{total}</strong>
          <span>Ready for portfolio deployment</span>
        </article>
      </section>

      <section className="readiness-sections">
        {sections.map((section) => (
          <article className="panel readiness-section" key={section.title}>
            <div className="panel-heading">
              <div>
                <p className="section-label">Checklist area</p>
                <h2>{section.title}</h2>
              </div>
            </div>
            <div className="checklist-table">
              {section.items.map(([label, note]) => (
                <div className="checklist-item done" key={label}>
                  <div className="checklist-status">
                    <CheckCircle2 size={17} />
                    <span>Completed</span>
                  </div>
                  <strong>{label}</strong>
                  <p>{note}</p>
                </div>
              ))}
            </div>
          </article>
        ))}
      </section>
    </AppShell>
  );
}
