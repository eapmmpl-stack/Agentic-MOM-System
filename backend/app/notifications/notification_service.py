"""Unified notification dispatcher – Google Sheets backed."""

import logging
from typing import Optional
from datetime import datetime

from app.services.google_sheets_service import SheetsDB, _to_int
from app.services.meeting_service import DotDict, _parse_iso_datetime
from app.notifications.email_service import EmailService

logger = logging.getLogger(__name__)


class NotificationService:

    @staticmethod
    async def notify_task_assigned(db, task, meeting_title: str, is_br: bool = False):
        """Send notification when a task is assigned."""
        email = task.responsible_email if hasattr(task, 'responsible_email') else None
        if email:
            await EmailService.send_task_assignment(
                to_email=email,
                task_title=task.title,
                meeting_title=meeting_title,
                deadline=str(task.deadline) if task.deadline else None,
                is_br=is_br
            )
            SheetsDB.append_row("Notifications", {
                "recipient_email": email,
                "message": f"Task assigned: {task.title} (Source: {meeting_title})",
                "notification_type": "email",
                "is_read": "False",
                "sent_at": datetime.utcnow().isoformat(),
            })

    @staticmethod
    async def notify_deadline_reminder(db, task):
        email = task.responsible_email if hasattr(task, 'responsible_email') else None
        deadline = task.deadline if hasattr(task, 'deadline') else None
        if email and deadline:
            await EmailService.send_deadline_reminder(
                to_email=email,
                task_title=task.title,
                deadline=str(deadline),
            )
            SheetsDB.append_row("Notifications", {
                "recipient_email": email,
                "message": f"Deadline reminder: {task.title} due {deadline}",
                "notification_type": "email",
                "is_read": "False",
                "sent_at": datetime.utcnow().isoformat(),
            })

    @staticmethod
    async def notify_overdue(db, task):
        email = task.responsible_email if hasattr(task, 'responsible_email') else None
        deadline = task.deadline if hasattr(task, 'deadline') else None
        if email and deadline:
            await EmailService.send_overdue_alert(
                to_email=email,
                task_title=task.title,
                deadline=str(deadline),
            )
            SheetsDB.append_row("Notifications", {
                "recipient_email": email,
                "message": f"OVERDUE: {task.title} was due {deadline}",
                "notification_type": "email",
                "is_read": "False",
                "sent_at": datetime.utcnow().isoformat(),
            })

    @staticmethod
    async def notify_absence_warning(db, email: str, user_name: str, count: int):
        await EmailService.send_absence_warning(email, user_name, count)
        SheetsDB.append_row("Notifications", {
            "recipient_email": email,
            "message": f"Attendance warning: {user_name} absent {count} times",
            "notification_type": "email",
            "is_read": "False",
            "sent_at": datetime.utcnow().isoformat(),
        })

    @staticmethod
    async def notify_meeting_invitation(db, email: str, user_name: str, meeting_title: str, date: str, time: str, venue: str, remarks: Optional[str] = None, is_br: bool = False, is_rescheduled: bool = False):
        if email:
            await EmailService.send_meeting_invitation(
                email,
                user_name,
                meeting_title,
                date,
                time,
                venue,
                remarks=remarks,
                is_br=is_br,
                is_rescheduled=is_rescheduled,
            )
            SheetsDB.append_row("Notifications", {
                "recipient_email": email,
                "message": f"Invitation: {meeting_title} on {date}",
                "notification_type": "email",
                "is_read": "False",
                "sent_at": datetime.utcnow().isoformat(),
            })

    @staticmethod
    async def notify_meeting_cancellation(db, email: str, user_name: str, meeting_title: str, is_br: bool = False):
        if email:
            await EmailService.send_meeting_cancellation(email, user_name, meeting_title, is_br=is_br)
            SheetsDB.append_row("Notifications", {
                "recipient_email": email,
                "message": f"CANCELLATION: {meeting_title}",
                "notification_type": "email",
                "is_read": "False",
                "sent_at": datetime.utcnow().isoformat(),
            })

    @staticmethod
    async def notify_meeting_rescheduled(db, email: str, user_name: str, meeting_title: str, old_date: str, old_time: str, new_date: str, new_time: str, is_br: bool = False):
        if email:
            await EmailService.send_meeting_rescheduled(email, user_name, meeting_title, old_date, old_time, new_date, new_time, is_br=is_br)
            SheetsDB.append_row("Notifications", {
                "recipient_email": email,
                "message": f"RESCHEDULED: {meeting_title} to {new_date} {new_time}",
                "notification_type": "email",
                "is_read": "False",
                "sent_at": datetime.utcnow().isoformat(),
            })

    @staticmethod
    async def notify_meeting_summary(db, email: str, user_name: str, meeting_title: str, is_absent: bool, summary: str, task_html: str, pdf_data: Optional[bytes] = None, pdf_name: Optional[str] = None, is_br: bool = False, pdf_link: Optional[str] = None):
        if email:
            await EmailService.send_meeting_summary(email, user_name, meeting_title, is_absent, summary, task_html, pdf_data=pdf_data, pdf_name=pdf_name, is_br=is_br, pdf_link=pdf_link)
            SheetsDB.append_row("Notifications", {
                "recipient_email": email,
                "message": f"Received MOM/Resolution for: {meeting_title}",
                "notification_type": "email",
                "is_read": "False",
                "sent_at": datetime.utcnow().isoformat(),
            })

    @staticmethod
    async def list_notifications(db, skip: int = 0, limit: int = 50):
        all_notifs = SheetsDB.get_all("Notifications")
        all_notifs.sort(key=lambda x: x.get("sent_at", ""), reverse=True)
        sliced = all_notifs[skip:skip + limit]
        return [DotDict({
            "id": _to_int(str(n.get("id", ""))) or 0,
            "user_id": _to_int(str(n.get("user_id", ""))) if n.get("user_id") else None,
            "recipient_email": n.get("recipient_email") or None,
            "message": n.get("message", ""),
            "notification_type": n.get("notification_type", "email"),
            "is_read": str(n.get("is_read", "")).strip().lower() in ("true", "1", "yes"),
            "sent_at": _parse_iso_datetime(n.get("sent_at")),
        }) for n in sliced]

    @staticmethod
    async def notify_cs_mom(db, email: str, meeting_title: str, pdf_data: bytes, pdf_name: str, is_br: bool = False, pdf_link: Optional[str] = None):
        """Send notification to Company Secretary including the official PDF."""
        if email:
            await EmailService.send_cs_mom(email, meeting_title, pdf_data, pdf_name, is_br=is_br, pdf_link=pdf_link)
            SheetsDB.append_row("Notifications", {
                "recipient_email": email,
                "message": f"GOVERNANCE FILING: Submitted MOM/Resolution for {meeting_title}",
                "notification_type": "email",
                "is_read": "False",
                "sent_at": datetime.utcnow().isoformat(),
            })

    @staticmethod
    async def mark_read(db, notification_id: int) -> bool:
        notif = SheetsDB.get_by_id("Notifications", notification_id)
        if not notif:
            return False
        SheetsDB.update_row("Notifications", notification_id, {"is_read": "True"})
        return True
