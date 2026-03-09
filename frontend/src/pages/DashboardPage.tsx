import { useQuery } from '@tanstack/react-query';
import {
  CalendarDaysIcon,
  ClipboardDocumentListIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  ClockIcon,
} from '@heroicons/react/24/outline';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend,
} from 'recharts';

import api from '../api';
import type { AnalyticsData } from '../types';
import StatCard from '../components/StatCard';
import StatusBadge from '../components/StatusBadge';
import { Link } from 'react-router-dom';

const PIE_COLORS = ['#399dff', '#f59e0b', '#22c55e'];

export default function DashboardPage() {
  const { data, isLoading } = useQuery<AnalyticsData>({
    queryKey: ['dashboard'],
    queryFn: async () => (await api.get('/dashboard/')).data,
  });

  if (isLoading || !data) {
    return (
      <div className="flex flex-col items-center justify-center h-64 gap-3">
        <div className="w-8 h-8 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
        <p className="text-sm text-slate-400">Loading dashboard…</p>
      </div>
    );
  }

  const { stats, task_distribution, meeting_trends, recent_meetings, overdue_tasks, nearest_upcoming_meeting, last_meeting } = data;

  return (
    <div className="space-y-6 max-w-[1400px] mx-auto">

      {/* ── Hero Row ── */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-5">

        {/* Next Meeting – wider */}
        <div className="lg:col-span-3 relative rounded-2xl overflow-hidden shadow-xl shadow-brand-100 dark:shadow-brand-900/30">
          {/* Gradient bg */}
          <div className="absolute inset-0 bg-gradient-to-br from-brand-400 via-brand-500 to-brand-800" />
          {/* Decorative circles */}
          <div className="absolute -top-12 -right-12 w-48 h-48 bg-white/5 rounded-full" />
          <div className="absolute bottom-0 left-24 w-32 h-32 bg-white/5 rounded-full" />

          <div className="relative z-10 p-6">
            <div className="flex items-center gap-2 mb-4">
              <span className="inline-flex items-center gap-1.5 text-[11px] font-bold uppercase tracking-wider bg-white/15 text-brand-100 px-3 py-1 rounded-full">
                <span className="w-1.5 h-1.5 bg-emerald-400 rounded-full animate-pulse" />
                Next Scheduled Meeting
              </span>
            </div>

            {nearest_upcoming_meeting ? (
              <>
                <h3 className="text-2xl font-extrabold text-white leading-tight mb-3">{nearest_upcoming_meeting.title}</h3>
                <div className="flex flex-wrap gap-4 text-brand-50 text-sm mb-5">
                  <span className="flex items-center gap-1.5">
                    <CalendarDaysIcon className="w-4 h-4 text-brand-200" />
                    {nearest_upcoming_meeting.date || 'TBD'} &nbsp;·&nbsp; {nearest_upcoming_meeting.time || 'TBD'}
                  </span>
                  <span className="flex items-center gap-1.5">
                    <ClockIcon className="w-4 h-4 text-brand-200" />
                    {nearest_upcoming_meeting.venue || 'TBD'}
                  </span>
                  <span className="flex items-center gap-1.5">
                    <span className="w-4 h-4 text-brand-200">👥</span>
                    {nearest_upcoming_meeting.attendees?.length || 0} attendees
                  </span>
                </div>
                <div className="flex gap-2.5">
                  <Link to={`/meetings/${nearest_upcoming_meeting.id}`}
                    className="px-4 py-2 text-[13px] font-semibold text-white rounded-xl bg-white/15 hover:bg-white/25 transition-colors backdrop-blur-sm">
                    View Details
                  </Link>
                  <Link to={`/meetings/${nearest_upcoming_meeting.id}/log-mom`}
                    className="px-4 py-2 text-[13px] font-bold text-brand-600 rounded-xl bg-white hover:bg-brand-50 transition-colors shadow-md">
                    Record MOM
                  </Link>
                </div>
              </>
            ) : (
              <p className="text-brand-100 text-sm mt-2">No upcoming meetings scheduled.</p>
            )}
          </div>
        </div>

        {/* Last Meeting – narrower */}
        <div className="lg:col-span-2 bg-white dark:bg-[#161b27] rounded-2xl border border-slate-100 dark:border-slate-800 p-6 shadow-sm flex flex-col justify-between">
          <div>
            <p className="text-[11px] font-bold uppercase tracking-widest text-slate-400 dark:text-slate-500 mb-3">Last Meeting</p>
            {last_meeting ? (
              <>
                <Link to={`/meetings/${last_meeting.id}`} className="text-[17px] font-bold text-slate-900 dark:text-white hover:text-brand-500 dark:hover:text-brand-400 transition-colors line-clamp-2 leading-snug">
                  {last_meeting.title}
                </Link>
                <p className="text-xs text-slate-400 mt-1 mb-5">{last_meeting.date}</p>
                <div className="grid grid-cols-2 gap-3">
          <div className="rounded-xl bg-emerald-50 dark:bg-emerald-500/10 p-3 text-center">
                    <p className="text-[10px] text-emerald-600 dark:text-emerald-400 font-bold uppercase tracking-wide">Tasks Done</p>
                    <p className="text-2xl font-extrabold text-emerald-700 dark:text-emerald-300 mt-1">
                      {last_meeting.tasks?.filter(t => t.status === 'Completed').length || 0}
                      <span className="text-base font-semibold text-slate-400"> / {last_meeting.tasks?.length || 0}</span>
                    </p>
                  </div>
                  <div className="rounded-xl bg-brand-50 dark:bg-brand-500/10 p-3 text-center">
                    <p className="text-[10px] text-brand-600 dark:text-brand-400 font-bold uppercase tracking-wide">Attendance</p>
                    <p className="text-2xl font-extrabold text-brand-700 dark:text-brand-300 mt-1">
                      {last_meeting.attendees?.filter(a => a.attendance_status === 'Present').length || 0}
                      <span className="text-base font-semibold text-slate-400"> / {last_meeting.attendees?.length || 0}</span>
                    </p>
                  </div>
                </div>
              </>
            ) : (
              <p className="text-slate-400 text-sm">No past meetings found.</p>
            )}
          </div>
          <div className="mt-4 pt-4 border-t border-slate-100 dark:border-slate-800">
            <Link to="/meetings" className="text-[12px] font-semibold text-brand-500 dark:text-brand-400 hover:underline">
              View all meetings →
            </Link>
          </div>
        </div>
      </div>

      {/* ── Stats Grid ── */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-7 gap-4">
        <StatCard title="Total Meetings"   value={stats.total_meetings}     color="blue"   icon={<CalendarDaysIcon className="w-5 h-5" />} />
        <StatCard title="Total Tasks"      value={stats.total_tasks}        color="indigo" icon={<ClipboardDocumentListIcon className="w-5 h-5" />} />
        <StatCard title="Pending"          value={stats.pending_tasks}      color="yellow" icon={<ClockIcon className="w-5 h-5" />} />
        <StatCard title="In Progress"      value={stats.in_progress_tasks}  color="purple" icon={<ClockIcon className="w-5 h-5" />} />
        <StatCard title="Completed"        value={stats.completed_tasks}    color="green"  icon={<CheckCircleIcon className="w-5 h-5" />} />
        <StatCard title="Overdue"          value={stats.overdue_tasks}      color="red"    icon={<ExclamationTriangleIcon className="w-5 h-5" />} />
        <StatCard title="Upcoming"         value={stats.upcoming_meetings}  color="indigo" icon={<CalendarDaysIcon className="w-5 h-5" />} />
      </div>

      {/* ── Charts ── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <div className="bg-white dark:bg-[#161b27] rounded-2xl border border-slate-100 dark:border-slate-800 p-5 shadow-sm">
          <p className="text-[13px] font-bold text-slate-800 dark:text-white mb-4">Meeting Trends</p>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={meeting_trends} barCategoryGap="40%">
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="month" tick={{ fontSize: 11, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
              <YAxis allowDecimals={false} tick={{ fontSize: 11, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
              <Tooltip
                contentStyle={{ borderRadius: 12, border: 'none', boxShadow: '0 4px 20px rgba(0,0,0,0.1)', fontSize: 12 }}
                cursor={{ fill: '#f1f5f9' }}
              />
              <Bar dataKey="count" fill="#399dff" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white dark:bg-[#161b27] rounded-2xl border border-slate-100 dark:border-slate-800 p-5 shadow-sm">
          <p className="text-[13px] font-bold text-slate-800 dark:text-white mb-4">Task Distribution</p>
          <ResponsiveContainer width="100%" height={240}>
            <PieChart>
              <Pie data={task_distribution} dataKey="count" nameKey="status" cx="50%" cy="50%" outerRadius={90} innerRadius={45}
                paddingAngle={3} strokeWidth={0}>
                {task_distribution.map((_, idx) => (
                  <Cell key={idx} fill={PIE_COLORS[idx % PIE_COLORS.length]} />
                ))}
              </Pie>
              <Legend iconType="circle" iconSize={8} formatter={(v) => <span style={{ fontSize: 11, color: '#94a3b8' }}>{v}</span>} />
              <Tooltip contentStyle={{ borderRadius: 12, border: 'none', boxShadow: '0 4px 20px rgba(0,0,0,0.1)', fontSize: 12 }} />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* ── Bottom Tables ── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">

        {/* Recent Meetings */}
        <div className="bg-white dark:bg-[#161b27] rounded-2xl border border-slate-100 dark:border-slate-800 p-5 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <p className="text-[13px] font-bold text-slate-800 dark:text-white">Recent Meetings</p>
            <Link to="/meetings" className="text-[11px] font-semibold text-brand-500 hover:text-brand-600 transition-colors">View all →</Link>
          </div>
          {recent_meetings.length === 0 ? (
            <p className="text-slate-400 text-sm">No meetings yet.</p>
          ) : (
            <div className="space-y-1.5">
              {recent_meetings.map((m) => (
                <Link key={m.id} to={`/meetings/${m.id}`}
                  className="flex items-center justify-between p-3 rounded-xl hover:bg-slate-50 dark:hover:bg-white/5 transition-colors group">
                  <div>
                    <p className="text-[13px] font-semibold text-slate-800 dark:text-white group-hover:text-brand-500 dark:group-hover:text-brand-400 transition-colors">{m.title}</p>
                    <p className="text-[11px] text-slate-400 mt-0.5">{m.date || 'No date'} · {m.venue || 'N/A'}</p>
                  </div>
                  <span className="text-[11px] font-semibold bg-brand-50 dark:bg-brand-500/15 text-brand-600 dark:text-brand-400 px-2.5 py-1 rounded-lg shrink-0">
                    {m.task_count} tasks
                  </span>
                </Link>
              ))}
            </div>
          )}
        </div>

        {/* Overdue Tasks */}
        <div className="bg-white dark:bg-[#161b27] rounded-2xl border border-slate-100 dark:border-slate-800 p-5 shadow-sm">
          <p className="text-[13px] font-bold text-slate-800 dark:text-white mb-4">Overdue Tasks</p>
          {overdue_tasks.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-8 gap-2">
              <CheckCircleIcon className="w-8 h-8 text-emerald-400" />
              <p className="text-sm text-slate-400">No overdue tasks. 🎉</p>
            </div>
          ) : (
            <div className="space-y-2">
              {overdue_tasks.map((t) => (
                <div key={t.id} className="p-3 rounded-xl bg-red-50 dark:bg-red-500/10 border border-red-100 dark:border-red-500/20">
                  <div className="flex items-start justify-between gap-2">
                    <p className="text-[13px] font-semibold text-slate-800 dark:text-white">{t.title}</p>
                    <StatusBadge status={t.status} />
                  </div>
                  <p className="text-[11px] text-slate-400 mt-1">
                    {t.responsible_person || 'Unassigned'} · Due: {t.deadline}
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
