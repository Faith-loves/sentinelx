'use client';

import { useEffect, useMemo, useState } from 'react';
import {
  Activity,
  ArrowRight,
  Bot,
  Gauge,
  Radio,
  RotateCcw,
  ShieldAlert,
  Siren,
  Zap,
} from 'lucide-react';
import AppShell from './components/AppShell';
import { fetchAlerts, fetchLogStream, runAttackSimulation, type Alert as ApiAlert } from './lib/api';

const severityColor: Record<string, string> = {
  CRITICAL: '#ef4444',
  HIGH: '#f97316',
  MEDIUM: '#eab308',
  LOW: '#22c55e',
};

const statusColor: Record<string, string> = {
  NEW: '#ef4444',
  INVESTIGATING: '#eab308',
  RESOLVED: '#22c55e',
};

const ATTACK_SEQUENCE = [
  { type: 'Recon Scan', severity: 'LOW', risk: 22, ip: '185.220.101.8', mitre: 'T1595', status: 'NEW', desc: 'Port scan detected from external IP' },
  { type: 'Brute Force', severity: 'HIGH', risk: 68, ip: '185.220.101.8', mitre: 'T1110', status: 'NEW', desc: '23 failed login attempts on auth-server-01' },
  { type: 'Initial Access', severity: 'CRITICAL', risk: 85, ip: '185.220.101.8', mitre: 'T1078', status: 'NEW', desc: 'Valid credentials obtained after repeated SSH attempts' },
  { type: 'Lateral Move', severity: 'CRITICAL', risk: 91, ip: '10.0.0.45', mitre: 'T1021', status: 'INVESTIGATING', desc: 'Pivot to web-server-02 and file-server-03' },
  { type: 'Data Access', severity: 'CRITICAL', risk: 93, ip: '10.0.0.45', mitre: 'T1005', status: 'INVESTIGATING', desc: 'Sensitive database records accessed' },
  { type: 'Exfiltration', severity: 'CRITICAL', risk: 97, ip: '10.0.0.45', mitre: 'T1041', status: 'NEW', desc: '2.4GB transferred to 45.33.32.156' },
];

const LIVE_LOGS = [
  '10.0.0.45 -> auth-server-01 [SSH] failed',
  '185.220.101.8 -> firewall-01 [SCAN] detected',
  '10.0.0.67 -> db-server-01 [SQL] query x847',
  '10.0.0.45 -> file-server-03 [SMB] connected',
  '10.0.0.89 -> external [TCP] large transfer',
  '10.0.0.45 -> auth-server-01 [SSH] success',
];

function normalizeAlert(alert: ApiAlert) {
  return {
    type: alert.type.replace(/_/g, ' ').replace(/\b\w/g, (letter) => letter.toUpperCase()),
    severity: alert.severity,
    risk: alert.risk_score,
    ip: alert.source_ip,
    mitre: alert.mitre_technique,
    status: alert.status,
    desc: alert.description,
  };
}

