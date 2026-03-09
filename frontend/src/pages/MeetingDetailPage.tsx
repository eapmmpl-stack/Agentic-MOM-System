import { useParams, Link, useNavigate } from 'react-router-dom';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import {
  TrashIcon,
  ArrowLeftIcon,
  CalendarDaysIcon,
  MapPinIcon,
  ClockIcon,
  UserIcon,
  BuildingOfficeIcon,
  ClipboardDocumentListIcon,
  ArrowDownTrayIcon,
  PencilSquareIcon,
  CheckCircleIcon,
} from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';
import api from '../api';
import type { Meeting } from '../types';

const statusColors: Record<string, string> = {
  Completed:   'bg-emerald-50 dark:bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border-emerald-200 dark:border-emerald-500/20',
  'In Progress':'bg-blue-50 dark:bg-blue-500/10 text-blue-700 dark:text-blue-400 border-blue-200 dark:border-blue-500/20',
  Pending:     'bg-amber-50 dark:bg-amber-500/10 text-amber-700 dark:text-amber-400 border-amber-200 dark:border-amber-500/20',
};

function Section({ title, icon, children }: { title: string; icon: React.ReactNode; children: React.ReactNode }) {
  return (
    <div className="bg-white dark:bg-[#161b27] rounded-2xl border border-slate-100 dark:border-slate-800 shadow-sm overflow-hidden">
      <div className="flex items-center gap-2.5 px-6 py-4 border-b border-slate-100 dark:border-slate-800">
        <span className="text-brand-500">{icon}</span>
        <h3 className="text-[14px] font-bold text-slate-800 dark:text-white">{title}</h3>
      </div>
      <div className="p-6">{children}</div>
    </div>
  );
}

