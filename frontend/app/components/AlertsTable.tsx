interface Alert {
  id: string;
  type: string;
  severity: string;
  risk_score: number;
  source_ip: string;
  status: string;
  mitre_technique: string;
  description: string;
  timestamp: string;
  event_count: number;
}

interface AlertsTableProps {
  alerts: Alert[];
}

const severityColors: Record<string, string> = {
  CRITICAL: '#ff4757',
  HIGH: '#ff6b35',
  MEDIUM: '#ffa502',
  LOW: '#2ed573',
};

const statusColors: Record<string, string> = {
  NEW: '#ff4757',
  INVESTIGATING: '#ffa502',
  RESOLVED: '#2ed573',
};

export default function AlertsTable({ alerts }: AlertsTableProps) {
  return (
    <div className="card">
      <h2 className="text-lg font-semibold mb-4 text-slate-200">
        🚨 Active Alerts
      </h2>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-slate-400 border-b border-slate-700">
              <th className="text-left pb-3">Type</th>
              <th className="text-left pb-3">Severity</th>
              <th className="text-left pb-3">Source IP</th>
              <th className="text-left pb-3">Risk Score</th>
              <th className="text-left pb-3">MITRE</th>
              <th className="text-left pb-3">Status</th>
              <th className="text-left pb-3">Time</th>
            </tr>
          </thead>
          <tbody>
            {alerts.map((alert) => (
              <tr
                key={alert.id}
                className="border-b border-slate-800 hover:bg-slate-800 transition-colors"
              >
                <td className="py-3 font-mono text-blue-400">
                  {alert.type.replace('_', ' ').toUpperCase()}
                </td>
                <td className="py-3">
                  <span
                    className="px-2 py-1 rounded text-xs font-bold"
                    style={{
                      color: severityColors[alert.severity],
                      backgroundColor: severityColors[alert.severity] + '20',
                    }}
                  >
                    {alert.severity}
                  </span>
                </td>
                <td className="py-3 font-mono text-slate-300">
                  {alert.source_ip}
                </td>
                <td className="py-3">
                  <div className="flex items-center gap-2">
                    <div className="w-16 h-2 bg-slate-700 rounded-full">
                      <div
                        className="h-2 rounded-full"
                        style={{
                          width: `${alert.risk_score}%`,
                          backgroundColor: severityColors[alert.severity],
                        }}
                      />
                    </div>
                    <span style={{ color: severityColors[alert.severity] }}>
                      {alert.risk_score}
                    </span>
                  </div>
                </td>
                <td className="py-3 font-mono text-purple-400">
                  {alert.mitre_technique}
                </td>
                <td className="py-3">
                  <span
                    className="px-2 py-1 rounded text-xs"
                    style={{
                      color: statusColors[alert.status],
                      backgroundColor: statusColors[alert.status] + '20',
                    }}
                  >
                    {alert.status}
                  </span>
                </td>
                <td className="py-3 text-slate-400 text-xs">
                  {new Date(alert.timestamp).toLocaleTimeString()}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}