export default function Dashboard() {
  const [time, setTime] = useState('');
  const [ticker, setTicker] = useState(0);
  const [alerts, setAlerts] = useState(ATTACK_SEQUENCE.slice(0, 4));
  const [simulating, setSimulating] = useState(false);
  const [simStep, setSimStep] = useState(0);
  const [logs, setLogs] = useState<string[]>([]);
  const [logIndex, setLogIndex] = useState(0);
  const [apiError, setApiError] = useState('');

  const tickerMessages = [
    'Threat intel updated: 847 new indicators scored and normalized',
    'Correlation engine reconstructed a 5-stage intrusion path',
    'Containment recommendation ready for INC-2024-0115',
    'MITRE mapping complete across credential access and exfiltration',
  ];

  useEffect(() => {
    const update = () => setTime(new Date().toLocaleTimeString('en-GB'));
    update();
    const t = setInterval(update, 1000);
    return () => clearInterval(t);
  }, []);

  useEffect(() => {
    const t = setInterval(() => setTicker((p) => (p + 1) % tickerMessages.length), 4000);
    return () => clearInterval(t);
  }, [tickerMessages.length]);

  useEffect(() => {
    let active = true;
    fetchAlerts()
      .then((data) => {
        if (active && data.length) setAlerts(data.map(normalizeAlert));
      })
      .catch(() => {
        if (active) setApiError('Portfolio preview mode: live backend data will sync after deployment.');
      });
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    const t = setInterval(() => {
      setLogs((prev) => [`${new Date().toLocaleTimeString('en-GB')} ${LIVE_LOGS[logIndex % LIVE_LOGS.length]}`, ...prev].slice(0, 8));
      setLogIndex((p) => p + 1);
    }, 1800);
    return () => clearInterval(t);
  }, [logIndex]);

  const stats = useMemo(() => ([
    { label: 'Critical Alerts', value: alerts.filter((a) => a.severity === 'CRITICAL').length, note: 'Immediate review', icon: ShieldAlert, tone: 'danger' },
    { label: 'Active Cases', value: alerts.filter((a) => a.status === 'INVESTIGATING').length, note: 'Being triaged', icon: Activity, tone: 'warning' },
    { label: 'Risk Score', value: alerts.length ? Math.round(alerts.reduce((a, b) => a + b.risk, 0) / alerts.length) : 0, note: 'Average active risk', icon: Gauge, tone: 'info' },
    { label: 'AI Confidence', value: '94%', note: 'Attack chain match', icon: Bot, tone: 'success' },
  ]), [alerts]);

  const runSimulation = async () => {
    if (simulating) return;
    setSimulating(true);
    setApiError('');
    setSimStep(0);
    try {
      const result = await runAttackSimulation();
      setAlerts(result.alerts.map(normalizeAlert));
      setSimStep(result.alerts.length);
      const stream = await fetchLogStream();
      setLogs(stream.map((log) => `${String(log.timestamp).slice(11, 19)} ${log.src_ip} -> ${log.dst_host || log.dst_ip || 'unknown'} [${log.event_type}]`));
    } catch {
      setApiError('Portfolio preview mode: visual attack simulation completed.');
      setAlerts([]);
      for (let i = 0; i < ATTACK_SEQUENCE.length; i++) {
        await new Promise((r) => setTimeout(r, 900));
        setAlerts((prev) => [ATTACK_SEQUENCE[i], ...prev]);
        setSimStep(i + 1);
      }
    }
    setSimulating(false);
  };

  const resetSim = () => {
    setAlerts(ATTACK_SEQUENCE.slice(0, 4));
    setSimStep(0);
    setSimulating(false);
  };

  return (
    <AppShell active="dashboard" statusText={`Live SOC / ${time}`}>
      <section className="hero-panel">
        <div className="hero-copy">
          <p className="section-label">Autonomous threat hunting</p>
          <h1>Detect, explain, and contain attacks before they become breach reports.</h1>
          <p>
            SentinelX turns raw security telemetry into a clear incident narrative with risk scoring,
            MITRE mapping, and AI-assisted response guidance.
          </p>
          <div className="hero-actions">
            <button className="primary-button" onClick={runSimulation} disabled={simulating}>
              <Zap size={16} />
              {simulating ? `Detecting ${simStep}/${ATTACK_SEQUENCE.length}` : 'Run attack simulation'}
            </button>
            <button className="secondary-button" onClick={resetSim}>
              <RotateCcw size={16} />
              Reset view
            </button>
          </div>
        </div>
        <div className="hero-signal" aria-label="Threat score summary">
          <div className="signal-ring">
            <span>94</span>
            <small>risk</small>
          </div>
          <div>
            <p className="signal-title">INC-2024-0115</p>
            <p className="signal-copy">Credential brute force, lateral movement, and data exfiltration detected across four hosts.</p>
          </div>
        </div>
      </section>

      <div className="ticker">
        <Radio size={16} />
        <span>{apiError || tickerMessages[ticker]}</span>
      </div>

      <section className="stats-grid">
        {stats.map((stat) => {
          const Icon = stat.icon;
          return (
            <article className={`metric-card ${stat.tone}`} key={stat.label}>
              <div className="metric-icon"><Icon size={18} /></div>
              <p>{stat.label}</p>
              <strong>{stat.value}</strong>
              <span>{stat.note}</span>
            </article>
          );
        })}
      </section>

      <section className="content-grid">
        <article className="panel span-2">
          <div className="panel-heading">
            <div>
              <p className="section-label">Active threat alerts</p>
              <h2>{alerts.length} correlated signals</h2>
            </div>
            <Siren size={20} />
          </div>
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Threat</th>
                  <th>Severity</th>
                  <th>Source</th>
                  <th>Risk</th>
                  <th>MITRE</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {alerts.map((alert, i) => (
                  <tr key={`${alert.type}-${i}`}>
                    <td>
                      <strong>{alert.type}</strong>
                      <span>{alert.desc}</span>
                    </td>
                    <td><span className="status-pill" style={{ color: severityColor[alert.severity], borderColor: `${severityColor[alert.severity]}55` }}>{alert.severity}</span></td>
                    <td className="mono">{alert.ip}</td>
                    <td>
                      <div className="risk-bar"><span style={{ width: `${alert.risk}%`, background: severityColor[alert.severity] }} /></div>
                      <span className="risk-value">{alert.risk}</span>
                    </td>
                    <td className="mono">{alert.mitre}</td>
                    <td><span className="status-pill" style={{ color: statusColor[alert.status], borderColor: `${statusColor[alert.status]}55` }}>{alert.status}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </article>

        <aside className="panel">
          <div className="panel-heading compact">
            <div>
              <p className="section-label">Live log stream</p>
              <h2>Ingestion</h2>
            </div>
            <span className="live-dot" />
          </div>
          <div className="log-list">
            {logs.length ? logs.map((log, i) => <p key={`${log}-${i}`} className={i === 0 ? 'fresh' : ''}>{log}</p>) : <p>Waiting for events...</p>}
          </div>
        </aside>
      </section>

      <section className="insight-grid">
        <article className="panel">
          <p className="section-label">Top attackers</p>
          {[
            { ip: '185.220.101.8', count: alerts.filter((a) => a.ip === '185.220.101.8').length, risk: 94 },
            { ip: '10.0.0.45', count: alerts.filter((a) => a.ip === '10.0.0.45').length, risk: 88 },
            { ip: '45.33.32.156', count: 1, risk: 76 },
          ].map((item) => (
            <div className="list-row" key={item.ip}>
              <span className="mono">{item.ip}</span>
              <small>{item.count} alerts</small>
              <strong>Risk {item.risk}</strong>
            </div>
          ))}
        </article>

        <article className="panel">
          <p className="section-label">Response plan</p>
          {['Isolate compromised hosts', 'Reset domain credentials', 'Block exfiltration endpoints'].map((item, i) => (
            <div className="check-row" key={item}>
              <span>{i + 1}</span>
              <p>{item}</p>
              <ArrowRight size={14} />
            </div>
          ))}
        </article>

        <article className="panel">
          <p className="section-label">System health</p>
          {['Log ingestion', 'Correlation engine', 'AI analyst', 'Threat intel'].map((item) => (
            <div className="list-row" key={item}>
              <span>{item}</span>
              <small className="healthy">Operational</small>
            </div>
          ))}
        </article>
      </section>
    </AppShell>
  );
}
