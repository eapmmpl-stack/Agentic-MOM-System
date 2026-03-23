import { useState, useEffect } from 'react';
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
  MicrophoneIcon,
  DocumentIcon,
  PlusIcon,
  XMarkIcon,
  PaperAirplaneIcon,
} from '@heroicons/react/24/outline';
import RecordingOverlay from '../components/RecordingOverlay';
import ProcessingBanner from '../components/ProcessingBanner';
import toast from 'react-hot-toast';
import api from '../api';
import type { Meeting, Task } from '../types';

const statusColors: Record<string, string> = {
  Completed: 'bg-emerald-50 dark:bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border-emerald-200 dark:border-emerald-500/20',
  Processing: 'bg-brand-50 dark:bg-brand-500/10 text-brand-700 dark:text-brand-400 border-brand-200 dark:border-brand-500/20 animate-pulse',
  'In Progress': 'bg-blue-50 dark:bg-blue-500/10 text-blue-700 dark:text-blue-400 border-blue-200 dark:border-blue-500/20',
  Pending: 'bg-amber-50 dark:bg-amber-500/10 text-amber-700 dark:text-amber-400 border-amber-200 dark:border-amber-500/20',
};

function Section({ title, icon, children, action }: { title: string; icon: React.ReactNode; children: React.ReactNode; action?: React.ReactNode }) {
  return (
    <div className="bg-white dark:bg-[#161b27] rounded-2xl border border-slate-100 dark:border-slate-800 shadow-sm overflow-hidden">
      <div className="flex items-center justify-between gap-2.5 px-6 py-4 border-b border-slate-100 dark:border-slate-800">
        <div className="flex items-center gap-2.5">
          <span className="text-brand-500">{icon}</span>
          <h3 className="text-[14px] font-bold text-slate-800 dark:text-white">{title}</h3>
        </div>
        {action && <div>{action}</div>}
      </div>
      <div className="p-6">{children}</div>
    </div>
  );
}

