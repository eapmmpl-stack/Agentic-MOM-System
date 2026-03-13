/* Shared TypeScript types (mirrors backend Pydantic schemas). */

export type UserRole = 'CEO' | 'Manager' | 'HR' | 'Employee';
export type TaskStatus = 'Pending' | 'In Progress' | 'Completed';
export type AttendanceStatus = 'Present' | 'Absent' | 'Excused';
export type MeetingStatus = 'Scheduled' | 'Rescheduled' | 'Cancelled' | 'Completed' | 'Processing';

export interface User {
  id: number;
  name: string;
  email: string;
  role: UserRole;
  phone?: string;
  is_active: boolean;
  created_at: string;
}

export interface Attendee {
  id: number;
  meeting_id: number;
  user_name: string;
  email?: string;
  designation?: string;
  whatsapp_number?: string;
  remarks?: string;
  attendance_status: AttendanceStatus;
}

export interface AgendaItem {
  id: number;
  meeting_id: number;
  topic: string;
  description?: string;
}

export interface Discussion {
  id: number;
  meeting_id: number;
  summary_text: string;
}

export interface Task {
  id: number;
  meeting_id: number;
  title: string;
  description?: string;
  responsible_person?: string;
  responsible_email?: string;
  deadline?: string;
  status: TaskStatus;
  created_at: string;
}

export interface TaskHistory {
  id: number;
  task_id: number;
  previous_status?: TaskStatus;
  new_status: TaskStatus;
  changed_at: string;
  changed_by?: string;
}

export interface NextMeeting {
  id: number;
  meeting_id: number;
  next_date?: string;
  next_time?: string;
}

export interface Meeting {
  id: number;
  title: string;
  organization?: string;
  meeting_type?: string;
  meeting_mode?: string;
  date?: string;
  time?: string;
  venue?: string;
  hosted_by?: string;
  file_path?: string;
  created_by?: number;
  created_at: string;
  attendees: Attendee[];
  agenda_items: AgendaItem[];
  discussion?: Discussion;
  tasks: Task[];
  next_meeting?: NextMeeting;
  supporting_documents?: any[];
  status: MeetingStatus;
  recording_link?: string;
  pdf_link?: string;
  ai_summary_link?: string;
  drive_transcript_id?: string;
  drive_logs_link?: string;
}

export interface MeetingListItem {
  id: number;
  title: string;
  organization?: string;
  date?: string;
  time?: string;
  venue?: string;
  created_at: string;
  task_count: number;
  status: MeetingStatus;
  recording_link?: string;
  pdf_link?: string;
}

export interface Notification {
  id: number;
  user_id?: number;
  recipient_email?: string;
  message: string;
  notification_type: string;
  is_read: boolean;
  sent_at: string;
}

export interface DashboardStats {
  total_meetings: number;
  total_tasks: number;
  pending_tasks: number;
  in_progress_tasks: number;
  completed_tasks: number;
  overdue_tasks: number;
  upcoming_meetings: number;
  total_users: number;
}

export interface TaskStatusDistribution {
  status: string;
  count: number;
}

export interface MeetingTrend {
  month: string;
  count: number;
}

export interface AnalyticsData {
  stats: DashboardStats;
  task_distribution: TaskStatusDistribution[];
  meeting_trends: MeetingTrend[];
  recent_meetings: MeetingListItem[];
  overdue_tasks: Task[];
  nearest_upcoming_meeting?: Meeting;
  last_meeting?: Meeting;
}

export interface LoginPayload {
  username: string;  // OAuth2 form uses "username" for email
  password: string;
}

export interface RegisterPayload {
  name: string;
  email: string;
  password: string;
  role: UserRole;
  phone?: string;
}

export interface MeetingFormData {
  title: string;
  organization?: string;
  meeting_type?: string;
  meeting_mode?: string;
  date?: string;
  time?: string;
  venue?: string;
  hosted_by?: string;
  attendees: {
    user_name: string;
    email?: string;
    designation?: string;
    whatsapp_number?: string;
    remarks?: string;
    attendance_status: AttendanceStatus;
  }[];
  agenda_items: { topic: string; description?: string }[];
  discussion_summary?: string;
  tasks: {
    title: string;
    description?: string;
    responsible_person?: string;
    responsible_email?: string;
    deadline?: string;
    status: TaskStatus;
  }[];
  next_meeting?: { next_date?: string; next_time?: string };
}

export interface AttendeeStatusUpdate {
  id: number;
  attendance_status: AttendanceStatus;
  remarks?: string;
}

export interface MeetingMOMUpdatePayload {
  attendees: AttendeeStatusUpdate[];
  discussion_summary?: string;
  tasks: {
    title: string;
    description?: string;
    responsible_person?: string;
    responsible_email?: string;
    deadline?: string;
    status: TaskStatus;
  }[];
  next_meeting?: { next_date?: string; next_time?: string };
}