export default function MeetingDetailPage() {
  const { id } = useParams<{ id: string }>();
  const queryClient = useQueryClient();
  const navigate = useNavigate();

  const handleDownloadPDF = () => {
    if (!id) return;
    window.open(`${window.location.origin}/api/v1/meetings/${id}/pdf`, '_blank');
  };

  const { data: meeting, isLoading } = useQuery<Meeting>({
    queryKey: ['meeting', id],
    queryFn: async () => (await api.get(`/meetings/${id}`)).data,
  });

  const handleDeleteMeeting = async () => {
    if (!meeting || !window.confirm(`Delete "${meeting.title}"?\nThis action cannot be undone.`)) return;
    try {
      await api.delete(`/meetings/${id}`);
      toast.success('Meeting deleted');
      queryClient.invalidateQueries({ queryKey: ['meetings'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
      navigate('/meetings');
    } catch {
      toast.error('Failed to delete meeting');
    }
  };

  const handleStatusChange = async (taskId: number, newStatus: string) => {
    try {
      await api.put(`/tasks/${taskId}`, { status: newStatus });
      toast.success('Status updated');
      queryClient.invalidateQueries({ queryKey: ['meeting', id] });
    } catch {
      toast.error('Failed to update task status');
    }
  };

  if (isLoading || !meeting) {
    return (
      <div className="flex flex-col items-center justify-center h-64 gap-3">
        <div className="w-7 h-7 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
        <p className="text-sm text-slate-400">Loading meeting…</p>
      </div>
    );
  }

  const metaItems = [
    { icon: <BuildingOfficeIcon className="w-4 h-4" />, label: 'Organization', value: meeting.organization },
    { icon: <ClipboardDocumentListIcon className="w-4 h-4" />, label: 'Type', value: meeting.meeting_type },
    { icon: <CalendarDaysIcon className="w-4 h-4" />, label: 'Date', value: meeting.date },
    { icon: <ClockIcon className="w-4 h-4" />, label: 'Time', value: meeting.time },
    { icon: <MapPinIcon className="w-4 h-4" />, label: 'Venue', value: meeting.venue },
    { icon: <UserIcon className="w-4 h-4" />, label: 'Called By', value: meeting.called_by },
    { icon: <UserIcon className="w-4 h-4" />, label: 'Prepared By', value: meeting.prepared_by },
  ];

  return (
    <div className="space-y-5 max-w-4xl mx-auto">

      {/* ── Top Nav Bar ── */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <Link to="/meetings" className="inline-flex items-center gap-1.5 text-[13px] font-semibold text-slate-500 hover:text-brand-600 dark:text-slate-400 dark:hover:text-brand-400 transition-colors">
          <ArrowLeftIcon className="w-4 h-4" /> Back to Meetings
        </Link>
        <div className="flex flex-wrap gap-2">
          <button
            onClick={handleDeleteMeeting}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 text-[13px] font-semibold rounded-xl bg-red-50 dark:bg-red-500/10 text-red-600 dark:text-red-400 hover:bg-red-100 dark:hover:bg-red-500/20 border border-red-100 dark:border-red-500/20 transition-all active:scale-[0.98]"
          >
            <TrashIcon className="w-4 h-4" /> Delete
          </button>
          <Link
            to={`/meetings/${id}/log-mom`}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 text-[13px] font-semibold rounded-xl bg-emerald-50 dark:bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 hover:bg-emerald-100 dark:hover:bg-emerald-500/20 border border-emerald-100 dark:border-emerald-500/20 transition-all active:scale-[0.98]"
          >
            <PencilSquareIcon className="w-4 h-4" /> Record MOM
          </Link>
          <button
            onClick={handleDownloadPDF}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 text-[13px] font-bold rounded-xl bg-brand-600 text-white hover:bg-brand-700 shadow-md shadow-brand-200 dark:shadow-brand-900/40 transition-all active:scale-[0.98]"
          >
            <ArrowDownTrayIcon className="w-4 h-4" /> Download MOM PDF
          </button>
        </div>
      </div>

      {/* ── Hero Header ── */}
      <div className="relative rounded-2xl overflow-hidden shadow-sm">
        <div className="absolute inset-0 bg-gradient-to-br from-brand-600 to-purple-700" />
        <div className="absolute inset-0 opacity-10" style={{ backgroundImage: 'radial-gradient(circle at 80% 20%, white 1px, transparent 1px)', backgroundSize: '24px 24px' }} />
        <div className="relative z-10 p-6 text-white">
          <p className="text-[11px] font-bold uppercase tracking-widest text-brand-200 mb-1">Meeting Details</p>
          <h2 className="text-2xl font-extrabold mb-4">{meeting.title}</h2>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
            {metaItems.filter(i => i.value).map((item, idx) => (
              <div key={idx} className="bg-white/10 rounded-xl px-3.5 py-3 backdrop-blur-sm">
                <div className="flex items-center gap-1.5 text-brand-200 mb-1">
                  {item.icon}
                  <p className="text-[10px] font-bold uppercase tracking-wide">{item.label}</p>
                </div>
                <p className="text-[13px] font-semibold text-white">{item.value}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ── Attendees ── */}
      <Section title="Attendees" icon={<UserIcon className="w-4.5 h-4.5 w-[18px] h-[18px]" />}>
        {meeting.attendees.length === 0 ? (
          <p className="text-sm text-slate-400">No attendees recorded.</p>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
            {meeting.attendees.map((a) => {
              const present = String(a.attendance_status).toLowerCase().includes('present');
              return (
                <div key={a.id} className="flex items-center gap-3 p-3 rounded-xl bg-slate-50 dark:bg-white/5 border border-slate-100 dark:border-slate-800">
                  <div className="w-9 h-9 rounded-full bg-brand-100 dark:bg-brand-500/20 flex items-center justify-center text-brand-700 dark:text-brand-400 text-[13px] font-bold shrink-0">
                    {a.user_name.charAt(0).toUpperCase()}
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="text-[13px] font-semibold text-slate-800 dark:text-white truncate">{a.user_name}</p>
                    <p className="text-[11px] text-slate-400 truncate">{a.email || 'No email'}</p>
                  </div>
                  <span className={`text-[11px] font-bold px-2.5 py-1 rounded-lg border shrink-0 ${present ? 'bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-500/10 dark:text-emerald-400 dark:border-emerald-500/20' : 'bg-red-50 text-red-600 border-red-200 dark:bg-red-500/10 dark:text-red-400 dark:border-red-500/20'}`}>
                    {present ? '✓ Present' : '✗ Absent'}
                  </span>
                </div>
              );
            })}
          </div>
        )}
      </Section>

      {/* ── Agenda ── */}
      <Section title="Agenda Items" icon={<ClipboardDocumentListIcon className="w-[18px] h-[18px]" />}>
        {meeting.agenda_items.length === 0 ? (
          <p className="text-sm text-slate-400">No agenda items.</p>
        ) : (
          <div className="space-y-2.5">
            {meeting.agenda_items.map((a, i) => (
              <div key={a.id} className="flex gap-3.5 p-3.5 rounded-xl bg-slate-50 dark:bg-white/5 border border-slate-100 dark:border-slate-800">
                <span className="w-6 h-6 rounded-full bg-brand-600 text-white text-[11px] font-bold flex items-center justify-center shrink-0 mt-0.5">{i + 1}</span>
                <div>
                  <p className="text-[13px] font-semibold text-slate-800 dark:text-white">{a.topic}</p>
                  {a.description && <p className="text-[12px] text-slate-500 dark:text-slate-400 mt-0.5">{a.description}</p>}
                </div>
              </div>
            ))}
          </div>
        )}
      </Section>

      {/* ── Discussion Summary ── */}
      {meeting.discussion && (
        <Section title="Discussion Summary" icon={<CheckCircleIcon className="w-[18px] h-[18px]" />}>
          <p className="text-[13px] text-slate-700 dark:text-slate-300 whitespace-pre-wrap leading-relaxed">{meeting.discussion.summary_text}</p>
        </Section>
      )}

      {/* ── Tasks ── */}
      <Section title="Action Items / Tasks" icon={<ClipboardDocumentListIcon className="w-[18px] h-[18px]" />}>
        {meeting.tasks.length === 0 ? (
          <p className="text-sm text-slate-400">No tasks recorded.</p>
        ) : (
          <div className="space-y-2.5">
            {meeting.tasks.map((t) => (
              <div key={t.id} className="flex flex-col sm:flex-row sm:items-center gap-3 p-4 rounded-xl border border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-white/5">
                <div className="flex-1 min-w-0">
                  <p className="text-[13px] font-semibold text-slate-800 dark:text-white">{t.title}</p>
                  {t.description && <p className="text-[11px] text-slate-400 mt-0.5 line-clamp-2">{t.description}</p>}
                  <div className="flex flex-wrap items-center gap-3 mt-1.5 text-[11px] text-slate-400">
                    {t.responsible_person && <span className="flex items-center gap-1"><UserIcon className="w-3 h-3" />{t.responsible_person}</span>}
                    {t.deadline && <span className="flex items-center gap-1"><CalendarDaysIcon className="w-3 h-3" />Due: {t.deadline}</span>}
                  </div>
                </div>
                <select
                  value={t.status}
                  onChange={(e) => handleStatusChange(t.id, e.target.value)}
                  className={`text-[12px] font-bold px-3 py-1.5 rounded-lg border cursor-pointer focus:outline-none focus:ring-2 focus:ring-brand-400 shrink-0 ${statusColors[t.status] ?? statusColors['Pending']}`}
                >
                  <option value="Pending">Pending</option>
                  <option value="In Progress">In Progress</option>
                  <option value="Completed">Completed</option>
                </select>
              </div>
            ))}
          </div>
        )}
      </Section>

      {/* ── Next Meeting ── */}
      {meeting.next_meeting && (
        <Section title="Next Meeting" icon={<CalendarDaysIcon className="w-[18px] h-[18px]" />}>
          <div className="flex items-center gap-6 text-[13px] text-slate-700 dark:text-slate-300">
            <span className="flex items-center gap-2"><CalendarDaysIcon className="w-4 h-4 text-brand-500" />{meeting.next_meeting.next_date || 'TBD'}</span>
            <span className="flex items-center gap-2"><ClockIcon className="w-4 h-4 text-brand-500" />{meeting.next_meeting.next_time || 'TBD'}</span>
          </div>
        </Section>
      )}
    </div>
  );
}
