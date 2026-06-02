const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const TOKEN_KEY = 'sentinelx_token';

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
    throw new Error(`SentinelX API error: ${response.status}`);
  }
  return response.json();
}

export async function fetchAlerts(): Promise<Alert[]> {
  const data = await request<{ alerts: Alert[] }>('/api/alerts?sort_by=risk_score&order=desc');
  return data.alerts;
}

export async function fetchIncidents(): Promise<Incident[]> {
  const data = await request<{ incidents: Incident[] }>('/api/incidents');
  return data.incidents;
}

export async function fetchIncident(incidentId: string): Promise<Incident> {
  return request<Incident>(`/api/incidents/${incidentId}`);
}

export async function createIncident(payload: IncidentCreatePayload): Promise<Incident> {
  return request<Incident>('/api/incidents', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function fetchIncidentReport(incidentId: string): Promise<string> {
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
  const data = await request<{ token: string; user: Analyst; expires_at: string }>('/api/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  });
  setToken(data.token);
  return data;
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
