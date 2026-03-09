/* Reusable premium stat card */

interface Props {
  title: string;
  value: number | string;
  icon: React.ReactNode;
  color: string;   // e.g. "indigo" | "blue" | "green" | "red" | "yellow" | "purple"
  trend?: string;  // optional +12% label
}

const palette: Record<string, { bg: string; icon: string; text: string; ring: string }> = {
  blue:   { bg: 'bg-brand-50 dark:bg-brand-900/10',   icon: 'bg-brand-500 text-white shadow-[0_2px_8px_rgba(57,157,255,0.3)]',   text: 'text-brand-600 dark:text-brand-400',   ring: 'ring-brand-100 dark:ring-brand-500/20'   },
  indigo: { bg: 'bg-brand-50 dark:bg-brand-900/10',   icon: 'bg-brand-500 text-white shadow-[0_2px_8px_rgba(57,157,255,0.3)]',   text: 'text-brand-600 dark:text-brand-400',   ring: 'ring-brand-100 dark:ring-brand-500/20'   },
  green:  { bg: 'bg-emerald-50 dark:bg-emerald-500/10', icon: 'bg-emerald-600 text-white shadow-emerald-200 dark:shadow-emerald-900/50', text: 'text-emerald-700 dark:text-emerald-400', ring: 'ring-emerald-100 dark:ring-emerald-500/20' },
  red:    { bg: 'bg-red-50 dark:bg-red-500/10',     icon: 'bg-red-500 text-white shadow-red-200 dark:shadow-red-900/50',       text: 'text-red-700 dark:text-red-400',     ring: 'ring-red-100 dark:ring-red-500/20'     },
  yellow: { bg: 'bg-amber-50 dark:bg-amber-500/10', icon: 'bg-amber-500 text-white shadow-amber-200 dark:shadow-amber-900/50', text: 'text-amber-700 dark:text-amber-400', ring: 'ring-amber-100 dark:ring-amber-500/20' },
  purple: { bg: 'bg-purple-50 dark:bg-purple-500/10', icon: 'bg-purple-600 text-white shadow-purple-200 dark:shadow-purple-900/50', text: 'text-purple-700 dark:text-purple-400', ring: 'ring-purple-100 dark:ring-purple-500/20' },
};

export default function StatCard({ title, value, icon, color, trend }: Props) {
  const p = palette[color] ?? palette['indigo'];
  return (
    <div className={`relative rounded-2xl p-5 ${p.bg} ring-1 ${p.ring} transition-all duration-200 hover:shadow-lg hover:-translate-y-0.5 group`}>
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-[12px] font-semibold uppercase tracking-wider text-slate-400 dark:text-slate-500 mb-2">{title}</p>
          <p className="text-3xl font-extrabold text-slate-900 dark:text-white leading-none">{value}</p>
          {trend && (
            <p className={`text-[11px] font-semibold mt-2 ${p.text}`}>{trend}</p>
          )}
        </div>
        <div className={`w-11 h-11 rounded-xl ${p.icon} flex items-center justify-center shadow-md flex-shrink-0`}>
          {icon}
        </div>
      </div>
    </div>
  );
}