export default function MeetingDetailPage() {
  const { id } = useParams<{ id: string }>();
  const queryClient = useQueryClient();
  const navigate = useNavigate();

  // ── Editable State ─────────────────────────────────
  const [editingDiscussion, setEditingDiscussion] = useState(false);
  const [discussionText, setDiscussionText] = useState('');
  const [editingTaskId, setEditingTaskId] = useState<number | null>(null);
  const [taskEditData, setTaskEditData] = useState<{ title: string; description: string; responsible_person: string; deadline: string; status: string }>({ title: '', description: '', responsible_person: '', deadline: '', status: 'Pending' });
  const [showAddTask, setShowAddTask] = useState(false);
  const [newTask, setNewTask] = useState({ title: '', description: '', responsible_person: '', responsible_email: '', deadline: '', status: 'Pending' });

  const handleDownloadPDF = () => {
    if (!id) return;
    const path = `/meetings/${id}/pdf`;
    const fullUrl = api.defaults.baseURL?.startsWith('http') 
      ? `${api.defaults.baseURL}${path}` 
      : `${window.location.origin}${api.defaults.baseURL || '/api/v1'}${path}`;
    window.open(fullUrl, '_blank');
  };

  const { data: meeting, isLoading } = useQuery<Meeting>({
    queryKey: ['meeting', id],
    queryFn: async () => (await api.get(`/meetings/${id}`)).data,
  });

  useEffect(() => {
    if (meeting?.discussion) {
      setDiscussionText(meeting.discussion.summary_text || '');
    }
  }, [meeting]);

  const fetchMeeting = () => {
    queryClient.invalidateQueries({ queryKey: ['meeting', id] });
    queryClient.refetchQueries({ queryKey: ['meeting', id] });
  };

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

  const handleCancelMeeting = async () => {
    if (!meeting || !window.confirm(`Cancel "${meeting.title}"?`)) return;
    try {
      await api.post(`/meetings/${id}/cancel`);
      toast.success('Meeting cancelled');
      queryClient.invalidateQueries({ queryKey: ['meeting', id] });
      queryClient.invalidateQueries({ queryKey: ['meetings'] });
    } catch {
      toast.error('Failed to cancel meeting');
    }
  };

  const handleRescheduleMeeting = async () => {
    const newDate = window.prompt("Enter new date (YYYY-MM-DD):", meeting?.date || "");
    if (!newDate) return;
    const newTime = window.prompt("Enter new time (HH:MM):", meeting?.time || "");
    if (!newTime) return;

    try {
      await api.post(`/meetings/${id}/reschedule`, { date: newDate, time: newTime });
      toast.success('Meeting rescheduled');
      queryClient.invalidateQueries({ queryKey: ['meeting', id] });
      queryClient.invalidateQueries({ queryKey: ['meetings'] });
    } catch {
      toast.error('Failed to reschedule meeting');
    }
  };

  // ── Task Operations ────────────────────────────────
  const handleStatusChange = async (taskId: number, newStatus: string) => {
    try {
      await api.put(`/tasks/${taskId}`, { status: newStatus });
      toast.success('Status updated');
      queryClient.invalidateQueries({ queryKey: ['meeting', id] });
    } catch {
      toast.error('Failed to update task status');
    }
  };

  const handleStartEdit = (task: Task) => {
    setEditingTaskId(task.id);
    setTaskEditData({
      title: task.title,
      description: task.description || '',
      responsible_person: task.responsible_person || '',
      deadline: task.deadline || '',
      status: task.status,
    });
  };

  const handleSaveEdit = async () => {
    if (!editingTaskId) return;
    try {
      await api.put(`/tasks/${editingTaskId}`, taskEditData);
      toast.success('Task updated');
      setEditingTaskId(null);
      queryClient.invalidateQueries({ queryKey: ['meeting', id] });
    } catch {
      toast.error('Failed to update task');
    }
  };

  const handleDeleteTask = async (taskId: number) => {
    if (!window.confirm('Delete this task?')) return;
    try {
      await api.delete(`/tasks/${taskId}`);
      toast.success('Task deleted');
      queryClient.invalidateQueries({ queryKey: ['meeting', id] });
    } catch {
      toast.error('Failed to delete task');
    }
  };

  const handleAddTask = async () => {
    try {
      await api.post(`/tasks/${id}`, {
        title: newTask.title,
        description: newTask.description || null,
        responsible_person: newTask.responsible_person || null,
        responsible_email: newTask.responsible_email || null,
        deadline: newTask.deadline || null,
        status: newTask.status,
      });
      toast.success('Task added');
      setShowAddTask(false);
      setNewTask({ title: '', description: '', responsible_person: '', responsible_email: '', deadline: '', status: 'Pending' });
      queryClient.invalidateQueries({ queryKey: ['meeting', id] });
    } catch {
      toast.error('Failed to add task');
    }
  };

  // ── Discussion Save ────────────────────────────────
  const handleSaveDiscussion = async () => {
    try {
      await api.post(`/meetings/${id}/mom`, {
        attendees: meeting!.attendees.map(a => ({ id: a.id, attendance_status: a.attendance_status })),
        discussion_summary: discussionText,
        tasks: meeting!.tasks.map(t => ({
          title: t.title, description: t.description, responsible_person: t.responsible_person,
          responsible_email: t.responsible_email, deadline: t.deadline, status: t.status,
        })),
      });
      toast.success('Discussion summary updated');
      setEditingDiscussion(false);
      queryClient.invalidateQueries({ queryKey: ['meeting', id] });
    } catch {
      toast.error('Failed to update discussion');
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
    { icon: <ClipboardDocumentListIcon className="w-4 h-4" />, label: 'Mode', value: meeting.meeting_mode },
    { icon: <CalendarDaysIcon className="w-4 h-4" />, label: 'Date', value: meeting.date },
    { icon: <ClockIcon className="w-4 h-4" />, label: 'Time', value: meeting.time },
    { icon: <MapPinIcon className="w-4 h-4" />, label: 'Venue/Link', value: meeting.venue },
    { icon: <UserIcon className="w-4 h-4" />, label: 'Hosted By', value: meeting.hosted_by },
    { icon: <CheckCircleIcon className="w-4 h-4" />, label: 'Status', value: meeting.status },
  ];

  const canAction = meeting.status === 'Scheduled' || meeting.status === 'Rescheduled' || meeting.status === 'Processing';
  const inputClass = 'w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-800 dark:text-white text-sm focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 outline-none transition-all';

  return (
    <div className="space-y-5 max-w-4xl mx-auto">

      {/* ── Top Nav Bar ── */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <Link to="/meetings" className="inline-flex items-center gap-1.5 text-[13px] font-semibold text-slate-500 hover:text-brand-600 dark:text-slate-400 dark:hover:text-brand-400 transition-colors">
          <ArrowLeftIcon className="w-4 h-4" /> Back to Meetings
        </Link>
        <div className="flex flex-wrap items-center gap-2">
          {canAction && (
            <div className="flex flex-wrap gap-2">
              <button
                onClick={handleRescheduleMeeting}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 md:px-3.5 md:py-2 text-[12px] md:text-[13px] font-semibold rounded-xl bg-brand-50 dark:bg-brand-500/10 text-brand-700 dark:text-brand-400 hover:bg-brand-100 dark:hover:bg-brand-500/20 border border-brand-100 dark:border-brand-500/20 transition-all active:scale-[0.98]"
              >
                <CalendarDaysIcon className="w-4 h-4" /> Reschedule
              </button>
              <button
                onClick={handleCancelMeeting}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 md:px-3.5 md:py-2 text-[12px] md:text-[13px] font-semibold rounded-xl bg-orange-50 dark:bg-orange-500/10 text-orange-700 dark:text-orange-400 hover:bg-orange-100 dark:hover:bg-orange-500/20 border border-orange-100 dark:border-orange-500/20 transition-all active:scale-[0.98]"
              >
                <ClockIcon className="w-4 h-4" /> Cancel
              </button>
            </div>
          )}
          
          <div className="flex flex-wrap gap-2">
            <button
              onClick={handleDeleteMeeting}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 md:px-3.5 md:py-2 text-[12px] md:text-[13px] font-semibold rounded-xl bg-red-50 dark:bg-red-500/10 text-red-600 dark:text-red-400 hover:bg-red-100 dark:hover:bg-red-500/20 border border-red-100 dark:border-red-500/20 transition-all active:scale-[0.98]"
            >
              <TrashIcon className="w-4 h-4" /> Delete
            </button>

            {canAction && (
              <Link
                to={`/meetings/${id}/log-mom`}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 md:px-3.5 md:py-2 text-[12px] md:text-[13px] font-semibold rounded-xl bg-emerald-50 dark:bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 hover:bg-emerald-100 dark:hover:bg-emerald-500/20 border border-emerald-100 dark:border-emerald-500/20 transition-all active:scale-[0.98]"
              >
                <PencilSquareIcon className="w-4 h-4" /> Record
              </Link>
            )}

            <button
              onClick={handleDownloadPDF}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 md:px-3.5 md:py-2 text-[12px] md:text-[13px] font-bold rounded-xl bg-brand-600 text-white hover:bg-brand-700 shadow-md shadow-brand-200 dark:shadow-brand-900/40 transition-all active:scale-[0.98]"
            >
              <ArrowDownTrayIcon className="w-4 h-4" /> PDF
            </button>
          </div>
        </div>
      </div>

      {/* ── Recording Section ── */}
      {meeting.status === 'Scheduled' && (
        <RecordingOverlay 
          meetingId={meeting.id} 
          meetingType="Regular" 
          meetingMode={meeting.meeting_mode}
          onComplete={fetchMeeting} 
        />
      )}

      {/* ── Processing Progress Banner ── */}
      {((meeting.status === 'Processing' && !meeting.ai_summary_link) || meeting.status === 'Scheduled') && (
        <ProcessingBanner
          meetingId={meeting.id}
          meetingType="Regular"
          onComplete={fetchMeeting}
        />
      )}

      {/* ── Hero Header ── */}
      <div className="relative rounded-2xl overflow-hidden shadow-sm">
        <div className="absolute inset-0 bg-gradient-to-br from-brand-600 to-purple-700" />
        <div className="absolute inset-0 opacity-10" style={{ backgroundImage: 'radial-gradient(circle at 80% 20%, white 1px, transparent 1px)', backgroundSize: '24px 24px' }} />
        <div className="relative z-10 p-6 text-white">
          <div className="flex items-center gap-2 mb-1">
            <span className="bg-white/20 px-2 py-0.5 rounded text-[10px] font-mono border border-white/10 uppercase tracking-widest text-brand-100">
              Meeting #{meeting.id}
            </span>
            <p className="text-[11px] font-bold uppercase tracking-widest text-brand-200">Details</p>
          </div>
          <h2 className="text-xl md:text-2xl font-extrabold mb-4">{meeting.title}</h2>
          <div className="grid grid-cols-1 xs:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
            {metaItems.filter(i => i.value).map((item, idx) => (
              <div key={idx} className="bg-white/10 rounded-xl px-3 py-2.5 md:px-3.5 md:py-3 backdrop-blur-sm">
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

      {/* ── Next Meeting ── */}
      {meeting.next_meeting && (meeting.next_meeting.next_date || meeting.next_meeting.next_time) && (
        <Section title="Next Meeting Schedule" icon={<CalendarDaysIcon className="w-[18px] h-[18px]" />}>
          <div className="flex flex-col sm:flex-row gap-4 p-4 rounded-xl bg-orange-50 dark:bg-orange-500/10 border border-orange-200 dark:border-orange-500/20">
            {meeting.next_meeting.next_date && (
              <div className="text-[13px] font-semibold text-orange-800 dark:text-orange-400">📅 Date: {meeting.next_meeting.next_date}</div>
            )}
            {meeting.next_meeting.next_time && (
              <div className="text-[13px] font-semibold text-orange-800 dark:text-orange-400">⏰ Time: {meeting.next_meeting.next_time}</div>
            )}
          </div>
        </Section>
      )}

      {/* ── Meeting Intelligence Archive ── */}
      {(meeting.recording_link || meeting.ai_summary_link || meeting.drive_transcript_id || meeting.drive_logs_link) && (
        <Section title="Meeting Intelligence Archive" icon={<MicrophoneIcon className="w-[18px] h-[18px]" />}>
          <div className="p-5 rounded-2xl bg-slate-50 dark:bg-white/5 border border-slate-100 dark:border-white/10">
            <div className="flex flex-col gap-4">
              <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
                <div className="space-y-1 text-center sm:text-left">
                  <p className="text-sm font-bold text-slate-900 dark:text-white">Central Intelligence Repository</p>
                  <p className="text-[11px] font-medium text-slate-500 uppercase tracking-tight">3-Asset Cloud Evidence Architecture</p>
                </div>
                {meeting.recording_link && (meeting.recording_link.endsWith('.webm') || meeting.recording_link.endsWith('.mp3')) && (
                    <audio controls className="h-9 w-full max-w-xs">
                      <source src={meeting.recording_link} type="audio/webm" />
                    </audio>
                )}
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mt-2">
                {meeting.ai_summary_link && (
                  <a href={meeting.ai_summary_link} target="_blank" rel="noreferrer" 
                     className="flex items-center gap-3 p-3.5 bg-white dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700 rounded-xl hover:border-emerald-400 dark:hover:border-emerald-500 transition-all group">
                    <ClipboardDocumentListIcon className="w-5 h-5 text-emerald-500" />
                    <div className="flex-1 min-w-0">
                      <p className="text-[12px] font-bold text-slate-800 dark:text-white">Executive Summary</p>
                      <p className="text-[10px] text-slate-500 group-hover:text-emerald-500">AI-Synthesized Briefing</p>
                    </div>
                  </a>
                )}
                {meeting.drive_transcript_id && (
                  <a href={meeting.drive_transcript_id} target="_blank" rel="noreferrer" 
                     className="flex items-center gap-3 p-3.5 bg-white dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700 rounded-xl hover:border-blue-400 dark:hover:border-blue-500 transition-all group">
                    <span className="text-[18px] text-blue-500">🎤</span>
                    <div className="flex-1 min-w-0">
                      <p className="text-[12px] font-bold text-slate-800 dark:text-white">Verbatim Transcript</p>
                      <p className="text-[10px] text-slate-500 group-hover:text-blue-500">Line-Numbered Speech Record</p>
                    </div>
                  </a>
                )}
                {meeting.drive_logs_link && (
                  <a href={meeting.drive_logs_link} target="_blank" rel="noreferrer" 
                     className="flex items-center gap-3 p-3.5 bg-white dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700 rounded-xl hover:border-orange-400 dark:hover:border-orange-500 transition-all group col-span-1 sm:col-span-2">
                    <ClipboardDocumentListIcon className="w-5 h-5 text-orange-500" />
                    <div className="flex-1 min-w-0">
                      <p className="text-[12px] font-bold text-slate-800 dark:text-white">AI Audit Trail</p>
                      <p className="text-[10px] text-slate-500 group-hover:text-orange-500">Segment-by-Segment Process Log</p>
                    </div>
                  </a>
                )}
              </div>
              <div className="pt-4 border-t border-slate-200 dark:border-white/10 flex items-center justify-between">
                 <div className="flex items-center gap-2 text-[10px] font-bold text-emerald-600 dark:text-emerald-400 uppercase tracking-wider">
                   <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                   AI Extraction Verified & Storage Optimized
                 </div>
              </div>
            </div>
          </div>
        </Section>
      )}

      {/* ── Attendees ── */}
      <Section title="Attendees" icon={<UserIcon className="w-[18px] h-[18px]" />}>
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
                    <div className="flex flex-col gap-1 w-full pl-2 border-l-2 border-slate-200 dark:border-slate-700">
                      <p className="text-[13px] font-semibold text-slate-800 dark:text-white truncate">{a.user_name} {a.designation ? `- ${a.designation}` : ''}</p>
                      <p className="text-[11px] text-slate-500 font-medium truncate">
                        {a.email || 'No email'} {a.whatsapp_number ? `| ${a.whatsapp_number}` : ''}
                      </p>
                      {a.remarks && (
                        <p className="text-[11px] text-slate-400 italic">"{a.remarks}"</p>
                      )}
                    </div>
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

      {/* ── Discussion Summary (Editable) ── */}
      <Section 
        title="Discussion Summary" 
        icon={<CheckCircleIcon className="w-[18px] h-[18px]" />}
        action={
          !editingDiscussion ? (
            <button onClick={() => setEditingDiscussion(true)} className="inline-flex items-center gap-1 px-2.5 py-1 text-[11px] font-bold rounded-lg bg-brand-50 dark:bg-brand-500/10 text-brand-600 dark:text-brand-400 hover:bg-brand-100 transition-colors">
              <PencilSquareIcon className="w-3 h-3" /> Edit
            </button>
          ) : (
            <div className="flex gap-2">
              <button onClick={handleSaveDiscussion} className="inline-flex items-center gap-1 px-2.5 py-1 text-[11px] font-bold rounded-lg bg-emerald-50 text-emerald-600 hover:bg-emerald-100 transition-colors">
                <CheckCircleIcon className="w-3 h-3" /> Save
              </button>
              <button onClick={() => { setEditingDiscussion(false); setDiscussionText(meeting?.discussion?.summary_text || ''); }} className="inline-flex items-center gap-1 px-2.5 py-1 text-[11px] font-bold rounded-lg bg-slate-100 text-slate-500 hover:bg-slate-200 transition-colors">
                <XMarkIcon className="w-3 h-3" /> Cancel
              </button>
            </div>
          )
        }
      >
        {editingDiscussion ? (
          <textarea
            rows={6}
            value={discussionText}
            onChange={(e) => setDiscussionText(e.target.value)}
            className={`${inputClass} resize-none leading-relaxed`}
            placeholder="Enter discussion summary..."
          />
        ) : (
          meeting.discussion ? (
            <div 
              className="text-[13px] text-slate-700 dark:text-slate-300 leading-relaxed space-y-2"
              dangerouslySetInnerHTML={{ 
                __html: (meeting.discussion.summary_text || "")
                  .replace(/\*\*\s*(.*?)\s*\*\*/gs, '<b class="font-extrabold text-slate-900 dark:text-white">$1</b>')
                  .replace(/\n/g, '<br/>')
              }} 
            />
          ) : (
            <p className="text-sm text-slate-400 italic">No discussion summary recorded. Click "Edit" to add one.</p>
          )
        )}
      </Section>

      {/* ── Tasks (Fully Editable) ── */}
      <Section 
        title="Action Items / Tasks" 
        icon={<ClipboardDocumentListIcon className="w-[18px] h-[18px]" />}
        action={
          <button onClick={() => setShowAddTask(true)} className="inline-flex items-center gap-1 px-2.5 py-1 text-[11px] font-bold rounded-lg bg-brand-50 dark:bg-brand-500/10 text-brand-600 dark:text-brand-400 hover:bg-brand-100 transition-colors">
            <PlusIcon className="w-3 h-3" /> Add Task
          </button>
        }
      >
        {/* Add Task Form */}
        {showAddTask && (
          <div className="mb-4 p-4 rounded-xl bg-brand-50/50 dark:bg-brand-500/5 border border-brand-200 dark:border-brand-500/20 space-y-3">
            <p className="text-[12px] font-bold text-brand-700 dark:text-brand-400 uppercase tracking-wide">New Task</p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <input placeholder="Task Title *" value={newTask.title} onChange={(e) => setNewTask(p => ({ ...p, title: e.target.value }))} className={inputClass} />
              <input placeholder="Responsible Person" value={newTask.responsible_person} onChange={(e) => setNewTask(p => ({ ...p, responsible_person: e.target.value }))} className={inputClass} />
              <input placeholder="Responsible Email" value={newTask.responsible_email} onChange={(e) => setNewTask(p => ({ ...p, responsible_email: e.target.value }))} className={inputClass} />
              <input type="date" value={newTask.deadline} onChange={(e) => setNewTask(p => ({ ...p, deadline: e.target.value }))} className={inputClass} />
            </div>
            <input placeholder="Description" value={newTask.description} onChange={(e) => setNewTask(p => ({ ...p, description: e.target.value }))} className={inputClass} />
            <div className="flex gap-2 justify-end">
              <button onClick={() => setShowAddTask(false)} className="px-3 py-1.5 text-[12px] font-bold rounded-lg bg-slate-100 text-slate-500 hover:bg-slate-200 transition-colors">Cancel</button>
              <button onClick={handleAddTask} disabled={!newTask.title.trim()} className="px-3 py-1.5 text-[12px] font-bold rounded-lg bg-brand-600 text-white hover:bg-brand-700 disabled:opacity-50 transition-all">Add Task</button>
            </div>
          </div>
        )}

        {meeting.tasks.length === 0 && !showAddTask ? (
          <p className="text-sm text-slate-400">No tasks recorded.</p>
        ) : (
          <div className="space-y-2.5">
            {meeting.tasks.map((t) => (
              <div key={t.id} className="rounded-xl border border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-white/5 overflow-hidden">
                {editingTaskId === t.id ? (
                  /* ── Inline Edit Mode ── */
                  <div className="p-4 space-y-3 bg-amber-50/30 dark:bg-amber-500/5">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      <input value={taskEditData.title} onChange={(e) => setTaskEditData(p => ({ ...p, title: e.target.value }))} className={inputClass} placeholder="Task Title" />
                      <input value={taskEditData.responsible_person} onChange={(e) => setTaskEditData(p => ({ ...p, responsible_person: e.target.value }))} className={inputClass} placeholder="Responsible Person" />
                      <input type="date" value={taskEditData.deadline} onChange={(e) => setTaskEditData(p => ({ ...p, deadline: e.target.value }))} className={inputClass} />
                      <select value={taskEditData.status} onChange={(e) => setTaskEditData(p => ({ ...p, status: e.target.value }))} className={inputClass}>
                        <option value="Pending">Pending</option>
                        <option value="In Progress">In Progress</option>
                        <option value="Completed">Completed</option>
                      </select>
                    </div>
                    <input value={taskEditData.description} onChange={(e) => setTaskEditData(p => ({ ...p, description: e.target.value }))} className={inputClass} placeholder="Description" />
                    <div className="flex gap-2 justify-end">
                      <button onClick={() => setEditingTaskId(null)} className="px-3 py-1.5 text-[12px] font-bold rounded-lg bg-slate-100 text-slate-500 hover:bg-slate-200 transition-colors">Cancel</button>
                      <button onClick={handleSaveEdit} className="px-3 py-1.5 text-[12px] font-bold rounded-lg bg-brand-600 text-white hover:bg-brand-700 transition-all">Save</button>
                    </div>
                  </div>
                ) : (
                  /* ── View Mode ── */
                  <div className="flex flex-col sm:flex-row sm:items-center gap-3 p-4">
                    <div className="flex-1 min-w-0">
                      <p className="text-[13px] font-semibold text-slate-800 dark:text-white">{t.title}</p>
                      {t.description && <p className="text-[11px] text-slate-400 mt-0.5 line-clamp-2">{t.description}</p>}
                      <div className="flex flex-wrap items-center gap-3 mt-1.5 text-[11px] text-slate-400">
                        {t.responsible_person && <span className="flex items-center gap-1"><UserIcon className="w-3 h-3" />{t.responsible_person}</span>}
                        {t.deadline && <span className="flex items-center gap-1"><CalendarDaysIcon className="w-3 h-3" />Due: {t.deadline}</span>}
                      </div>
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
                      <select
                        value={t.status}
                        onChange={(e) => handleStatusChange(t.id, e.target.value)}
                        className={`text-[12px] font-bold px-3 py-1.5 rounded-lg border cursor-pointer focus:outline-none focus:ring-2 focus:ring-brand-400 ${statusColors[t.status] ?? statusColors['Pending']}`}
                      >
                        <option value="Pending">Pending</option>
                        <option value="In Progress">In Progress</option>
                        <option value="Completed">Completed</option>
                      </select>
                      <button onClick={() => handleStartEdit(t)} className="p-1.5 rounded-lg text-slate-400 hover:text-brand-500 hover:bg-brand-50 dark:hover:bg-brand-500/10 transition-colors" title="Edit Task">
                        <PencilSquareIcon className="w-4 h-4" />
                      </button>
                      <button onClick={() => handleDeleteTask(t.id)} className="p-1.5 rounded-lg text-slate-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-500/10 transition-colors" title="Delete Task">
                        <TrashIcon className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </Section>

    </div>
  );
}
