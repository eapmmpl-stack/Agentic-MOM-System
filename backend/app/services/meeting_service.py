"""Meeting service – CRUD using Google Sheets as the database."""

from datetime import date, time, datetime
from typing import Optional, Any
import logging

from app.services.google_sheets_service import SheetsDB, _to_int, upload_to_drive, delete_from_drive
from app.schemas.schemas import MeetingCreate, ExtractedMOM, MeetingMOMUpdate

logger = logging.getLogger(__name__)


# ── Helper: dict → object-like namespace for PDF generation etc. ──────

class DotDict:
    """Converts a dict to an object with attribute access (for templates)."""
    def __init__(self, d: dict):
        for k, v in d.items():
            setattr(self, k, v)

    def __repr__(self):
        return str(self.__dict__)


def _parse_date(s: str | None) -> date | None:
    if not s or str(s).strip() == "":
        return None
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%m/%d/%Y", "%B %d, %Y", "%d %B %Y"):
        try:
            return datetime.strptime(str(s).strip(), fmt).date()
        except ValueError:
            continue
    return None


def _parse_time(s: str | None) -> time | None:
    if not s or str(s).strip() == "":
        return None
    for fmt in ("%H:%M", "%I:%M %p", "%H:%M:%S"):
        try:
            return datetime.strptime(str(s).strip(), fmt).time()
        except ValueError:
            continue
    return None


def _row_to_meeting_obj(m: dict, attendees=None, agenda_items=None, discussion=None, tasks=None, next_meeting=None, files=None):
    """Convert sheet row dicts into a DotDict meeting object suitable for API responses."""
    meeting = DotDict({
        "id": _to_int(str(m.get("id", ""))) or 0,
        "title": m.get("title", ""),
        "organization": m.get("organization") or None,
        "meeting_type": m.get("meeting_type") or None,
        "meeting_mode": m.get("meeting_mode") or None,
        "date": _parse_date(m.get("date")),
        "time": _parse_time(m.get("time")),
        "venue": m.get("venue") or None,
        "hosted_by": m.get("hosted_by") or None,
        "file_path": m.get("file_path") or None,
        "created_by": _to_int(str(m.get("created_by", ""))) if m.get("created_by") else None,
        "created_at": datetime.fromisoformat(m["created_at"]) if m.get("created_at") else datetime.utcnow(),
        "pdf_link": m.get("pdf_link") or None,
        "drive_file_id": m.get("drive_file_id") or None,
        "drive_folder_id": m.get("drive_folder_id") or None,
        "recording_link": m.get("recording_link") or None,
        "drive_recording_id": m.get("drive_recording_id") or None,
        "drive_transcript_id": m.get("drive_transcript_id") or None,
        "ai_summary_link": m.get("ai_summary_link") or None,
        "drive_logs_link": m.get("drive_logs_link") or None,
        "status": m.get("status") or "Scheduled",
        "attendees": attendees or [],
        "agenda_items": agenda_items or [],
        "discussion": discussion,
        "tasks": tasks or [],
        "next_meeting": next_meeting,
        "supporting_documents": files or [],
    })
    return meeting


def _row_to_attendee(a: dict):
    return DotDict({
        "id": _to_int(str(a.get("id", ""))) or 0,
        "meeting_id": _to_int(str(a.get("meeting_id", ""))) or 0,
        "user_name": a.get("user_name", ""),
        "email": a.get("email") or None,
        "designation": a.get("designation") or None,
        "whatsapp_number": a.get("whatsapp_number") or None,
        "remarks": a.get("remarks") or None,
        "attendance_status": a.get("attendance_status", "Present"),
    })


def _row_to_agenda(a: dict):
    return DotDict({
        "id": _to_int(str(a.get("id", ""))) or 0,
        "meeting_id": _to_int(str(a.get("meeting_id", ""))) or 0,
        "topic": a.get("topic", ""),
        "description": a.get("description") or None,
    })


def _row_to_discussion(d: dict):
    return DotDict({
        "id": _to_int(str(d.get("id", ""))) or 0,
        "meeting_id": _to_int(str(d.get("meeting_id", ""))) or 0,
        "summary_text": d.get("summary_text", ""),
    })


def _row_to_task(t: dict):
    return DotDict({
        "id": _to_int(str(t.get("id", ""))) or 0,
        "meeting_id": _to_int(str(t.get("meeting_id", ""))) or 0,
        "title": t.get("title", ""),
        "description": t.get("description") or None,
        "responsible_person": t.get("responsible_person") or None,
        "responsible_email": t.get("responsible_email") or None,
        "deadline": _parse_date(t.get("deadline")),
        "status": t.get("status", "Pending"),
        "created_at": datetime.fromisoformat(t["created_at"]) if t.get("created_at") else datetime.utcnow(),
    })


