import { useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import toast from 'react-hot-toast';
import {
  TrashIcon,
  CalendarDaysIcon,
  MapPinIcon,
  ClipboardDocumentListIcon,
  BuildingOfficeIcon,
  ArrowRightIcon,
  PlusIcon,
  ArrowUpTrayIcon,
} from '@heroicons/react/24/outline';
import api from '../api';
import type { MeetingListItem } from '../types';

export default function MeetingsPage() {
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState<'Upcoming' | 'Completed' | 'Cancelled'>('Upcoming');

  const { data: meetings = [], isLoading } = useQuery<MeetingListItem[]>({
    queryKey: ['meetings'],
    queryFn: async () => (await api.get('/meetings/')).data,
  });

  const handleDelete = async (id: number, title: string) => {
    if (!window.confirm(`Delete meeting "${title}"?\nThis action cannot be undone.`)) return;
    try {
      await api.delete(`/meetings/${id}`);
      toast.success('Meeting deleted');
      queryClient.invalidateQueries({ queryKey: ['meetings'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
    } catch {
      toast.error('Failed to delete meeting');
    }
  };

  const upcomingMeetings = meetings.filter(m => m.status === 'Scheduled' || m.status === 'Rescheduled' || m.status === 'Processing');
  const completedMeetings = meetings.filter(m => m.status === 'Completed');
  const cancelledMeetings = meetings.filter(m => m.status === 'Cancelled');

  const displayedMeetings =
    activeTab === 'Completed' ? completedMeetings :
      activeTab === 'Cancelled' ? cancelledMeetings : upcomingMeetings;

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'Completed': return 'text-green-600 bg-green-50 dark:bg-green-500/10 dark:text-green-400 border-green-100 dark:border-green-500/20';
      case 'Processing': return 'text-brand-600 bg-brand-50 dark:bg-brand-500/10 dark:text-brand-400 border-brand-100 dark:border-brand-500/20 animate-pulse';
      case 'Rescheduled': return 'text-amber-600 bg-amber-50 dark:bg-amber-500/10 dark:text-amber-400 border-amber-100 dark:border-amber-100/20';
      case 'Cancelled': return 'text-red-600 bg-red-50 dark:bg-red-500/10 dark:text-red-400 border-red-100 dark:border-red-500/20';
      default: return 'text-brand-600 bg-brand-50 dark:bg-brand-500/10 dark:text-brand-400 border-brand-100 dark:border-brand-500/20';
    }
  };

  return (
    <div className="space-y-5 max-w-[1200px] mx-auto">

      {/* ── Page Header ── */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-extrabold text-slate-900 dark:text-white">All Meetings</h2>
          <p className="text-sm text-slate-400 mt-0.5">{displayedMeetings.length} meeting{displayedMeetings.length !== 1 ? 's' : ''} in {activeTab}</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Link
            to="/upload"
            className="inline-flex items-center gap-2 px-4 py-2.5 text-[13px] font-semibold rounded-xl bg-slate-100 dark:bg-white/5 text-slate-700 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-white/10 transition-all"
          >
            <ArrowUpTrayIcon className="w-4 h-4" />
            Upload MOM
          </Link>
          <Link
            to="/schedule-meeting"
            className="inline-flex items-center gap-2 px-4 py-2.5 text-[13px] font-semibold rounded-xl bg-brand-50 dark:bg-brand-500/10 text-brand-700 dark:text-brand-400 hover:bg-brand-100 dark:hover:bg-brand-500/20 transition-all border border-brand-100 dark:border-brand-500/20"
          >
            <CalendarDaysIcon className="w-4 h-4" />
            Schedule Meeting
          </Link>
          <Link
            to="/create-mom"
            className="inline-flex items-center gap-2 px-4 py-2.5 text-[13px] font-bold rounded-xl bg-brand-600 text-white hover:bg-brand-700 shadow-md shadow-brand-200 dark:shadow-brand-900/40 transition-all active:scale-[0.98]"
          >
            <PlusIcon className="w-4 h-4" />
            Create MOM
          </Link>
        </div>
      </div>

      {/* ── Tabs ── */}
      <div className="flex bg-slate-100 dark:bg-slate-800 p-1 rounded-xl w-fit">
        <button
          onClick={() => setActiveTab('Upcoming')}
          className={`px-5 py-2 text-[13px] font-bold rounded-lg transition-colors ${activeTab === 'Upcoming'
            ? 'bg-white dark:bg-[#161b27] text-brand-600 dark:text-brand-400 shadow-sm'
            : 'text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200'
            }`}
        >
          Upcoming ({upcomingMeetings.length})
        </button>
        <button
          onClick={() => setActiveTab('Completed')}
          className={`px-5 py-2 text-[13px] font-bold rounded-lg transition-colors ${activeTab === 'Completed'
            ? 'bg-white dark:bg-[#161b27] text-brand-600 dark:text-brand-400 shadow-sm'
            : 'text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200'
            }`}
        >
          Completed ({completedMeetings.length})
        </button>
        <button
          onClick={() => setActiveTab('Cancelled')}
          className={`px-5 py-2 text-[13px] font-bold rounded-lg transition-colors ${activeTab === 'Cancelled'
            ? 'bg-white dark:bg-[#161b27] text-brand-600 dark:text-brand-400 shadow-sm'
            : 'text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200'
            }`}
        >
          Cancelled ({cancelledMeetings.length})
        </button>
      </div>

      {/* ── Content ── */}
      {isLoading ? (
        <div className="flex flex-col items-center justify-center h-52 gap-3">
          <div className="w-7 h-7 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
          <p className="text-sm text-slate-400">Loading meetings…</p>
        </div>
      ) : displayedMeetings.length === 0 ? (
        <div className="flex flex-col items-center justify-center h-52 gap-3 bg-white dark:bg-[#161b27] rounded-2xl border border-dashed border-slate-200 dark:border-slate-700">
          <CalendarDaysIcon className="w-10 h-10 text-slate-300 dark:text-slate-600" />
          <p className="text-sm font-medium text-slate-400">No {activeTab.toLowerCase()} meetings found.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-3">
          {displayedMeetings.map((m) => (
            <div
              key={m.id}
              className="group bg-white dark:bg-[#161b27] rounded-2xl border border-slate-100 dark:border-slate-800 px-5 py-4 shadow-sm hover:shadow-md hover:border-brand-200 dark:hover:border-brand-500/30 transition-all duration-200"
            >
              <div className="flex items-start justify-between gap-4">

                {/* Left – Info */}
                <div className="flex items-start gap-4 min-w-0">
                  {/* Status Indicator Bar */}
                  <div className={`w-1 self-stretch rounded-full ${m.status === 'Completed' ? 'bg-green-500' :
                      m.status === 'Cancelled' ? 'bg-red-500' :
                        m.status === 'Rescheduled' ? 'bg-amber-500' :
                          'bg-brand-500'
                    }`} />

                  {/* Icon */}
                  <div className="w-11 h-11 rounded-xl bg-slate-50 dark:bg-white/5 flex items-center justify-center shrink-0">
                    <CalendarDaysIcon className="w-5 h-5 text-slate-400" />
                  </div>

                  {/* Text */}
                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <Link
                        to={`/meetings/${m.id}`}
                        className="text-[15px] font-bold text-slate-900 dark:text-white hover:text-brand-600 dark:hover:text-brand-400 transition-colors line-clamp-1"
                      >
                        {m.title}
                      </Link>
                      <span className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded-md border ${getStatusColor(m.status)}`}>
                        {m.status}
                      </span>
                    </div>

                    {/* Meta row */}
                    <div className="flex flex-wrap items-center gap-x-4 gap-y-1 mt-1.5">
                      {m.organization && (
                        <span className="flex items-center gap-1 text-[12px] text-slate-500 dark:text-slate-400">
                          <BuildingOfficeIcon className="w-3.5 h-3.5 shrink-0" />
                          {m.organization}
                        </span>
                      )}
                      {m.date && (
                        <span className="flex items-center gap-1 text-[12px] text-slate-500 dark:text-slate-400">
                          <CalendarDaysIcon className="w-3.5 h-3.5 shrink-0" />
                          {m.date}
                        </span>
                      )}
                      {m.venue && (
                        <span className="flex items-center gap-1 text-[12px] text-slate-500 dark:text-slate-400">
                          <MapPinIcon className="w-3.5 h-3.5 shrink-0" />
                          {m.venue}
                        </span>
                      )}
                    </div>
                  </div>
                </div>

                {/* Right – Badges + Actions */}
                <div className="flex items-center gap-3 shrink-0">
                  {/* Task badge */}
                  <span className="hidden sm:inline-flex items-center gap-1.5 text-[12px] font-semibold bg-brand-50 dark:bg-brand-500/15 text-brand-700 dark:text-brand-400 px-3 py-1.5 rounded-xl border border-brand-100 dark:border-brand-500/20">
                    <ClipboardDocumentListIcon className="w-3.5 h-3.5" />
                    {m.task_count} {m.task_count === 1 ? 'task' : 'tasks'}
                  </span>

                  {/* View button */}
                  <Link
                    to={`/meetings/${m.id}`}
                    className="inline-flex items-center gap-1.5 text-[12px] font-semibold text-brand-600 dark:text-brand-400 hover:text-brand-800 dark:hover:text-brand-300 transition-colors"
                  >
                    View <ArrowRightIcon className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
                  </Link>

                  {/* Delete */}
                  <button
                    onClick={() => handleDelete(m.id, m.title)}
                    className="w-8 h-8 flex items-center justify-center rounded-xl text-slate-400 hover:bg-red-50 hover:text-red-500 dark:hover:bg-red-500/10 dark:hover:text-red-400 transition-all"
                    title="Delete meeting"
                  >
                    <TrashIcon className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
