"""Pydantic schemas for request/response validation."""

from datetime import datetime, date, time
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models.models import UserRole, AttendanceStatus, TaskStatus, NotificationType


# ── User Schemas ───────────────────────────────────────────────────────

class UserCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    password: str = Field(..., min_length=6)
    role: UserRole = UserRole.EMPLOYEE
    phone: Optional[str] = None


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[UserRole] = None
    phone: Optional[str] = None
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    role: UserRole
    phone: Optional[str]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: Optional[int] = None
    role: Optional[str] = None


# ── Attendee Schemas ───────────────────────────────────────────────────

class AttendeeCreate(BaseModel):
    user_name: str
    email: Optional[str] = None
    designation: Optional[str] = None
    whatsapp_number: Optional[str] = None
    remarks: Optional[str] = None
    attendance_status: AttendanceStatus = AttendanceStatus.PRESENT


class AttendeeStatusUpdate(BaseModel):
    id: int
    attendance_status: AttendanceStatus
    remarks: Optional[str] = None


class AttendeeResponse(BaseModel):
    id: int
    meeting_id: int
    user_name: str
    email: Optional[str]
    designation: Optional[str]
    whatsapp_number: Optional[str]
    remarks: Optional[str]
    attendance_status: AttendanceStatus

    class Config:
        from_attributes = True


# ── Agenda Schemas ─────────────────────────────────────────────────────

class AgendaItemCreate(BaseModel):
    topic: str
    description: Optional[str] = None


class AgendaItemResponse(BaseModel):
    id: int
    meeting_id: int
    topic: str
    description: Optional[str]

    class Config:
        from_attributes = True


# ── Discussion Schemas ─────────────────────────────────────────────────

class DiscussionCreate(BaseModel):
    summary_text: str


class DiscussionResponse(BaseModel):
    id: int
    meeting_id: int
    summary_text: str

    class Config:
        from_attributes = True


# ── Task Schemas ───────────────────────────────────────────────────────

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    responsible_person: Optional[str] = None
    responsible_email: Optional[str] = None
    deadline: Optional[date] = None
    status: TaskStatus = TaskStatus.PENDING



class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    responsible_person: Optional[str] = None
    responsible_email: Optional[str] = None
    deadline: Optional[date] = None
    status: Optional[TaskStatus] = None


class TaskResponse(BaseModel):
    id: int
    meeting_id: int
    title: str
    description: Optional[str]
    responsible_person: Optional[str]
    responsible_email: Optional[str]
    deadline: Optional[date]
    status: TaskStatus
    created_at: datetime

    class Config:
        from_attributes = True


class TaskHistoryResponse(BaseModel):
    id: int
    task_id: int
    previous_status: Optional[TaskStatus]
    new_status: TaskStatus
    changed_at: datetime
    changed_by: Optional[str]

    class Config:
        from_attributes = True


# ── Next Meeting Schemas ───────────────────────────────────────────────

class NextMeetingCreate(BaseModel):
    next_date: Optional[date] = None
    next_time: Optional[time] = None



class NextMeetingResponse(BaseModel):
    id: int
    meeting_id: int
    next_date: Optional[date]
    next_time: Optional[time]

    class Config:
        from_attributes = True


# ── File Schemas ───────────────────────────────────────────────────────

class FileResponse(BaseModel):
    id: int
    meeting_id: int
    file_path: str
    file_type: str
    uploaded_at: datetime

    class Config:
        from_attributes = True


# ── Meeting Schemas ────────────────────────────────────────────────────

class MeetingCreate(BaseModel):
    title: str
    organization: Optional[str] = "Botivate Services LLP"
    meeting_type: Optional[str] = None
    meeting_mode: Optional[str] = None
    date: date
    time: time
    venue: Optional[str] = None
    hosted_by: Optional[str] = None
    attendees: list[AttendeeCreate] = []
    agenda_items: list[AgendaItemCreate] = []
    discussion_summary: Optional[str] = None
    tasks: list[TaskCreate] = []
    next_meeting: Optional[NextMeetingCreate] = None
    status: Optional[str] = "Scheduled"


