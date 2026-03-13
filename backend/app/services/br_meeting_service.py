"""Board Resolution (BR) service – Clone of MeetingService but for Board Resolutions."""

from datetime import date, time, datetime
from typing import Optional, Any
import logging

from app.services.google_sheets_service import SheetsDB, _to_int, upload_to_drive, delete_from_drive
from app.schemas.schemas import MeetingCreate, ExtractedMOM, MeetingMOMUpdate
from app.services.meeting_service import DotDict, _parse_date, _parse_time, _row_to_meeting_obj, _row_to_attendee, _row_to_agenda, _row_to_discussion, _row_to_task, _row_to_next_meeting

logger = logging.getLogger(__name__)

def _load_br_relations(meeting_id: int):
    """Load all sub-entities for a BR meeting from its specific sheets."""
    attendees = [_row_to_attendee(a) for a in SheetsDB.get_by_field("BR_Directors", "meeting_id", meeting_id)]
    agenda_items = [_row_to_agenda(a) for a in SheetsDB.get_by_field("BR_Agenda", "meeting_id", meeting_id)]

    disc_rows = SheetsDB.get_by_field("BR_Discussions", "meeting_id", meeting_id)
    discussion = _row_to_discussion(disc_rows[0]) if disc_rows else None

    tasks = [_row_to_task(t) for t in SheetsDB.get_by_field("BR_Tasks", "meeting_id", meeting_id)]

    nm_rows = SheetsDB.get_by_field("BR_NextMeeting", "meeting_id", meeting_id)
    next_meeting = _row_to_next_meeting(nm_rows[0]) if nm_rows else None

    files_rows = SheetsDB.get_by_field("BR_Files", "meeting_id", meeting_id)
    files = [DotDict(f) for f in files_rows]

    return attendees, agenda_items, discussion, tasks, next_meeting, files

