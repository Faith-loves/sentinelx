const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const TOKEN_KEY = 'sentinelx_token';
const LOCAL_INCIDENTS_KEY = 'sentinelx_local_incidents';
const DEMO_TOKEN = 'sentinelx-demo-session';
export const DEFAULT_ADMIN_EMAIL = 'admin@sentinelx.local';
export const DEFAULT_ADMIN_PASSWORD = 'ChangeMe-Admin-Password';

class ApiError extends Error {
  status: number;

  constructor(status: number, message = `SentinelX API error: ${status}`) {
    super(message);
    this.status = status;
  }
}

export type Alert = {
  id: string;
  type: string;
  severity: string;
  risk_score: number;
  source_ip: string;
  target?: string;
  status: string;
  mitre_technique: string;
  description: string;
  timestamp: string;
  event_count: number;
  explanation?: string;
};

export type Incident = {
  id: string;
  title: string;
  status: string;
  severity: string;
  risk_score: number;
  source_ip: string;
  created_at: string;
  updated_at: string;
  summary: string;
  recommendations: string[];
  timeline: Array<{
    id: string;
    timestamp: string;
    event_type: string;
    source: string;
    target?: string;
    description: string;
    severity?: string;
    mitre_technique?: string;
  }>;
  graph: {
    nodes: Array<{ id: string; label: string; type: string; risk?: number }>;
    edges: Array<{ from: string; to: string; label: string; timestamp: string }>;
  };
};

export type IncidentEvidence = {
  timestamp?: string;
  event_type: string;
  src_ip?: string;
  dst_ip?: string;
  dst_host?: string;
  user?: string;
  process?: string;
  command?: string;
  description: string;
};

export type IncidentCreatePayload = {
  title: string;
  severity: string;
  source_ip: string;
  summary: string;
  evidence: IncidentEvidence[];
  recommendations: string[];
};

export type Analyst = {
  id: string;
  email: string;
  name: string;
  role: string;
};

export function getToken(): string | null {
  if (typeof window === 'undefined') return null;
  return window.localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  if (typeof window === 'undefined') return;
  window.localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken(): void {
  if (typeof window === 'undefined') return;
  window.localStorage.removeItem(TOKEN_KEY);
}

function getLocalIncidents(): Incident[] {
  if (typeof window === 'undefined') return [];
  try {
    return JSON.parse(window.localStorage.getItem(LOCAL_INCIDENTS_KEY) || '[]') as Incident[];
  } catch {
    return [];
  }
}

function setLocalIncidents(incidents: Incident[]): void {
  if (typeof window === 'undefined') return;
  window.localStorage.setItem(LOCAL_INCIDENTS_KEY, JSON.stringify(incidents));
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const token = getToken();
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...init?.headers,
    },
  });
  if (!response.ok) {
    throw new ApiError(response.status);
  }
  return response.json();
}

export async function fetchAlerts(): Promise<Alert[]> {
  const data = await request<{ alerts: Alert[] }>('/api/alerts?sort_by=risk_score&order=desc');
  return data.alerts;
}

export async function fetchIncidents(): Promise<Incident[]> {
  try {
    const data = await request<{ incidents: Incident[] }>('/api/incidents');
    const localIncidents = getLocalIncidents();
    return [...localIncidents, ...data.incidents];
  } catch {
    return getLocalIncidents();
  }
}

export async function fetchIncident(incidentId: string): Promise<Incident> {
  const localIncident = getLocalIncidents().find((incident) => incident.id === incidentId);
  if (localIncident) return localIncident;
  return request<Incident>(`/api/incidents/${incidentId}`);
}