def _row_to_next_meeting(n: dict):
    return DotDict({
        "id": _to_int(str(n.get("id", ""))) or 0,
        "meeting_id": _to_int(str(n.get("meeting_id", ""))) or 0,
        "next_date": _parse_date(n.get("next_date")),
        "next_time": _parse_time(n.get("next_time")),
    })


def _load_meeting_relations(meeting_id: int):
    """Load all sub-entities for a meeting from their sheets."""
    attendees = [_row_to_attendee(a) for a in SheetsDB.get_by_field("Attendees", "meeting_id", meeting_id)]
    agenda_items = [_row_to_agenda(a) for a in SheetsDB.get_by_field("Agenda", "meeting_id", meeting_id)]

    disc_rows = SheetsDB.get_by_field("Discussions", "meeting_id", meeting_id)
    discussion = _row_to_discussion(disc_rows[0]) if disc_rows else None

    tasks = [_row_to_task(t) for t in SheetsDB.get_by_field("Tasks", "meeting_id", meeting_id)]

    nm_rows = SheetsDB.get_by_field("NextMeeting", "meeting_id", meeting_id)
    next_meeting = _row_to_next_meeting(nm_rows[0]) if nm_rows else None

    files_rows = SheetsDB.get_by_field("Files", "meeting_id", meeting_id)
    files = [DotDict(f) for f in files_rows]

    return attendees, agenda_items, discussion, tasks, next_meeting, files


