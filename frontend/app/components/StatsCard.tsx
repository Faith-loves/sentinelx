interface StatsCardProps {
  title: string;
  value: number | string;
  color: string;
  icon: string;
  subtitle?: string;
}

export default function StatsCard({ title, value, color, icon, subtitle }: StatsCardProps) {
  return (
    <div className="card slide-in" style={{ borderColor: color + '40' }}>
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm text-slate-400 uppercase tracking-wider">{title}</span>
        <span className="text-2xl">{icon}</span>
      </div>
      <div className="text-3xl font-bold mb-1" style={{ color }}>
        {value}
      </div>
      {subtitle && (
        <div className="text-xs text-slate-500">{subtitle}</div>
      )}
    </div>
  );
}