import { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import toast from 'react-hot-toast';
import { PlusIcon, TrashIcon } from '@heroicons/react/24/outline';
import api from '../api';
import type { MeetingFormData, AttendanceStatus } from '../types';

const emptyForm: MeetingFormData = {
  title: '',
  organization: '',
  meeting_type: '',
  meeting_mode: 'Online',
  date: '',
  time: '',
  venue: '',
  hosted_by: '',
  attendees: [],
  agenda_items: [],
  discussion_summary: '',
  tasks: [],
};

const normalizeMeetingType = (meetingType?: string) => {
  const value = String(meetingType || '').trim().toLowerCase();
  if (!value || value === 'regular' || value === 'regular meeting') return '';
  if (value === 'br' || value.includes('board resolution')) return 'Board Resolution';
  if (value.includes('committee')) return 'Committee Meeting';
  if (value.includes('annual general')) return 'Annual General Meeting';
  return meetingType || '';
};

export default function ScheduleMeetingPage() {
  const [form, setForm] = useState<MeetingFormData>({ ...emptyForm });
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const routeState = location.state as {
    prefill?: Partial<MeetingFormData>;
    rescheduleContext?: { isRescheduled?: boolean };
  } | null;
  const isRescheduleFlow = Boolean(routeState?.rescheduleContext?.isRescheduled);

  useEffect(() => {
    const state = location.state as { prefill?: Partial<MeetingFormData> } | null;
    const prefill = state?.prefill;
    if (!prefill) return;

    setForm({
      ...emptyForm,
      ...prefill,
      meeting_type: normalizeMeetingType(prefill.meeting_type),
      meeting_mode: prefill.meeting_mode === 'Offline' ? 'Offline' : 'Online',
      attendees: prefill.attendees ?? [],
      agenda_items: prefill.agenda_items ?? [],
      tasks: prefill.tasks ?? [],
    });
  }, [location.state]);

  // Load branding config for autofill
  useEffect(() => {
    api.get('/branding/').then(({ data }) => {
      if (data.client_name) {
        setForm(prev => (
          prev.organization && prev.organization.trim() !== ''
            ? prev
            : { ...prev, organization: data.client_name }
        ));
      }
    }).catch(err => console.error('Failed to load branding:', err));
  }, []);

  const updateField = (field: string, value: any) => setForm((p) => ({ ...p, [field]: value }));

  // Attendees
  const addAttendee = () =>
    setForm((p) => ({
      ...p,
      attendees: [...p.attendees, { user_name: '', email: '', designation: '', whatsapp_number: '', remarks: '', attendance_status: 'Present' as AttendanceStatus }],
    }));
  const removeAttendee = (i: number) =>
    setForm((p) => ({ ...p, attendees: p.attendees.filter((_, idx) => idx !== i) }));
  const updateAttendee = (i: number, field: string, value: string) =>
    setForm((p) => ({
      ...p,
      attendees: p.attendees.map((a, idx) => (idx === i ? { ...a, [field]: value } : a)),
    }));

  // Agenda
  const addAgenda = () =>
    setForm((p) => ({ ...p, agenda_items: [...p.agenda_items, { topic: '', description: '' }] }));
  const removeAgenda = (i: number) =>
    setForm((p) => ({ ...p, agenda_items: p.agenda_items.filter((_, idx) => idx !== i) }));
  const updateAgenda = (i: number, field: string, value: string) =>
    setForm((p) => ({
      ...p,
      agenda_items: p.agenda_items.map((a, idx) => (idx === i ? { ...a, [field]: value } : a)),
    }));

  const handleFormKeyDown = (e: React.KeyboardEvent<HTMLFormElement>) => {
    if (e.key !== 'Enter') return;

    const target = e.target as HTMLElement;
    const isTextArea = target instanceof HTMLTextAreaElement;
    const isSubmitButton = target instanceof HTMLButtonElement && target.type === 'submit';

    if (!isTextArea && !isSubmitButton) {
      e.preventDefault();
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.title.trim()) {
      toast.error('Meeting title is required');
      return;
    }
    setLoading(true);
    try {
      const payload = {
        ...form,
        status: isRescheduleFlow ? 'Rescheduled' : 'Scheduled',
        date: form.date && form.date.trim() !== '' ? form.date : null,
        time: form.time && form.time.trim() !== '' ? form.time : null,
        attendees: form.attendees.map((a) => ({
          ...a,
          email: a.email && a.email.trim() !== '' ? a.email : null,
        }))
      };
      const isBR = form.meeting_type?.toLowerCase().includes('board resolution') || form.meeting_type?.toLowerCase() === 'br';
      const endpoint = isBR ? '/br/' : '/meetings/';

      const { data } = await api.post(endpoint, payload);
      toast.success(`${isBR ? 'Board Resolution' : 'Meeting'} ${isRescheduleFlow ? 'rescheduled' : 'scheduled'} successfully! Invitations sent.`);
      navigate(`${isBR ? '/br' : '/meetings'}/${data.id}`);
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      if (typeof detail === 'string') {
        toast.error(detail);
      } else if (Array.isArray(detail)) {
        toast.error(detail.map((d: any) => d.msg || JSON.stringify(d)).join('\n'));
      } else {
        toast.error('Failed to schedule meeting');
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
      <button 
        onClick={() => navigate('/')} 
        className="inline-flex items-center gap-1.5 text-xs font-bold text-slate-400 hover:text-brand-500 transition-colors mb-4 w-fit"
      >
        <PlusIcon className="w-3 h-3 rotate-45" /> Back to Dashboard
      </button>
      <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-6">Schedule New Meeting</h2>

      <form onSubmit={handleSubmit} onKeyDown={handleFormKeyDown} className="space-y-6">
        {/* Meeting Details */}
        <section className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Meeting Details</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className={labelClass}>Title *</label>
              <input required value={form.title} onChange={(e) => updateField('title', e.target.value)} className={inputClass} />
            </div>
            <div>
              <label className={labelClass}>Organization</label>
              <input value={form.organization} onChange={(e) => updateField('organization', e.target.value)} className={inputClass} />
            </div>
            <div>
              <label className={labelClass}>Meeting Type</label>
              <select value={form.meeting_type} onChange={(e) => updateField('meeting_type', e.target.value)} className={inputClass}>
                <option value="">Regular Meeting</option>
                <option value="Board Resolution">Board Resolution</option>
                <option value="Committee Meeting">Committee Meeting</option>
                <option value="Annual General Meeting">Annual General Meeting</option>
              </select>
            </div>
            <div>
              <label className={labelClass}>Meeting Mode</label>
              <select value={form.meeting_mode} onChange={(e) => updateField('meeting_mode', e.target.value)} className={inputClass}>
                <option value="Online">Online</option>
                <option value="Offline">Offline</option>
              </select>
            </div>
            <div>
              <label className={labelClass}>Venue / Platform</label>
              <input value={form.venue} onChange={(e) => updateField('venue', e.target.value)} placeholder={form.meeting_mode === 'Online' ? 'Google Meet link...' : 'Conference Hall...'} className={inputClass} />
            </div>
            <div>
              <label className={labelClass}>Date</label>
              <input type="date" value={form.date} onChange={(e) => updateField('date', e.target.value)} className={inputClass} />
            </div>
            <div>
              <label className={labelClass}>Time</label>
              <input type="time" value={form.time} onChange={(e) => updateField('time', e.target.value)} className={inputClass} />
            </div>
            <div>
              <label className={labelClass}>Hosted By</label>
              <input value={form.hosted_by} onChange={(e) => updateField('hosted_by', e.target.value)} className={inputClass} />
            </div>
          </div>
        </section>

        {/* Agenda */}
        <section className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Agenda</h3>
            <button type="button" onClick={addAgenda} className="flex items-center gap-1 text-sm text-brand-600 hover:underline">
              <PlusIcon className="w-4 h-4" /> Add
            </button>
          </div>
          {form.agenda_items.map((a, i) => (
            <div key={i} className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-3">
              <input placeholder="Topic" value={a.topic} onChange={(e) => updateAgenda(i, 'topic', e.target.value)} className={inputClass} />
              <input placeholder="Description" value={a.description || ''} onChange={(e) => updateAgenda(i, 'description', e.target.value)} className={inputClass} />
              <button type="button" onClick={() => removeAgenda(i)} className="text-red-500 hover:text-red-700 text-sm flex items-center gap-1">
                <TrashIcon className="w-4 h-4" /> Remove
              </button>
            </div>
          ))}
        </section>

        {/* Attendees */}
        <section className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Expected Attendees</h3>
            <button type="button" onClick={addAttendee} className="flex items-center gap-1 text-sm text-brand-600 hover:underline">
              <PlusIcon className="w-4 h-4" /> Add
            </button>
          </div>
          <p className="text-sm text-gray-500 mb-4 font-medium italic">
            Note: Filling out this form will schedule the meeting and send invitations to the attendees automatically.
          </p>
          {form.attendees.map((a, i) => (
            <div key={i} className="flex flex-col gap-3 mb-4 bg-gray-50 dark:bg-gray-800/50 p-4 rounded-lg">
              <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
                <input placeholder="Unique ID" value={a.unique_id || ''} onChange={(e) => updateAttendee(i, 'unique_id', e.target.value)} className={inputClass} />
                <input placeholder="Name *" value={a.user_name} onChange={(e) => updateAttendee(i, 'user_name', e.target.value)} className={inputClass} />
                <input placeholder="Email" value={a.email || ''} onChange={(e) => updateAttendee(i, 'email', e.target.value)} className={inputClass} />
                <input placeholder="Designation" value={a.designation || ''} onChange={(e) => updateAttendee(i, 'designation', e.target.value)} className={inputClass} />
                <input placeholder="WhatsApp Number" value={a.whatsapp_number || ''} onChange={(e) => updateAttendee(i, 'whatsapp_number', e.target.value)} className={inputClass} />
              </div>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
                <input placeholder="Remarks (Will be included in the schedule email)" value={a.remarks || ''} onChange={(e) => updateAttendee(i, 'remarks', e.target.value)} className={`md:col-span-3 ${inputClass}`} />
                <button type="button" onClick={() => removeAttendee(i)} className="text-red-500 hover:text-red-700 justify-end text-sm flex items-center justify-center gap-1">
                  <TrashIcon className="w-4 h-4" /> Remove Attendee
                </button>
              </div>
            </div>
          ))}
        </section>

        <button
          type="submit"
          disabled={loading}
          className="w-full py-3 rounded-lg bg-brand-600 hover:bg-brand-700 text-white font-medium transition disabled:opacity-50"
        >
          {loading ? 'Scheduling...' : 'Schedule & Send Invites'}
        </button>
      </form>
    </div>
  );
}