class BRService:

    @staticmethod
    async def create_br(db, data: MeetingCreate, created_by: int | None = None):
        logger.info("Creating BR: %s", data.title)
        now = datetime.utcnow().isoformat()

        meeting_row = SheetsDB.append_row("BR_Meetings", {
            "title": data.title,
            "organization": data.organization or "Botivate Services LLP",
            "meeting_type": data.meeting_type or "Board Resolution",
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

        # Batch Directors
        if data.attendees:
            SheetsDB.append_rows("BR_Directors", [
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
            SheetsDB.append_rows("BR_Agenda", [
                {"meeting_id": meeting_id, "topic": ag.topic, "description": ag.description}
                for ag in data.agenda_items
            ])

        # Discussion / Resolution
        if data.discussion_summary:
            SheetsDB.append_row("BR_Discussions", {
                "meeting_id": meeting_id,
                "summary_text": data.discussion_summary,
            })

        # Batch Tasks / Action Items
        if data.tasks:
            SheetsDB.append_rows("BR_Tasks", [
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
            SheetsDB.append_row("BR_NextMeeting", {
                "meeting_id": meeting_id,
                "next_date": data.next_meeting.next_date,
                "next_time": data.next_meeting.next_time,
            })

        return await BRService.get_br(db, meeting_id)

    @staticmethod
    async def get_br(db, meeting_id: int):
        m = SheetsDB.get_by_id("BR_Meetings", meeting_id)
        if not m:
            return None
        attendees, agenda_items, discussion, tasks, next_meeting, files = _load_br_relations(meeting_id)
        return _row_to_meeting_obj(m, attendees, agenda_items, discussion, tasks, next_meeting, files)

    @staticmethod
    async def list_brs(db, skip: int = 0, limit: int = 50):
        all_brs = SheetsDB.get_all("BR_Meetings")
        all_brs.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        sliced = all_brs[skip:skip + limit]

        results = []
        for m in sliced:
            mid = _to_int(str(m.get("id", "")))
            tasks = SheetsDB.get_by_field("BR_Tasks", "meeting_id", mid) if mid else []
            results.append(_row_to_meeting_obj(m, tasks=[_row_to_task(t) for t in tasks]))
        return results

    @staticmethod
    async def delete_br(db, meeting_id: int) -> bool:
        m = SheetsDB.get_by_id("BR_Meetings", meeting_id)
        if not m:
            return False
            
        # 1. Drive Cleanup: Delete the Entire folder (recursive)
        folder_id = m.get("drive_folder_id")
        if folder_id:
            delete_from_drive(folder_id)
        else:
            # Fallback for old records
            if m.get("drive_file_id"): delete_from_drive(m["drive_file_id"])
            if m.get("drive_recording_id"): delete_from_drive(m["drive_recording_id"])
            
            # Legacy Ref files delete
            ref_files = SheetsDB.get_by_field("BR_Files", "meeting_id", meeting_id)
            for rf in ref_files:
                if rf.get("drive_file_id"): delete_from_drive(rf["drive_file_id"])

        # 2. Database Cleanup (Cascading)
        # Note: TaskHistory might be shared or prefixed, but standard is 'TaskHistory'
        tasks = SheetsDB.get_by_field("BR_Tasks", "meeting_id", meeting_id)
        for t in tasks:
            tid = _to_int(str(t.get("id", "")))
            if tid:
                # We assume BR tasks also log to TaskHistory if implemented
                SheetsDB.delete_by_field("TaskHistory", "task_id", tid)

        # Clear BR specific related sheets
        related_sheets = [
            "BR_Directors", "BR_Agenda", "BR_Discussions", "BR_Tasks", 
            "BR_NextMeeting", "BR_Files"
        ]
        for sheet in related_sheets:
            SheetsDB.delete_by_field(sheet, "meeting_id", meeting_id)
            
        # Finally delete from the main BR table
        SheetsDB.delete_row("BR_Meetings", meeting_id)
        logger.info(f"BR Meeting {meeting_id} and all related data purged.")
        return True

    @staticmethod
    async def update_br_pdf_link(meeting_id: int, pdf_link: str, drive_file_id: str, drive_folder_id: str = None):
        update_data = {
            "pdf_link": pdf_link,
            "drive_file_id": drive_file_id,
        }
        if drive_folder_id:
            update_data["drive_folder_id"] = drive_folder_id
            
        SheetsDB.update_row("BR_Meetings", meeting_id, update_data)
    
    @staticmethod
    async def add_mom_to_br(db, meeting_id: int, data: MeetingMOMUpdate):
        """Add formal Board Resolution details to a scheduled meeting."""
        meeting = await BRService.get_br(db, meeting_id)
        if not meeting:
            return None

        # Attendance & Remarks
        for update_a in data.attendees:
            SheetsDB.update_row("BR_Directors", update_a.id, {
                "attendance_status": update_a.attendance_status,
                "remarks": update_a.remarks
            })

        # Resolution Text
        if data.discussion_summary:
            existing = SheetsDB.get_by_field("BR_Discussions", "meeting_id", meeting_id)
            if existing:
                SheetsDB.update_row("BR_Discussions", _to_int(str(existing[0].get("id", ""))), {"summary_text": data.discussion_summary})
            else:
                SheetsDB.append_row("BR_Discussions", {"meeting_id": meeting_id, "summary_text": data.discussion_summary})

        # Tasks
        now = datetime.utcnow().isoformat()
        if data.tasks:
            SheetsDB.append_rows("BR_Tasks", [
                {
                    "meeting_id": meeting_id, "title": t.title,
                    "description": t.description, "responsible_person": t.responsible_person,
                    "responsible_email": t.responsible_email, "deadline": t.deadline,
                    "status": t.status, "created_at": now,
                } for t in data.tasks
            ])

        # Next
        if data.next_meeting:
            existing = SheetsDB.get_by_field("BR_NextMeeting", "meeting_id", meeting_id)
            if existing:
                SheetsDB.update_row("BR_NextMeeting", _to_int(str(existing[0].get("id", ""))), {
                    "next_date": data.next_meeting.next_date,
                    "next_time": data.next_meeting.next_time,
                })
            else:
                SheetsDB.append_row("BR_NextMeeting", {
                    "meeting_id": meeting_id,
                    "next_date": data.next_meeting.next_date,
                    "next_time": data.next_meeting.next_time,
                })

        # Mark as Completed
        SheetsDB.update_row("BR_Meetings", meeting_id, {"status": "Completed"})

        # Notify Attendees with Final Resolution Summary & Remarks
        final_br = await BRService.get_br(db, meeting_id)
        if final_br and final_br.attendees:
            from app.notifications.notification_service import NotificationService
            
            task_html = ""
            if final_br.tasks:
                task_html = "<table border='1' style='border-collapse:collapse;width:100%;margin:16px 0;'><tr style='background:#f0f4f8;'><th style='padding:10px;'>Action Item</th><th style='padding:10px;'>Owner</th><th style='padding:10px;'>Deadline</th></tr>"
                for t in final_br.tasks:
                    deadline_str = str(t.deadline) if t.deadline else "N/A"
                    task_html += f"<tr><td style='padding:10px;'>{t.title}</td><td style='padding:10px;'>{t.responsible_person or 'None'}</td><td style='padding:10px;'>{deadline_str}</td></tr>"
                task_html += "</table>"
            else:
                task_html = "<p>No new action items assigned.</p>"

            for attendee in final_br.attendees:
                if attendee.email:
                    is_absent = (str(attendee.attendance_status).strip() != "Present")
                    await NotificationService.notify_meeting_summary(
                        None, email=attendee.email, user_name=attendee.user_name,
                        meeting_title=meeting.title, is_absent=is_absent,
                        summary=data.discussion_summary or "Attached in Resolution PDF.", 
                        task_html=task_html, 
                        remarks=attendee.remarks,
                        is_br=True
                    )

        return final_br

    @staticmethod
    async def create_br_from_extraction(db, extracted: ExtractedMOM, created_by: int | None = None, file_path: str | None = None):
        """Build a Board Resolution record from AI-extracted data."""
        now = datetime.utcnow().isoformat()

        meeting_row = SheetsDB.append_row("BR_Meetings", {
            "title": extracted.meeting_title or "Untitled Board Resolution",
            "organization": extracted.organization_name,
            "meeting_type": "Board Resolution",
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

        # Batch Directors
        directors_to_add = []
        for p in extracted.attendees:
            directors_to_add.append({
                "meeting_id": meeting_id, "user_name": p.name, "email": p.email,
                "designation": p.designation, "whatsapp_number": p.whatsapp_number,
                "remarks": p.remarks, "attendance_status": "Present",
            })
        for p in extracted.absentees:
            directors_to_add.append({
                "meeting_id": meeting_id, "user_name": p.name, "email": p.email,
                "designation": p.designation, "whatsapp_number": p.whatsapp_number,
                "remarks": p.remarks, "attendance_status": "Absent",
            })
        if directors_to_add:
            SheetsDB.append_rows("BR_Directors", directors_to_add)

        # Batch Agenda
        if extracted.agenda:
            SheetsDB.append_rows("BR_Agenda", [
                {"meeting_id": meeting_id, "topic": ag.topic, "description": ag.description}
                for ag in extracted.agenda
            ])

        # Discussion / Resolution
        if extracted.discussion_summary:
            SheetsDB.append_row("BR_Discussions", {"meeting_id": meeting_id, "summary_text": extracted.discussion_summary})

        # Build email map
        attendee_email_map = {p.name: p.email for p in extracted.attendees if p.email}

        # Batch Tasks
        if extracted.action_items:
            SheetsDB.append_rows("BR_Tasks", [
                {
                    "meeting_id": meeting_id, "title": item.task,
                    "responsible_person": item.responsible_person,
                    "responsible_email": attendee_email_map.get(item.responsible_person),
                    "deadline": item.deadline, "status": "Pending", "created_at": now,
                } for item in extracted.action_items
            ])

        # Next
        nd = extracted.next_meeting_date
        nt = extracted.next_meeting_time
        if nd or nt:
            SheetsDB.append_row("BR_NextMeeting", {"meeting_id": meeting_id, "next_date": nd, "next_time": nt})

        # Files
        if file_path:
            ext = file_path.rsplit(".", 1)[-1] if "." in file_path else "unknown"
            SheetsDB.append_row("BR_Files", {
                "meeting_id": meeting_id, "file_path": file_path,
                "file_type": ext, "uploaded_at": now,
            })

        return await BRService.get_br(db, meeting_id)

    @staticmethod
    async def count_brs(db) -> int:
        return SheetsDB.count("BR_Meetings")

    @staticmethod
    async def upcoming_brs(db, limit: int = 5):
        all_meetings = SheetsDB.get_all("BR_Meetings")
        upcoming = [m for m in all_meetings if m.get("status") in ["Scheduled", "Rescheduled", "Processing"]]
        upcoming.sort(key=lambda x: x.get("date", ""))
        return [_row_to_meeting_obj(m) for m in upcoming[:limit]]

    @staticmethod
    async def update_br_status(meeting_id: int, status: str):
        SheetsDB.update_row("BR_Meetings", meeting_id, {"status": status})

    @staticmethod
    async def cancel_br(meeting_id: int):
        SheetsDB.update_row("BR_Meetings", meeting_id, {"status": "Cancelled"})

    @staticmethod
    async def reschedule_br(meeting_id: int, new_date: date, new_time: time):
        SheetsDB.update_row("BR_Meetings", meeting_id, {
            "date": new_date,
            "time": new_time,
            "status": "Rescheduled"
        })

    @staticmethod
    async def update_br_task(task_id: int, status: str):
        """Update status of a BR task."""
        return SheetsDB.update_row("BR_Tasks", task_id, {"status": status})