class MeetingService:

    @staticmethod
    async def create_meeting(db, data: MeetingCreate, created_by: int | None = None):
        logger.info("Creating meeting: %s", data.title)
        now = datetime.utcnow().isoformat()

        meeting_row = SheetsDB.append_row("Meetings", {
            "title": data.title,
            "organization": data.organization or "Botivate Services LLP",
            "meeting_type": data.meeting_type,
            "meeting_mode": data.meeting_mode,
            "date": data.date,
            "time": data.time,
            "venue": data.venue,
            "hosted_by": data.hosted_by,
            "created_by": created_by,
            "created_at": now,
            "status": data.status or "Scheduled",
        })
        meeting_id = _to_int(str(meeting_row.get("id", "")))

        # Batch Attendees
        if data.attendees:
            SheetsDB.append_rows("Attendees", [
                {
                    "meeting_id": meeting_id,
                    "user_name": att.user_name,
                    "email": att.email,
                    "designation": att.designation,
                    "whatsapp_number": att.whatsapp_number,
                    "remarks": att.remarks,
                    "attendance_status": att.attendance_status,
                } for att in data.attendees
            ])

        # Batch Agenda
        if data.agenda_items:
            SheetsDB.append_rows("Agenda", [
                {"meeting_id": meeting_id, "topic": ag.topic, "description": ag.description}
                for ag in data.agenda_items
            ])

        # Discussion
        if data.discussion_summary:
            SheetsDB.append_row("Discussions", {
                "meeting_id": meeting_id,
                "summary_text": data.discussion_summary,
            })

        # Batch Tasks
        if data.tasks:
            SheetsDB.append_rows("Tasks", [
                {
                    "meeting_id": meeting_id,
                    "title": t.title,
                    "description": t.description,
                    "responsible_person": t.responsible_person,
                    "responsible_email": t.responsible_email,
                    "deadline": t.deadline,
                    "status": t.status,
                    "created_at": now,
                } for t in data.tasks
            ])

        # Next meeting
        if data.next_meeting and (data.next_meeting.next_date or data.next_meeting.next_time):
            SheetsDB.append_row("NextMeeting", {
                "meeting_id": meeting_id,
                "next_date": data.next_meeting.next_date,
                "next_time": data.next_meeting.next_time,
            })

        return await MeetingService.get_meeting(db, meeting_id)

    @staticmethod
    async def create_from_extraction(db, extracted: ExtractedMOM, created_by: int | None = None, file_path: str | None = None):
        """Build a Meeting record from AI-extracted MOM data."""
        now = datetime.utcnow().isoformat()

        meeting_row = SheetsDB.append_row("Meetings", {
            "title": extracted.meeting_title or "Untitled Meeting",
            "organization": extracted.organization_name,
            "meeting_type": extracted.meeting_type,
            "meeting_mode": extracted.meeting_mode,
            "date": extracted.date,
            "time": extracted.time,
            "venue": extracted.venue,
            "hosted_by": extracted.hosted_by,
            "file_path": file_path,
            "created_by": created_by,
            "created_at": now,
            "status": "Completed",
        })
        meeting_id = _to_int(str(meeting_row.get("id", "")))

        # Batch Attendees
        attendees_to_add = []
        for p in extracted.attendees:
            attendees_to_add.append({
                "meeting_id": meeting_id, "user_name": p.name, "email": p.email,
                "designation": p.designation, "whatsapp_number": p.whatsapp_number,
                "remarks": p.remarks, "attendance_status": "Present",
            })
        for p in extracted.absentees:
            attendees_to_add.append({
                "meeting_id": meeting_id, "user_name": p.name, "email": p.email,
                "designation": p.designation, "whatsapp_number": p.whatsapp_number,
                "remarks": p.remarks, "attendance_status": "Absent",
            })
        if attendees_to_add:
            SheetsDB.append_rows("Attendees", attendees_to_add)

        # Batch Agenda
        if extracted.agenda:
            SheetsDB.append_rows("Agenda", [
                {"meeting_id": meeting_id, "topic": ag.topic, "description": ag.description}
                for ag in extracted.agenda
            ])

        # Discussion
        if extracted.discussion_summary:
            SheetsDB.append_row("Discussions", {"meeting_id": meeting_id, "summary_text": extracted.discussion_summary})

        # Build attendee email map
        attendee_email_map = {p.name: p.email for p in extracted.attendees if p.email}

        # Batch Tasks
        if extracted.action_items:
            SheetsDB.append_rows("Tasks", [
                {
                    "meeting_id": meeting_id,
                    "title": item.task,
                    "responsible_person": item.responsible_person,
                    "responsible_email": attendee_email_map.get(item.responsible_person),
                    "deadline": item.deadline,
                    "status": "Pending",
                    "created_at": now,
                } for item in extracted.action_items
            ])

        # Next meeting
        nd = extracted.next_meeting_date
        nt = extracted.next_meeting_time
        if nd or nt:
            SheetsDB.append_row("NextMeeting", {"meeting_id": meeting_id, "next_date": nd, "next_time": nt})

        # File reference
        if file_path:
            ext = file_path.rsplit(".", 1)[-1] if "." in file_path else "unknown"
            SheetsDB.append_row("Files", {
                "meeting_id": meeting_id, "file_path": file_path,
                "file_type": ext, "uploaded_at": now,
            })

        return await MeetingService.get_meeting(db, meeting_id)

    @staticmethod
    async def get_meeting(db, meeting_id: int):
        m = SheetsDB.get_by_id("Meetings", meeting_id)
        if not m:
            return None
        attendees, agenda_items, discussion, tasks, next_meeting, files = _load_meeting_relations(meeting_id)
        return _row_to_meeting_obj(m, attendees, agenda_items, discussion, tasks, next_meeting, files)

    @staticmethod
    async def add_mom_to_meeting(db, meeting_id: int, data: MeetingMOMUpdate):
        meeting = await MeetingService.get_meeting(db, meeting_id)
        if not meeting:
            return None

        # Update attendance statuses AND remarks
        for update_a in data.attendees:
            SheetsDB.update_row("Attendees", update_a.id, {
                "attendance_status": update_a.attendance_status,
                "remarks": update_a.remarks
            })

        # Discussion
        if data.discussion_summary:
            existing = SheetsDB.get_by_field("Discussions", "meeting_id", meeting_id)
            if existing:
                SheetsDB.update_row("Discussions", _to_int(str(existing[0].get("id", ""))), {"summary_text": data.discussion_summary})
            else:
                SheetsDB.append_row("Discussions", {"meeting_id": meeting_id, "summary_text": data.discussion_summary})

        # Tasks
        now = datetime.utcnow().isoformat()
        for t in data.tasks:
            SheetsDB.append_row("Tasks", {
                "meeting_id": meeting_id, "title": t.title,
                "description": t.description, "responsible_person": t.responsible_person,
                "responsible_email": t.responsible_email, "deadline": t.deadline,
                "status": t.status, "created_at": now,
            })

        # Next meeting
        if data.next_meeting:
            existing = SheetsDB.get_by_field("NextMeeting", "meeting_id", meeting_id)
            if existing:
                SheetsDB.update_row("NextMeeting", _to_int(str(existing[0].get("id", ""))), {
                    "next_date": data.next_meeting.next_date,
                    "next_time": data.next_meeting.next_time,
                })
            else:
                SheetsDB.append_row("NextMeeting", {
                    "meeting_id": meeting_id,
                    "next_date": data.next_meeting.next_date,
                    "next_time": data.next_meeting.next_time,
                })

        # Mark as Completed
        SheetsDB.update_row("Meetings", meeting_id, {"status": "Completed"})

        # Notify Attendees with Final MOM & Remarks
        final_meeting = await MeetingService.get_meeting(db, meeting_id)
        if final_meeting and final_meeting.attendees:
            # Import here to avoid circular dependencies
            from app.notifications.notification_service import NotificationService
            
            # Prepare task list HTML for email
            task_html = ""
            if final_meeting.tasks:
                task_html = "<table border='1' style='border-collapse:collapse;width:100%;margin:16px 0;'><tr style='background:#f0f4f8;'><th style='padding:10px;'>Task</th><th style='padding:10px;'>Owner</th><th style='padding:10px;'>Deadline</th></tr>"
                for t in final_meeting.tasks:
                    deadline_str = str(t.deadline) if t.deadline else "N/A"
                    task_html += f"<tr><td style='padding:10px;'>{t.title}</td><td style='padding:10px;'>{t.responsible_person or 'None'}</td><td style='padding:10px;'>{deadline_str}</td></tr>"
                task_html += "</table>"
            else:
                task_html = "<p>No new tasks assigned.</p>"

            for attendee in final_meeting.attendees:
                if attendee.email:
                    is_absent = (str(attendee.attendance_status).strip() != "Present")
                    await NotificationService.notify_meeting_summary(
                        None, email=attendee.email, user_name=attendee.user_name,
                        meeting_title=meeting.title, is_absent=is_absent,
                        summary=data.discussion_summary or "Attached in MOM.", 
                        task_html=task_html, 
                        remarks=attendee.remarks,
                        is_br=False
                    )

        return final_meeting

    @staticmethod
    async def list_meetings(db, skip: int = 0, limit: int = 50):
        all_meetings = SheetsDB.get_all("Meetings")
        # Sort by created_at descending
        all_meetings.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        sliced = all_meetings[skip:skip + limit]

        results = []
        for m in sliced:
            mid = _to_int(str(m.get("id", "")))
            tasks = SheetsDB.get_by_field("Tasks", "meeting_id", mid) if mid else []
            results.append(_row_to_meeting_obj(m, tasks=[_row_to_task(t) for t in tasks]))
        return results

    @staticmethod
    async def delete_meeting(db, meeting_id: int) -> bool:
        m = SheetsDB.get_by_id("Meetings", meeting_id)
        if not m:
            return False
            
        # 1. Drive Cleanup: Delete the Entire folder (recursive)
        folder_id = m.get("drive_folder_id")
        if folder_id:
            delete_from_drive(folder_id)
        else:
            # Fallback for legacy records
            if m.get("drive_file_id"): delete_from_drive(m["drive_file_id"])
            if m.get("drive_recording_id"): delete_from_drive(m["drive_recording_id"])

        # 2. Database Cleanup (Cascading)
        # First, find tasks to clean TaskHistory
        tasks = SheetsDB.get_by_field("Tasks", "meeting_id", meeting_id)
        for t in tasks:
            tid = _to_int(str(t.get("id", "")))
            if tid:
                SheetsDB.delete_by_field("TaskHistory", "task_id", tid)

        # Clear other related sheets
        related_sheets = [
            "Attendees", "Agenda", "Discussions", "Tasks", 
            "NextMeeting", "Files"
        ]
        for sheet in related_sheets:
            SheetsDB.delete_by_field(sheet, "meeting_id", meeting_id)
            
        # Finally delete the meeting itself
        SheetsDB.delete_row("Meetings", meeting_id)
        logger.info(f"Meeting {meeting_id} and all related data purged.")
        return True

    @staticmethod
    async def count_meetings(db) -> int:
        return SheetsDB.count("Meetings")

    @staticmethod
    async def upcoming_meetings(db, limit: int = 5):
        all_meetings = SheetsDB.get_all("Meetings")
        upcoming = [m for m in all_meetings if m.get("status") in ["Scheduled", "Rescheduled", "Processing"]]
        upcoming.sort(key=lambda x: x.get("date", ""))
        return [_row_to_meeting_obj(m) for m in upcoming[:limit]]

    @staticmethod
    async def update_meeting_status(meeting_id: int, status: str):
        SheetsDB.update_row("Meetings", meeting_id, {"status": status})

    @staticmethod
    async def cancel_meeting(meeting_id: int):
        SheetsDB.update_row("Meetings", meeting_id, {"status": "Cancelled"})

    @staticmethod
    async def reschedule_meeting(meeting_id: int, new_date: date, new_time: time):
        SheetsDB.update_row("Meetings", meeting_id, {
            "date": new_date,
            "time": new_time,
            "status": "Rescheduled"
        })

    @staticmethod
    async def update_meeting_pdf_link(meeting_id: int, pdf_link: str, drive_file_id: str, drive_folder_id: str = None):
        """Update the PDF link and drive file ID for a meeting."""
        update_data = {
            "pdf_link": pdf_link,
            "drive_file_id": drive_file_id,
        }
        if drive_folder_id:
            update_data["drive_folder_id"] = drive_folder_id

        SheetsDB.update_row("Meetings", meeting_id, update_data)
