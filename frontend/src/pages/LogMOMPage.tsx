import { useState, useEffect, useRef } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import toast from 'react-hot-toast';
import { PlusIcon, TrashIcon } from '@heroicons/react/24/outline';
import api from '../api';
import type { Meeting, MeetingMOMUpdatePayload, AttendanceStatus, TaskStatus } from '../types';

export default function LogMOMPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const { data: meeting, isLoading: meetingLoading, isError: meetingError, error } = useQuery<Meeting>({
    queryKey: ['meetings', id],
    queryFn: async () => (await api.get(`/meetings/${id}`)).data,
    enabled: !!id,
  });

  const [form, setForm] = useState<MeetingMOMUpdatePayload>({
    attendees: [],
    discussion_summary: '',
    tasks: [],
    next_meeting: { next_date: '', next_time: '' },
  });
  const [loading, setLoading] = useState(false);
  const [editingDiscussion, setEditingDiscussion] = useState(false);
  const discussionTextareaRef = useRef<HTMLTextAreaElement | null>(null);

  const normalizeText = (value: unknown) => {
    if (typeof value === 'string') return value;
    if (value === null || value === undefined) return '';
    return String(value);
  };

  const normalizeObjectArray = (value: unknown): any[] => {
    if (!Array.isArray(value)) return [];
    return value.filter((item) => item && typeof item === 'object');
  };

  useEffect(() => {
    if (meeting) {
      const attendees = normalizeObjectArray(meeting.attendees);
      const tasks = normalizeObjectArray(meeting.tasks);
      const summaryText = normalizeText(meeting.discussion?.summary_text);

      setForm({
        attendees: attendees.map(a => ({
          id: a.id,
          attendance_status: a.attendance_status || 'Present',
          remarks: a.remarks || '',
        })),
        discussion_summary: summaryText,
        tasks: tasks.map(t => ({
          title: t.title,
          description: t.description || '',
          responsible_person: t.responsible_person || '',
          responsible_email: t.responsible_email || '',
          deadline: t.deadline || '',
          status: t.status,
          _manualMode: (t.responsible_person && !attendees.some(a => a.user_name === t.responsible_person)) as boolean,
        }) as any),
        next_meeting: {
          next_date: meeting.next_meeting?.next_date || '',
          next_time: meeting.next_meeting?.next_time || '',
        },
      });
      setEditingDiscussion(!summaryText.trim());
    }
  }, [meeting]);

  const updateField = (field: string, value: any) => setForm((p) => ({ ...p, [field]: value }));

  const autoResizeDiscussion = (target?: HTMLTextAreaElement | null) => {
    const el = target || discussionTextareaRef.current;
    if (!el) return;
    el.style.height = 'auto';
    el.style.height = `${Math.max(el.scrollHeight, 180)}px`;
  };

  const formatDiscussionHtml = (text: string) => {
    return (text || '')
      .replace(/\*\*\s*(.*?)\s*\*\*/gs, '<b class="font-extrabold text-slate-900 dark:text-white">$1</b>')
      .replace(/^###\s*(.*)$/gm, '<h3 class="text-md font-extrabold text-brand-600 dark:text-brand-400 mt-4 mb-2 uppercase tracking-wide">$1</h3>')
      .replace(/^##\s*(.*)$/gm, '<h2 class="text-lg font-extrabold text-brand-700 dark:text-brand-300 mt-5 mb-2 uppercase tracking-tight">$1</h2>')
      .replace(/\n/g, '<br/>');
  };

  useEffect(() => {
    if (editingDiscussion) {
      autoResizeDiscussion();
    }
  }, [editingDiscussion, form.discussion_summary]);

  if (meetingLoading) {
    return <div className="p-8 text-center text-gray-500">Loading meeting details...</div>;
  }

  if (meetingError) {
    return (
      <div className="p-8 text-center text-red-500">
        Failed to load meeting details. {(error as any)?.message ? `(${(error as any).message})` : ''}
      </div>
    );
  }

  if (!meeting) {
    return <div className="p-8 text-center text-gray-500">Meeting details not found.</div>;
  }

  const safeAttendees = normalizeObjectArray(meeting.attendees);

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
      await api.post(`/meetings/${id}/mom`, payload);
      toast.success('MOM saved and notifications sent successfully!');
      navigate(`/meetings/${id}`);
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      if (typeof detail === 'string') {
        toast.error(detail);
      } else if (Array.isArray(detail)) {
        toast.error(detail.map((d: any) => d.msg || JSON.stringify(d)).join('\n'));
      } else {
        toast.error('Failed to record MOM');
      }
    } finally {
      setLoading(false);
    }
  };

  const inputClass =
    'w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-brand-500 focus:border-transparent';
  const labelClass = 'block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1';

  return (
    <div className="max-w-4xl mx-auto">
      <div className="flex flex-col gap-1 mb-6">
        <button 
          onClick={() => navigate(`/meetings/${id}`)} 
          className="inline-flex items-center gap-1.5 text-xs font-bold text-slate-400 hover:text-brand-500 transition-colors mb-2 w-fit"
        >
          <PlusIcon className="w-3 h-3 rotate-45" /> Back to Details
        </button>
        <h2 className="text-xl font-bold text-gray-900 dark:text-white">Record MOM: {meeting.title}</h2>
        <p className="text-gray-500 text-sm">
          Date: {meeting.date} | Venue: {meeting.venue || 'TBD'}
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Attendees */}
        <section className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Mark Attendance</h3>
          <p className="text-sm text-gray-500 mb-4 italic">Select who attended the meeting.</p>
          {safeAttendees.map((a, i) => (
            <div key={a.id} className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-3 items-center">
              <div>
                <span className="font-medium text-gray-900 dark:text-white">{a.user_name}</span>
                {a.email && <span className="ml-2 text-sm text-gray-500">({a.email})</span>}
              </div>
              <div className="flex gap-2">
                <select value={form.attendees[i]?.attendance_status || 'Present'} onChange={(e) => updateAttendee(i, 'attendance_status', e.target.value)} className={inputClass}>
                  <option value="Present">Present</option>
                  <option value="Absent">Absent</option>
                  <option value="Excused">Excused</option>
                </select>
                <input 
                  placeholder="Personal Remark" 
                  value={form.attendees[i]?.remarks || ''} 
                  onChange={(e) => updateAttendee(i, 'remarks', e.target.value)} 
                  className={inputClass} 
                />
              </div>
            </div>
          ))}
        </section>

        {/* Discussion */}
        <section className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-center justify-between mb-4 gap-3">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Discussion Summary</h3>
            <button
              type="button"
              onClick={() => setEditingDiscussion((prev) => !prev)}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-brand-50 dark:bg-brand-500/10 text-brand-600 dark:text-brand-400 text-xs font-bold hover:bg-brand-100 transition-colors"
            >
              {editingDiscussion ? 'Preview Structured' : 'Edit Raw Text'}
            </button>
          </div>

          {editingDiscussion ? (
            <textarea
              ref={discussionTextareaRef}
              rows={1}
              value={form.discussion_summary}
              onChange={(e) => {
                updateField('discussion_summary', e.target.value);
                autoResizeDiscussion(e.target);
              }}
              className={`${inputClass} resize-none overflow-hidden`}
              style={{ minHeight: '180px' }}
              placeholder="Summarize the key discussion points from the meeting..."
            />
          ) : (
            <div
              className="text-[13px] text-slate-700 dark:text-slate-300 leading-relaxed space-y-2 bg-slate-50 dark:bg-white/5 p-4 rounded-xl border border-slate-100 dark:border-slate-800 min-h-[180px]"
              dangerouslySetInnerHTML={{
                __html: normalizeText(form.discussion_summary).trim()
                  ? formatDiscussionHtml(normalizeText(form.discussion_summary))
                  : '<p class="text-sm text-slate-400 italic">No discussion summary recorded yet. Click Edit Raw Text to add one.</p>',
              }}
            />
          )}
        </section>

        {/* Tasks */}
        <section className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Action Items / Tasks</h3>
            <button type="button" onClick={addTask} className="flex items-center gap-1 text-sm text-brand-600 hover:underline">
              <PlusIcon className="w-4 h-4" /> Add Task
            </button>
          </div>
          {form.tasks.map((t, i) => (
            <div key={i} className="grid grid-cols-1 md:grid-cols-6 gap-3 mb-3 items-start p-3 bg-gray-50 dark:bg-gray-800/50 rounded-lg">
              <input placeholder="Task title" value={t.title} onChange={(e) => updateTask(i, 'title', e.target.value)} className={inputClass} />

              <div className="md:col-span-2 flex flex-col gap-2">
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
                    } else if (val) {
                      const a = safeAttendees.find(x => x.user_name === val);
                      setForm(p => {
                        const newTasks = [...p.tasks];
                        (newTasks[i] as any)._manualMode = false;
                        newTasks[i].responsible_person = a?.user_name || '';
                        newTasks[i].responsible_email = a?.email || '';
                        return { ...p, tasks: newTasks };
                      });
                    } else {
                      setForm(p => {
                        const newTasks = [...p.tasks];
                        (newTasks[i] as any)._manualMode = false;
                        newTasks[i].responsible_person = '';
                        newTasks[i].responsible_email = '';
                        return { ...p, tasks: newTasks };
                      });
                    }
                  }}
                  className={inputClass}
                >
                  <option value="">-- Select Assignee --</option>
                  {safeAttendees.map(a => (
                    <option key={a.id} value={a.user_name}>{a.user_name} {a.email ? `(${a.email})` : ''}</option>
                  ))}
                  <option value="__OTHER__">Other / Manual</option>
                </select>

                {(t as any)._manualMode && (
                  <div className="grid grid-cols-2 gap-2">
                    <input placeholder="Name" value={t.responsible_person || ''} onChange={(e) => updateTask(i, 'responsible_person', e.target.value)} className={inputClass} />
                    <input placeholder="Email" value={t.responsible_email || ''} onChange={(e) => updateTask(i, 'responsible_email', e.target.value)} className={inputClass} />
                  </div>
                )}
              </div>

              <input type="date" value={t.deadline || ''} onChange={(e) => updateTask(i, 'deadline', e.target.value)} className={inputClass} />
              <select value={t.status} onChange={(e) => updateTask(i, 'status', e.target.value)} className={inputClass}>
                <option value="Pending">Pending</option>
                <option value="In Progress">In Progress</option>
                <option value="Completed">Completed</option>
              </select>
              <button type="button" onClick={() => removeTask(i)} className="text-red-500 hover:text-red-700 text-sm flex items-center justify-center gap-1 mb-2">
                <TrashIcon className="w-4 h-4" /> Remove
              </button>
            </div>
          ))}
          {form.tasks.length === 0 && <p className="text-gray-500 text-sm italic">No tasks assigned yet.</p>}
        </section>

        {/* Next Meeting */}
        <section className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Schedule Next Meeting</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className={labelClass}>Date</label>
              <input
                type="date"
                value={form.next_meeting?.next_date || ''}
                onChange={(e) =>
                  setForm((p) => ({
                    ...p,
                    next_meeting: {
                      ...(p.next_meeting || { next_date: '', next_time: '' }),
                      next_date: e.target.value,
                    },
                  }))
                }
                className={inputClass}
              />
            </div>
            <div>
              <label className={labelClass}>Time</label>
              <input
                type="time"
                value={form.next_meeting?.next_time || ''}
                onChange={(e) =>
                  setForm((p) => ({
                    ...p,
                    next_meeting: {
                      ...(p.next_meeting || { next_date: '', next_time: '' }),
                      next_time: e.target.value,
                    },
                  }))
                }
                className={inputClass}
              />
            </div>
          </div>
        </section>

        <button
          type="submit"
          disabled={loading}
          className="w-full py-3 rounded-lg bg-green-600 hover:bg-green-700 text-white font-bold shadow-lg shadow-green-200 dark:shadow-green-900/20 transition-all active:scale-[0.98] disabled:opacity-50"
        >
          {loading ? 'Finalizing...' : '🚀 Save & Finalize MOM'}
        </button>
      </form>
    </div>
  );
}
