import { useState } from 'react';
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
    ShieldCheckIcon,
    DocumentIcon,
    MicrophoneIcon,
    PlusIcon,
    XMarkIcon,
} from '@heroicons/react/24/outline';
import RecordingOverlay from '../components/RecordingOverlay';
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
                    <span className="text-brand-500 font-bold">{icon}</span>
                    <h3 className="text-[14px] font-bold text-slate-800 dark:text-white uppercase tracking-wide">{title}</h3>
                </div>
                {action && <div>{action}</div>}
            </div>
            <div className="p-6">{children}</div>
        </div>
    );
}

export default function BRDetailPage() {
    const { id } = useParams<{ id: string }>();
    const queryClient = useQueryClient();
    const navigate = useNavigate();

    // ── Editable State ─────────────────────────────────
    const [editingTaskId, setEditingTaskId] = useState<number | null>(null);
    const [taskEditData, setTaskEditData] = useState<{ title: string; description: string; responsible_person: string; deadline: string; status: string }>({ title: '', description: '', responsible_person: '', deadline: '', status: 'Pending' });

    const handleDownloadPDF = () => {
        if (!id) return;
        window.open(`${window.location.origin}/api/v1/br/${id}/pdf`, '_blank');
    };

    const { data: meeting, isLoading } = useQuery<Meeting>({
        queryKey: ['br', id],
        queryFn: async () => (await api.get(`/br/${id}`)).data,
    });

    const refreshData = () => {
        queryClient.invalidateQueries({ queryKey: ['br', id] });
        queryClient.refetchQueries({ queryKey: ['br', id] });
    };

    const handleDeleteMeeting = async () => {
        if (!meeting || !window.confirm(`Delete board resolution "${meeting.title}"?\nThis action cannot be undone.`)) return;
        try {
            await api.delete(`/br/${id}`);
            toast.success('Board resolution deleted');
            queryClient.invalidateQueries({ queryKey: ['br'] });
            navigate('/br');
        } catch {
            toast.error('Failed to delete resolution');
        }
    };

    const handleCancelMeeting = async () => {
        if (!meeting || !window.confirm(`Cancel board resolution "${meeting.title}"?`)) return;
        try {
            await api.post(`/br/${id}/cancel`);
            toast.success('Resolution cancelled');
            queryClient.invalidateQueries({ queryKey: ['br', id] });
        } catch {
            toast.error('Failed to cancel resolution');
        }
    };

    const handleRescheduleMeeting = async () => {
        const newDate = window.prompt("Enter new date (YYYY-MM-DD):", meeting?.date || "");
        if (!newDate) return;
        const newTime = window.prompt("Enter new time (HH:MM):", meeting?.time || "");
        if (!newTime) return;

        try {
            await api.post(`/br/${id}/reschedule`, { date: newDate, time: newTime });
            toast.success('Resolution rescheduled');
            queryClient.invalidateQueries({ queryKey: ['br', id] });
        } catch {
            toast.error('Failed to reschedule resolution');
        }
    };

    // ── Task Operations ────────────────────────────────
    const handleStatusChange = async (taskId: number, newStatus: string) => {
        try {
            await api.put(`/br/tasks/${taskId}`, { status: newStatus });
            toast.success('Task status updated');
            queryClient.invalidateQueries({ queryKey: ['br', id] });
        } catch {
            toast.error('Failed to update task');
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
            await api.put(`/br/tasks/${editingTaskId}`, taskEditData);
            toast.success('Task updated');
            setEditingTaskId(null);
            queryClient.invalidateQueries({ queryKey: ['br', id] });
        } catch {
            toast.error('Failed to update task');
        }
    };

    if (isLoading || !meeting) {
        return (
            <div className="flex flex-col items-center justify-center h-64 gap-3">
                <div className="w-8 h-8 border-3 border-brand-500 border-t-transparent rounded-full animate-spin" />
                <p className="text-sm font-bold text-slate-400 uppercase tracking-widest">Loading Board Resolution…</p>
            </div>
        );
    }

    const metaItems = [
        { icon: <BuildingOfficeIcon className="w-4 h-4" />, label: 'Organization', value: meeting.organization },
        { icon: <MapPinIcon className="w-4 h-4" />, label: 'Venue', value: meeting.venue },
        { icon: <CalendarDaysIcon className="w-4 h-4" />, label: 'Meeting Date', value: meeting.date },
        { icon: <ClockIcon className="w-4 h-4" />, label: 'Meeting Time', value: meeting.time },
        { icon: <ShieldCheckIcon className="w-4 h-4" />, label: 'Status', value: meeting.status },
    ];

    const canAction = meeting.status === 'Scheduled' || meeting.status === 'Rescheduled' || meeting.status === 'Processing';
    const inputClass = 'w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-800 dark:text-white text-sm focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 outline-none transition-all';

    return (
        <div className="space-y-6 max-w-5xl mx-auto">
            {/* ── Top Bar ── */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <Link to="/br" className="inline-flex items-center gap-1.5 text-[13px] font-bold text-slate-500 hover:text-brand-600 dark:text-slate-400 dark:hover:text-brand-400 transition-colors uppercase tracking-wide">
                    <ArrowLeftIcon className="w-4 h-4" /> All Resolutions
                </Link>
                <div className="flex flex-wrap items-center gap-2">
                    {meeting.status === 'Scheduled' && (
                        <RecordingOverlay 
                            meetingId={meeting.id} 
                            meetingType="BR" 
                            onComplete={refreshData} 
                        />
                    )}
                    <button
                        onClick={() => navigate(`/br/${id}/log-mom`)}
                        className="inline-flex items-center gap-1.5 px-3.5 py-2 text-[13px] font-semibold rounded-xl bg-brand-50 dark:bg-brand-500/10 text-brand-700 dark:text-brand-400 hover:bg-brand-100 dark:hover:bg-brand-500/20 border border-brand-100 dark:border-brand-500/20 transition-all active:scale-[0.98]"
                    >
                        <PencilSquareIcon className="w-4 h-4" /> Pass Resolution
                    </button>
                    {canAction && (
                        <>
                            <button
                                onClick={handleRescheduleMeeting}
                                className="inline-flex items-center gap-1.5 px-3.5 py-2 text-[13px] font-semibold rounded-xl bg-brand-50 dark:bg-brand-500/10 text-brand-700 dark:text-brand-400 hover:bg-brand-100 dark:hover:bg-brand-500/20 border border-brand-100 dark:border-brand-500/20 transition-all active:scale-[0.98]"
                            >
                                <CalendarDaysIcon className="w-4 h-4" /> Reschedule
                            </button>
                            <button
                                onClick={handleCancelMeeting}
                                className="inline-flex items-center gap-1.5 px-3.5 py-2 text-[13px] font-semibold rounded-xl bg-orange-50 dark:bg-orange-500/10 text-orange-700 dark:text-orange-400 hover:bg-orange-100 dark:hover:bg-orange-500/20 border border-orange-100 dark:border-orange-500/20 transition-all active:scale-[0.98]"
                            >
                                <ClockIcon className="w-4 h-4" /> Cancel
                            </button>
                        </>
                    )}

                    <button
                        onClick={handleDeleteMeeting}
                        className="inline-flex items-center gap-1.5 px-3.5 py-2 text-[13px] font-semibold rounded-xl bg-red-50 dark:bg-red-500/10 text-red-600 dark:text-red-400 hover:bg-red-100 dark:hover:bg-red-500/20 border border-red-100 dark:border-red-500/20 transition-all active:scale-[0.98]"
                    >
                        <TrashIcon className="w-4 h-4" /> Delete
                    </button>

                    <button
                        onClick={handleDownloadPDF}
                        className="inline-flex items-center gap-1.5 px-3.5 py-2 text-[13px] font-bold rounded-xl bg-brand-600 text-white hover:bg-brand-700 shadow-md shadow-brand-200 dark:shadow-brand-900/40 transition-all active:scale-[0.98]"
                    >
                        <ArrowDownTrayIcon className="w-4 h-4" /> Download BR PDF
                    </button>
                </div>
            </div>

            {/* ── Hero Header ── */}
            <div className="relative rounded-2xl overflow-hidden shadow-sm">
                <div className="absolute inset-0 bg-gradient-to-br from-amber-600 to-brand-700" />
                <div className="absolute inset-0 opacity-10" style={{ backgroundImage: 'radial-gradient(circle at 80% 20%, white 1px, transparent 1px)', backgroundSize: '24px 24px' }} />
                <div className="relative z-10 p-6 text-white">
                    <p className="text-[11px] font-bold uppercase tracking-widest text-brand-200 mb-1">Board Resolution Details</p>
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

            {/* ── Resolution Details ── */}
            {meeting.discussion && (
                <Section title="Resolution Wording" icon={<CheckCircleIcon className="w-[18px] h-[18px]" />}>
                    <p className="text-[14px] text-slate-700 dark:text-slate-300 whitespace-pre-wrap leading-relaxed font-medium bg-slate-50 dark:bg-white/5 p-4 rounded-xl border border-slate-100 dark:border-slate-800">
                        {meeting.discussion.summary_text}
                    </p>
                </Section>
            )}

            {/* ── Intelligence Archive ── */}
            {(meeting.recording_link || meeting.ai_summary_link || meeting.drive_transcript_id || meeting.drive_logs_link) && (
                <Section title="Governance Intelligence Archive" icon={<MicrophoneIcon className="w-[18px] h-[18px]" />}>
                    <div className="p-5 rounded-2xl bg-slate-50 dark:bg-white/5 border border-slate-100 dark:border-white/10">
                        <div className="flex flex-col gap-5">
                            <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
                                <div className="space-y-1 text-center sm:text-left">
                                    <p className="text-sm font-bold text-slate-900 dark:text-white">Central Intelligence Repository</p>
                                    <p className="text-[11px] font-medium text-slate-500 uppercase tracking-tight">Governance-Grade Cloud Evidence</p>
                                </div>
                                {meeting.recording_link && (meeting.recording_link.endsWith('.webm') || meeting.recording_link.endsWith('.mp3')) && (
                                    <audio controls className="h-9 w-full max-w-xs shadow-sm">
                                        <source src={meeting.recording_link} type="audio/webm" />
                                    </audio>
                                )}
                            </div>
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mt-2">
                                {meeting.recording_link && !meeting.recording_link.endsWith('.webm') && (
                                    <a href={meeting.recording_link} target="_blank" rel="noreferrer" className="flex items-center gap-3.5 p-4 bg-white dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700 rounded-xl hover:border-brand-400 transition-all group shadow-sm">
                                        <DocumentIcon className="w-5 h-5 text-brand-500" />
                                        <div className="flex-1 min-w-0"><p className="text-[12px] font-bold text-slate-800 dark:text-white">Official Resolution Report</p><p className="text-[10px] text-slate-500 group-hover:text-brand-500">Professional Board Record</p></div>
                                    </a>
                                )}
                                {meeting.ai_summary_link && (
                                    <a href={meeting.ai_summary_link} target="_blank" rel="noreferrer" className="flex items-center gap-3.5 p-4 bg-white dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700 rounded-xl hover:border-emerald-400 transition-all group shadow-sm">
                                        <ClipboardDocumentListIcon className="w-5 h-5 text-emerald-500" />
                                        <div className="flex-1 min-w-0"><p className="text-[12px] font-bold text-slate-800 dark:text-white">Executive Summary</p><p className="text-[10px] text-slate-500 group-hover:text-emerald-500">AI-Synthesized Briefing</p></div>
                                    </a>
                                )}
                                {meeting.drive_transcript_id && (
                                    <a href={meeting.drive_transcript_id} target="_blank" rel="noreferrer" className="flex items-center gap-3.5 p-4 bg-white dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700 rounded-xl hover:border-blue-400 transition-all group shadow-sm">
                                        <span className="text-[18px] text-blue-500">🎤</span>
                                        <div className="flex-1 min-w-0"><p className="text-[12px] font-bold text-slate-800 dark:text-white">Verbatim Transcript</p><p className="text-[10px] text-slate-500 group-hover:text-blue-500">Line-Numbered Speech Record</p></div>
                                    </a>
                                )}
                                {meeting.drive_logs_link && (
                                    <a href={meeting.drive_logs_link} target="_blank" rel="noreferrer" className="flex items-center gap-3.5 p-4 bg-white dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700 rounded-xl hover:border-orange-400 transition-all group shadow-sm">
                                        <ClipboardDocumentListIcon className="w-5 h-5 text-orange-500" />
                                        <div className="flex-1 min-w-0"><p className="text-[12px] font-bold text-slate-800 dark:text-white">AI Audit Trail</p><p className="text-[10px] text-slate-500 group-hover:text-orange-500">Segment-by-Segment Process Log</p></div>
                                    </a>
                                )}
                            </div>
                            <div className="pt-4 border-t border-slate-200 dark:border-white/10">
                                <div className="flex items-center gap-2 text-[10px] font-bold text-emerald-600 dark:text-emerald-400 uppercase tracking-widest">
                                    <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                                    Board Intelligence Extracted & Verified
                                </div>
                            </div>
                        </div>
                    </div>
                </Section>
            )}

            {/* ── Directors ── */}
            <Section title="Directors" icon={<UserIcon className="w-[18px] h-[18px]" />}>
                {meeting.attendees.length === 0 ? (
                    <p className="text-sm text-slate-400">No directors recorded.</p>
                ) : (
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                        {meeting.attendees.map((a) => {
                            const present = String(a.attendance_status).toLowerCase().includes('present');
                            return (
                                <div key={a.id} className="flex items-center gap-3 p-3 rounded-xl bg-slate-50 dark:bg-white/5 border border-slate-100 dark:border-slate-800">
                                    <div className="w-9 h-9 rounded-full bg-amber-100 dark:bg-amber-500/20 flex items-center justify-center text-amber-700 dark:text-amber-400 text-[13px] font-bold shrink-0">
                                        {a.user_name.charAt(0).toUpperCase()}
                                    </div>
                                    <div className="min-w-0 flex-1">
                                        <div className="flex flex-col gap-1 w-full pl-2 border-l-2 border-slate-200 dark:border-slate-700">
                                            <p className="text-[13px] font-semibold text-slate-800 dark:text-white truncate">{a.user_name} {a.designation ? `- ${a.designation}` : ''}</p>
                                            <p className="text-[11px] text-slate-500 font-medium truncate">{a.email || 'No email'}</p>
                                            {a.remarks && <p className="text-[11px] text-slate-400 italic">"{a.remarks}"</p>}
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
            <Section title="Agenda / Resolutions" icon={<ClipboardDocumentListIcon className="w-[18px] h-[18px]" />}>
                {meeting.agenda_items.length === 0 ? (
                    <p className="text-sm text-slate-400">No agenda items recorded for this resolution.</p>
                ) : (
                    <div className="space-y-3">
                        {meeting.agenda_items.map((a, i) => (
                            <div key={a.id} className="flex gap-4 p-4 rounded-xl bg-slate-50 dark:bg-white/5 border border-slate-100 dark:border-slate-800">
                                <span className="w-6 h-6 rounded-full bg-brand-600 text-white text-[11px] font-bold flex items-center justify-center shrink-0 mt-0.5">{i + 1}</span>
                                <div>
                                    <p className="text-[14px] font-bold text-slate-800 dark:text-white">{a.topic}</p>
                                    {a.description && <p className="text-[12px] text-slate-500 dark:text-slate-400 mt-1">{a.description}</p>}
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </Section>

            {/* ── Action Mandates (Editable Tasks) ── */}
            <Section title="Action Mandates" icon={<ClipboardDocumentListIcon className="w-[18px] h-[18px]" />}>
                {meeting.tasks.length === 0 ? (
                    <p className="text-sm text-slate-400">No mandates recorded.</p>
                ) : (
                    <div className="space-y-2.5">
                        {meeting.tasks.map((t) => (
                            <div key={t.id} className="rounded-xl border border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-white/5 overflow-hidden">
                                {editingTaskId === t.id ? (
                                    <div className="p-4 space-y-3 bg-amber-50/30 dark:bg-amber-500/5">
                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                                            <input value={taskEditData.title} onChange={(e) => setTaskEditData(p => ({ ...p, title: e.target.value }))} className={inputClass} placeholder="Mandate Title" />
                                            <input value={taskEditData.responsible_person} onChange={(e) => setTaskEditData(p => ({ ...p, responsible_person: e.target.value }))} className={inputClass} placeholder="Responsible Director" />
                                            <input type="date" value={taskEditData.deadline} onChange={(e) => setTaskEditData(p => ({ ...p, deadline: e.target.value }))} className={inputClass} />
                                            <select value={taskEditData.status} onChange={(e) => setTaskEditData(p => ({ ...p, status: e.target.value }))} className={inputClass}>
                                                <option value="Pending">Pending</option>
                                                <option value="In Progress">In Progress</option>
                                                <option value="Completed">Completed</option>
                                            </select>
                                        </div>
                                        <div className="flex gap-2 justify-end">
                                            <button onClick={() => setEditingTaskId(null)} className="px-3 py-1.5 text-[12px] font-bold rounded-lg bg-slate-100 text-slate-500 hover:bg-slate-200 transition-colors">Cancel</button>
                                            <button onClick={handleSaveEdit} className="px-3 py-1.5 text-[12px] font-bold rounded-lg bg-brand-600 text-white hover:bg-brand-700 transition-all">Save</button>
                                        </div>
                                    </div>
                                ) : (
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
                                            <button onClick={() => handleStartEdit(t)} className="p-1.5 rounded-lg text-slate-400 hover:text-brand-500 hover:bg-brand-50 dark:hover:bg-brand-500/10 transition-colors" title="Edit Mandate">
                                                <PencilSquareIcon className="w-4 h-4" />
                                            </button>
                                        </div>
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                )}
            </Section>

            {/* ── Supporting Docs ── */}
            <Section title="Supporting Evidence" icon={<PaperClipIcon className="w-[18px] h-[18px]" />}>
                <div className="p-4 rounded-xl bg-slate-50 dark:bg-white/5 border border-slate-100 dark:border-white/5 text-center">
                    <p className="text-sm text-slate-500">No supporting documents uploaded.</p>
                </div>
            </Section>
        </div>
    );
}

function PaperClipIcon(props: any) {
    return (
        <svg {...props} xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M18.375 12.739l-7.693 7.693a4.5 4.5 0 01-6.364-6.364l10.94-10.94A3 3 0 1119.5 7.372L8.552 18.32a1.5 1.5 0 01-2.121-2.121l10.94-10.94" />
        </svg>
    )
}