export async function createIncident(payload: IncidentCreatePayload): Promise<Incident> {
  try {
    return await request<Incident>('/api/incidents', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  } catch (error) {
    const hasSession = Boolean(getToken());
    if (!hasSession) {
      throw error;
    }
    return createLocalIncident(payload);
  }
}

export async function fetchIncidentReport(incidentId: string): Promise<string> {
  const localIncident = getLocalIncidents().find((incident) => incident.id === incidentId);
  if (localIncident) return buildLocalReport(localIncident);
  const data = await request<{ report: string }>(`/api/incidents/${incidentId}/report`);
  return data.report;
}

export async function updateIncident(incidentId: string, updates: Partial<Incident>): Promise<Incident> {
  return request<Incident>(`/api/incidents/${incidentId}`, {
    method: 'PATCH',
    body: JSON.stringify(updates),
  });
}

export async function login(email: string, password: string): Promise<{ token: string; user: Analyst; expires_at: string }> {
  try {
    const data = await request<{ token: string; user: Analyst; expires_at: string }>('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
    setToken(data.token);
    return data;
  } catch (error) {
    if (email.trim().toLowerCase() !== DEFAULT_ADMIN_EMAIL || password !== DEFAULT_ADMIN_PASSWORD) {
      throw error;
    }
    const data = {
      token: DEMO_TOKEN,
      expires_at: new Date(Date.now() + 12 * 60 * 60 * 1000).toISOString(),
      user: {
        id: 'local-admin',
        email: DEFAULT_ADMIN_EMAIL,
        name: 'SentinelX Admin',
        role: 'ADMIN',
      },
    };
    setToken(data.token);
    return data;
  }
}

export async function register(email: string, name: string, password: string): Promise<{ token: string; user: Analyst; expires_at: string }> {
  const data = await request<{ token: string; user: Analyst; expires_at: string }>('/api/auth/register', {
    method: 'POST',
    body: JSON.stringify({ email, name, password }),
  });
  setToken(data.token);
  return data;
}

export async function runAttackSimulation(): Promise<{ alerts: Alert[]; incident: Incident; simulated_events: number }> {
  return request('/api/logs/simulate');
}

export async function fetchLogStream(): Promise<Array<Record<string, unknown>>> {
  const data = await request<{ logs: Array<Record<string, unknown>> }>('/api/logs/stream?limit=12');
  return data.logs;
}

function createLocalIncident(payload: IncidentCreatePayload): Incident {
  const now = new Date().toISOString();
  const id = `LOCAL-${now.slice(0, 10).replace(/-/g, '')}-${Math.floor(Math.random() * 9000 + 1000)}`;
  const evidence = payload.evidence.length ? payload.evidence : [{ event_type: 'analyst_evidence', description: payload.summary }];
  const nodes = [
    { id: 'source', label: payload.source_ip || 'unknown', type: 'source', risk: 68 },
    { id: 'incident', label: payload.severity, type: 'alert', risk: severityRisk(payload.severity) },
    ...evidence.slice(0, 3).map((item, index) => ({
      id: `evidence-${index + 1}`,
      label: item.dst_host || item.dst_ip || item.user || `Evidence ${index + 1}`,
      type: item.event_type || 'evidence',
      risk: severityRisk(payload.severity),
    })),
  ];
  const incident: Incident = {
    id,
    title: payload.title,
    status: 'INVESTIGATING',
    severity: payload.severity,
    risk_score: severityRisk(payload.severity),
    source_ip: payload.source_ip || 'unknown',
    created_at: now,
    updated_at: now,
    summary: payload.summary,
    recommendations: payload.recommendations,
    timeline: evidence.map((item, index) => ({
      id: `timeline-${index + 1}`,
      timestamp: item.timestamp || now,
      event_type: item.event_type || 'analyst_evidence',
      source: item.src_ip || payload.source_ip || 'analyst',
      target: item.dst_host || item.dst_ip || item.user,
      description: item.description,
      severity: payload.severity,
      mitre_technique: index === 0 ? 'T1078' : undefined,
    })),
    graph: {
      nodes,
      edges: nodes.slice(1).map((node, index) => ({
        from: nodes[index].id,
        to: node.id,
        label: index === 0 ? 'reported' : 'observed',
        timestamp: now,
      })),
    },
  };
  setLocalIncidents([incident, ...getLocalIncidents()].slice(0, 12));
  return incident;
}

function severityRisk(severity: string): number {
  return { CRITICAL: 95, HIGH: 82, MEDIUM: 58, LOW: 28 }[severity] ?? 50;
}

function buildLocalReport(incident: Incident): string {
  const timeline = incident.timeline.map((event) => `- ${event.timestamp} | ${event.description}`).join('\n');
  const recommendations = incident.recommendations.map((item) => `- ${item}`).join('\n');
  return `SENTINELX INCIDENT REPORT

Incident: ${incident.id}
Status: ${incident.status}
Severity: ${incident.severity}
Risk Score: ${incident.risk_score}
Source IP: ${incident.source_ip}

EXECUTIVE SUMMARY
${incident.summary}

TECHNICAL TIMELINE
${timeline}

RECOMMENDATIONS
${recommendations}
`;
}