class MeetingMOMUpdate(BaseModel):
    attendees: list[AttendeeStatusUpdate] = []
    discussion_summary: Optional[str] = None
    tasks: list[TaskCreate] = []
    next_meeting: Optional[NextMeetingCreate] = None

class RescheduleMeeting(BaseModel):
    date: date
    time: time



class MeetingResponse(BaseModel):
    id: int
    title: str
    organization: Optional[str]
    meeting_type: Optional[str]
    meeting_mode: Optional[str]
    date: Optional[date]
    time: Optional[time]
    venue: Optional[str]
    hosted_by: Optional[str]
    file_path: Optional[str]
    pdf_link: Optional[str] = None
    drive_file_id: Optional[str] = None
    drive_folder_id: Optional[str] = None
    recording_link: Optional[str] = None
    drive_recording_id: Optional[str] = None
    drive_transcript_id: Optional[str] = None
    ai_summary_link: Optional[str] = None
    drive_logs_link: Optional[str] = None
    created_by: Optional[int]
    created_at: datetime
    attendees: list[AttendeeResponse] = []
    agenda_items: list[AgendaItemResponse] = []
    discussion: Optional[DiscussionResponse] = None
    tasks: list[TaskResponse] = []
    next_meeting: Optional[NextMeetingResponse] = None
    supporting_documents: list[FileResponse] = []
    status: str = "Scheduled"

    class Config:
        from_attributes = True


class MeetingListResponse(BaseModel):
    id: int
    title: str
    organization: Optional[str]
    date: Optional[date]
    time: Optional[time]
    venue: Optional[str]
    created_at: datetime
    task_count: int = 0
    status: str = "Scheduled"
    pdf_link: Optional[str] = None
    recording_link: Optional[str] = None

    class Config:
        from_attributes = True


# ── Notification Schemas ───────────────────────────────────────────────

class NotificationResponse(BaseModel):
    id: int
    user_id: Optional[int]
    recipient_email: Optional[str]
    message: str
    notification_type: NotificationType
    is_read: bool
    sent_at: datetime

    class Config:
        from_attributes = True




# ── Dashboard / Analytics Schemas ──────────────────────────────────────

class DashboardStats(BaseModel):
    total_meetings: int
    total_tasks: int
    pending_tasks: int
    in_progress_tasks: int
    completed_tasks: int
    overdue_tasks: int
    upcoming_meetings: int
    total_users: int


class TaskStatusDistribution(BaseModel):
    status: str
    count: int


class MeetingTrend(BaseModel):
    month: str
    count: int


class AnalyticsResponse(BaseModel):
    stats: DashboardStats
    task_distribution: list[TaskStatusDistribution]
    meeting_trends: list[MeetingTrend]
    recent_meetings: list[MeetingListResponse]
    overdue_tasks: list[TaskResponse]
    nearest_upcoming_meeting: Optional[MeetingResponse] = None
    last_meeting: Optional[MeetingResponse] = None


# ── AI Extraction Schemas ──────────────────────────────────────────────

class ExtractedParticipant(BaseModel):
    name: str
    email: Optional[str] = None
    designation: Optional[str] = None
    whatsapp_number: Optional[str] = None
    remarks: Optional[str] = None
    status: AttendanceStatus = AttendanceStatus.PRESENT


class ExtractedAgenda(BaseModel):
    topic: str
    description: Optional[str] = None


class ExtractedTask(BaseModel):
    task: str
    responsible_person: Optional[str] = None
    deadline: Optional[str] = None
    status: str = "Pending"


class ExtractedMOM(BaseModel):
    """Structured MOM data extracted by AI."""
    organization_name: Optional[str] = None
    meeting_title: Optional[str] = None
    meeting_type: Optional[str] = None
    meeting_mode: Optional[str] = None
    date: Optional[str] = None
    time: Optional[str] = None
    venue: Optional[str] = None
    hosted_by: Optional[str] = None
    attendees: list[ExtractedParticipant] = []
    absentees: list[ExtractedParticipant] = []
    agenda: list[ExtractedAgenda] = []
    discussion_summary: Optional[str] = None
    action_items: list[ExtractedTask] = []
    next_meeting_date: Optional[str] = None
    next_meeting_time: Optional[str] = None
