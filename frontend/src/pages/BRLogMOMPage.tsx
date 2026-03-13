import { useState, useEffect } from 'react';
import { useNavigate, useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import toast from 'react-hot-toast';
import { PlusIcon, TrashIcon, ArrowLeftIcon, CloudArrowUpIcon, DocumentIcon, XMarkIcon } from '@heroicons/react/24/outline';
import api from '../api';
import type { Meeting, MeetingMOMUpdatePayload, AttendanceStatus, TaskStatus } from '../types';

export default function BRLogMOMPage() {
    const { id } = useParams<{ id: string }>();
    const navigate = useNavigate();

    const { data: meeting, isLoading: meetingLoading } = useQuery<Meeting>({
        queryKey: ['br-meeting', id],
        queryFn: async () => (await api.get(`/br/${id}`)).data,
        enabled: !!id,
    });

    const [form, setForm] = useState<MeetingMOMUpdatePayload>({
        attendees: [],
        discussion_summary: '',
        tasks: [],
        next_meeting: { next_date: '', next_time: '' },
    });
    const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        if (meeting) {
            setForm({
                attendees: meeting.attendees.map(a => ({
                    id: a.id,
                    attendance_status: a.attendance_status || 'Present',
                    remarks: a.remarks || '',
                })),
                discussion_summary: meeting.discussion?.summary_text || '',
                tasks: meeting.tasks.map(t => ({
                    title: t.title,
                    description: t.description || '',
                    responsible_person: t.responsible_person || '',
                    responsible_email: t.responsible_email || '',
                    deadline: t.deadline || '',
                    status: t.status,
                    _manualMode: (t.responsible_person && !meeting.attendees.some(a => a.user_name === t.responsible_person)) as boolean,
                }) as any),
                next_meeting: {
                    next_date: meeting.next_meeting?.next_date || '',
                    next_time: meeting.next_meeting?.next_time || '',
                },
            });
        }
    }, [meeting]);

    if (meetingLoading || !meeting) {
        return (
            <div className="flex flex-col items-center justify-center min-h-[400px] gap-4">
                <div className="w-8 h-8 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
                <p className="text-sm text-slate-500 font-medium">Loading resolution context...</p>
            </div>
        );
    }

    const updateField = (field: string, value: any) => setForm((p) => ({ ...p, [field]: value }));

    const updateAttendee = (i: number, field: 'attendance_status' | 'remarks', value: string) =>
        setForm((p) => ({
            ...p,
            attendees: p.attendees.map((a, idx) => (idx === i ? { ...a, [field]: value } : a)),
        }));

    const addTask = () =>
        setForm((p) => ({
            ...p,
            tasks: [
                ...p.tasks,
                { title: '', description: '', responsible_person: '', responsible_email: '', deadline: '', status: 'Pending' as TaskStatus, _manualMode: false } as any,
            ],
        }));
    const removeTask = (i: number) =>
        setForm((p) => ({ ...p, tasks: p.tasks.filter((_, idx) => idx !== i) }));
    const updateTask = (i: number, field: string, value: string) =>
        setForm((p) => ({
            ...p,
            tasks: p.tasks.map((t, idx) => (idx === i ? { ...t, [field]: value } : t)),
        }));

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files) {
            const newFiles = Array.from(e.target.files);
            setSelectedFiles(prev => [...prev, ...newFiles]);
        }
    };

    const removeFile = (index: number) => {
        setSelectedFiles(prev => prev.filter((_, i) => i !== index));
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        try {
            const payload = {
                attendees: form.attendees,
                discussion_summary: form.discussion_summary,
                tasks: form.tasks.map((t) => ({
                    ...t,
                    deadline: t.deadline && t.deadline.trim() !== '' ? t.deadline : null,
                    responsible_email: t.responsible_email && t.responsible_email.trim() !== '' ? t.responsible_email : null,
                })),
                next_meeting:
                    form.next_meeting && (form.next_meeting.next_date?.trim() !== '' || form.next_meeting.next_time?.trim() !== '')
                        ? {
                            next_date: form.next_meeting.next_date && form.next_meeting.next_date.trim() !== '' ? form.next_meeting.next_date : null,
                            next_time: form.next_meeting.next_time && form.next_meeting.next_time.trim() !== '' ? form.next_meeting.next_time : null,
                        }
                        : null,
            };

            // Create FormData to handle files and JSON
            const formData = new FormData();
            formData.append('data_str', JSON.stringify(payload));
            selectedFiles.forEach(file => {
                formData.append('files', file);
            });

            await api.post(`/br/${id}/mom`, formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });

            toast.success('Resolution passed and documents archived successfully!');
            navigate(`/br/${id}`);
        } catch (err: any) {
            console.error(err);
            toast.error('Failed to archive resolution');
        } finally {
            setLoading(false);
        }
    };

    const inputClass = 'w-full px-4 py-2.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-slate-900 dark:text-white text-sm focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 transition-all outline-none';
    const labelClass = 'block text-[12px] font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-1.5 ml-1';

    return (
        <div className="max-w-4xl mx-auto space-y-6">
            <div className="flex flex-col gap-1">
                <Link to={`/br/${id}`} className="inline-flex items-center gap-1.5 text-xs font-bold text-slate-400 hover:text-brand-500 transition-colors mb-2">
                    <ArrowLeftIcon className="w-3 h-3" /> Back to Details
                </Link>
                <h2 className="text-2xl font-extrabold text-slate-900 dark:text-white">Record Final Board Resolution</h2>
                <p className="text-[13px] text-slate-500 dark:text-slate-400">
                    Document the decisions, mandates, and supporting evidence for <strong>{meeting.title}</strong>
                </p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-6 pb-20">

                {/* ── Resolution Content ── */}
                <section className="bg-white dark:bg-[#161b27] rounded-2xl border border-slate-100 dark:border-slate-800 shadow-sm p-6 overflow-hidden relative">
                    <div className="absolute top-0 right-0 w-32 h-32 bg-brand-500/5 rounded-full -mr-16 -mt-16 blur-3xl" />
                    <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-4 flex items-center gap-2">
                        <DocumentIcon className="w-5 h-5 text-brand-500" /> Resolution Wording
                    </h3>
                    <textarea
                        rows={8}
                        value={form.discussion_summary}
                        onChange={(e) => updateField('discussion_summary', e.target.value)}
                        className={`${inputClass} font-medium leading-relaxed resize-none`}
                        placeholder="Enter the formal 'RESOLVED THAT...' wording here..."
                        required
                    />
                </section>

                {/* ── Supporting Documents (FILES) ── */}
                <section className="bg-white dark:bg-[#161b27] rounded-2xl border border-slate-100 dark:border-slate-800 shadow-sm p-6">
                    <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-4 flex items-center gap-2">
                        <CloudArrowUpIcon className="w-5 h-5 text-brand-500" /> Reference Documents
                    </h3>
                    <div className="space-y-4">
                        <div className="flex items-center justify-center w-full">
                            <label className="flex flex-col items-center justify-center w-full h-32 border-2 border-slate-200 dark:border-slate-800 border-dashed rounded-2xl cursor-pointer bg-slate-50/50 dark:bg-white/5 hover:bg-slate-100 dark:hover:bg-white/10 transition-all">
                                <div className="flex flex-col items-center justify-center pt-5 pb-6">
                                    <CloudArrowUpIcon className="w-8 h-8 text-slate-400 mb-2" />
                                    <p className="text-xs font-bold text-slate-500">Click to upload Board Papers (PDF, Excel, ZIP)</p>
                                </div>
                                <input type="file" className="hidden" multiple onChange={handleFileChange} />
                            </label>
                        </div>

                        {selectedFiles.length > 0 && (
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                                {selectedFiles.map((file, idx) => (
                                    <div key={idx} className="flex items-center justify-between p-3 rounded-xl bg-brand-50/30 dark:bg-brand-500/5 border border-brand-100 dark:border-brand-500/10">
                                        <div className="flex items-center gap-2 min-w-0">
                                            <DocumentIcon className="w-4 h-4 text-brand-500 shrink-0" />
                                            <span className="text-[12px] font-semibold text-slate-700 dark:text-slate-300 truncate">{file.name}</span>
                                        </div>
                                        <button type="button" onClick={() => removeFile(idx)} className="text-slate-400 hover:text-red-500 transition-colors">
                                            <XMarkIcon className="w-4 h-4" />
                                        </button>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                </section>

                {/* ── Attendance ── */}
                <section className="bg-white dark:bg-[#161b27] rounded-2xl border border-slate-100 dark:border-slate-800 shadow-sm p-6">
                    <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-4">Board Attendance</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {meeting.attendees.map((a, i) => (
                            <div key={a.id} className="flex flex-col p-4 rounded-xl bg-slate-50/50 dark:bg-white/5 border border-slate-100 dark:border-slate-800 gap-3">
                                <div className="flex items-center gap-2">
                                    <div className="w-8 h-8 rounded-full bg-slate-200 dark:bg-slate-700 flex items-center justify-center text-xs font-bold text-slate-600 dark:text-slate-400">
                                        {a.user_name.charAt(0)}
                                    </div>
                                    <div className="min-w-0 flex-1">
                                        <p className="text-[13px] font-bold text-slate-900 dark:text-white truncate">{a.user_name}</p>
                                        <p className="text-[11px] text-slate-500 truncate">{a.designation || 'Director'}</p>
                                    </div>
                                </div>
                                <div className="flex flex-col gap-2">
                                    <select
                                        value={form.attendees[i]?.attendance_status || 'Present'}
                                        onChange={(e) => updateAttendee(i, 'attendance_status', e.target.value)}
                                        className={`${inputClass} py-2`}
                                    >
                                        <option value="Present">Present</option>
                                        <option value="Absent">Absent</option>
                                        <option value="Excused">Excused</option>
                                    </select>
                                    <input 
                                        placeholder="Confidential Remark" 
                                        value={form.attendees[i]?.remarks || ''} 
                                        onChange={(e) => updateAttendee(i, 'remarks', e.target.value)} 
                                        className={`${inputClass} py-2`} 
                                    />
                                </div>
                            </div>
                        ))}
                    </div>
                </section>

                {/* ── Mandates (Tasks) ── */}
                <section className="bg-white dark:bg-[#161b27] rounded-2xl border border-slate-100 dark:border-slate-800 shadow-sm p-6">
                    <div className="flex items-center justify-between mb-6">
                        <h3 className="text-lg font-bold text-slate-900 dark:text-white">Action Mandates</h3>
                        <button type="button" onClick={addTask} className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-brand-50 dark:bg-brand-500/10 text-brand-600 dark:text-brand-400 text-xs font-bold hover:bg-brand-100 transition-colors">
                            <PlusIcon className="w-4 h-4" /> Add Mandate
                        </button>
                    </div>
                    <div className="space-y-3">
                        {form.tasks.map((t, i) => (
                            <div key={i} className="flex flex-col gap-4 p-5 rounded-2xl bg-slate-50/50 dark:bg-white/5 border border-slate-100 dark:border-slate-800">
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    <div className="flex-1">
                                        <label className={labelClass}>Resolution Action Item</label>
                                        <input placeholder="What needs to be done?" value={t.title} onChange={(e) => updateTask(i, 'title', e.target.value)} className={inputClass} />
                                    </div>
                                    <div className="flex-1">
                                        <label className={labelClass}>Responsible Director</label>
                                        <select
                                            value={(t as any)._manualMode ? '__OTHER__' : (t.responsible_person || '')}
                                            onChange={(e) => {
                                                const val = e.target.value;
                                                if (val === '__OTHER__') {
                                                    setForm(p => {
                                                        const newTasks = [...p.tasks];
                                                        (newTasks[i] as any)._manualMode = true;
                                                        newTasks[i].responsible_person = '';
                                                        newTasks[i].responsible_email = '';
                                                        return { ...p, tasks: newTasks };
                                                    });
                                                } else {
                                                    const a = meeting.attendees.find(x => x.user_name === val);
                                                    setForm(p => {
                                                        const newTasks = [...p.tasks];
                                                        (newTasks[i] as any)._manualMode = false;
                                                        newTasks[i].responsible_person = a?.user_name || '';
                                                        newTasks[i].responsible_email = a?.email || '';
                                                        return { ...p, tasks: newTasks };
                                                    });
                                                }
                                            }}
                                            className={inputClass}
                                        >
                                            <option value="">-- Select Assignee --</option>
                                            {meeting.attendees.map(a => (
                                                <option key={a.id} value={a.user_name}>{a.user_name} ({a.designation || 'Reviewer'})</option>
                                            ))}
                                            <option value="__OTHER__">Other / External</option>
                                        </select>
                                    </div>
                                </div>

                                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                    <div className="md:col-span-2">
                                        <label className={labelClass}>Execution Deadline</label>
                                        <input type="date" value={t.deadline || ''} onChange={(e) => updateTask(i, 'deadline', e.target.value)} className={inputClass} />
                                    </div>
                                    <div className="flex items-end">
                                        <button type="button" onClick={() => removeTask(i)} className="w-full flex items-center justify-center gap-1.5 px-4 py-2.5 rounded-xl text-red-500 text-xs font-bold bg-red-50 dark:bg-red-500/10 hover:bg-red-100 transition-colors">
                                            <TrashIcon className="w-4 h-4" /> Remove
                                        </button>
                                    </div>
                                </div>
                            </div>
                        ))}
                        {form.tasks.length === 0 && <p className="text-slate-400 text-sm italic py-4 text-center">No compliance mandates assigned.</p>}
                    </div>
                </section>

                {/* ── Submit ── */}
                <div className="flex justify-center pt-8 pb-16">
                    <button
                        type="submit"
                        disabled={loading}
                        className="relative group overflow-hidden px-10 py-3.5 rounded-2xl bg-brand-600 text-white font-bold shadow-xl shadow-brand-500/20 transition-all hover:shadow-brand-500/40 hover:-translate-y-0.5 active:scale-[0.98] disabled:opacity-50 flex items-center justify-center gap-3"
                    >
                        {/* Interactive Gradient Overlay */}
                        <div className="absolute inset-0 bg-gradient-to-r from-brand-600 via-indigo-600 to-brand-600 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                        
                        <div className="relative flex items-center gap-3">
                            {loading ? (
                                <>
                                    <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                                    <span className="tracking-wide text-[14px]">Archiving Resolution...</span>
                                </>
                            ) : (
                                <>
                                    <ShieldCheckIcon className="w-5 h-5" />
                                    <span className="tracking-wide text-[14px]">Pass Resolution & Notify Directors</span>
                                </>
                            )}
                        </div>
                    </button>
                </div>

            </form>
        </div>
    );
}

function ShieldCheckIcon(props: any) {
    return (
        <svg fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" {...props}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75 11.25 15 15 9.75m-3-7.036A11.959 11.959 0 0 1 3.598 6 11.99 11.99 0 0 0 3 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285Z" />
        </svg>
    )
}
