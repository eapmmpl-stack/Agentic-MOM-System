"""Email notification service using aiosmtplib."""

import logging
from typing import Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from datetime import datetime

import aiosmtplib

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

def get_base_template(title: str, content: str, is_br: bool = False) -> str:
    """Returns professional branding – either Standard or Board Resolution style."""
    # Branding config
    accent_primary = "#4f46e5" if not is_br else "#1e293b" # Royal Blue vs Deep Corporate Charcoal
    accent_secondary = "#60a5fa" if not is_br else "#64748b" 
    brand_name = settings.CLIENT_NAME if not is_br else f"{settings.CLIENT_NAME} Board Governance"
    tagline = "Meeting Intelligence Portal" if not is_br else "Official Board Resolution Management"
    system_name = f"{settings.CLIENT_NAME} Management System" if not is_br else f"{settings.CLIENT_NAME} Corporate Governance Portal"
    
    return f"""
    <!DOCTYPE html>
    <html>
    <body style="margin: 0; padding: 0; background-color: #f8fafc; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; -webkit-font-smoothing: antialiased;">
        <table align="center" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width: 600px; margin: 40px auto; background-color: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);">
            <!-- Header Ribbon -->
            <tr>
                <td style="height: 6px; background: linear-gradient(90deg, {accent_secondary} 0%, {accent_primary} 100%); line-height: 6px; font-size: 6px;">&nbsp;</td>
            </tr>
            <!-- Header Content -->
            <tr>
                <td style="padding: 30px 40px; border-bottom: 2px solid #f1f5f9;">
                    <table border="0" cellpadding="0" cellspacing="0" width="100%">
                        <tr>
                            <td>
                                <h1 style="margin: 0; font-size: 24px; color: #1e293b; letter-spacing: -0.5px;">{brand_name}</h1>
                                <p style="margin: 4px 0 0; font-size: 13px; color: #64748b; font-style: italic;">{tagline}</p>
                            </td>
                            <td align="right" style="text-align: right;">
                                <h2 style="margin: 0; font-size: 12px; color: #475569; text-transform: uppercase; letter-spacing: 0.5px;">{settings.CLIENT_NAME}</h2>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
            <!-- Main Content Area -->
            <tr>
                <td style="padding: 40px;">
                    <h2 style="margin: 0 0 24px; color: {accent_primary}; font-size: 20px; font-weight: 600;">{title}</h2>
                    {content}
                </td>
            </tr>
            <!-- Footer Area -->
            <tr>
                <td style="padding: 30px 40px; background-color: #f8fafc; border-top: 1px solid #e2e8f0;">
                    <p style="margin: 0; color: #64748b; font-size: 13px; text-align: center;">
                        This is an automated notification from the <strong>{system_name}</strong>.<br>
                        Please do not reply directly to this email.
                    </p>
                    {f'<p style="margin: 12px 0 0; color: #94a3b8; font-size: 11px; text-align: center; font-style: italic;">{settings.BOTIVATE_SIGNATURE}</p>' if settings.SHOW_BOTIVATE_BRANDING else ''}
                </td>
            </tr>
            <!-- Bottom Ribbon -->
            <tr>
                <td style="height: 6px; background: linear-gradient(90deg, {accent_primary} 0%, {accent_secondary} 100%); line-height: 6px; font-size: 6px;">&nbsp;</td>
            </tr>
        </table>
    </body>
    </html>
    """

class EmailService:
    @staticmethod
    async def send_email(to_email: str, subject: str, body_html: str, attachment_data: Optional[bytes] = None, attachment_name: Optional[str] = None) -> bool:
        """Queues an email into the Google Sheets 'EmailQueue' tab for processing by Apps Script."""
        try:
            email_data = {
                "to_email": to_email,
                "subject": subject,
                "body": body_html,
                "status": "Pending",
                "created_at": datetime.now().isoformat()
            }
            
            # Note: We don't store raw bytes in Sheets. 
            # The system already uploads PDFs to Drive and puts links in the summary/notif.
            
            SheetsDB.append_row("EmailQueue", email_data)
            logger.info("Email queued in Google Sheets for %s: %s", to_email, subject)
            return True
        except Exception as e:
            logger.error("Failed to queue email in Google Sheets for %s: %s", to_email, e)
            return Falsealse

    @staticmethod
    async def send_task_assignment(to_email: str, task_title: str, meeting_title: str, deadline: str | None, is_br: bool = False):
        subject = f"New Action Item: {task_title}" if is_br else f"New Task Assigned: {task_title}"
        greeting = "Dear Board Member," if is_br else "Dear Team Member,"
        intro = f"You have been assigned a new mandatory action item from the Board Resolution discussion <strong>{meeting_title}</strong>." if is_br else f"You have been assigned a new task from the meeting <strong>{meeting_title}</strong>."
        label = "Action Item" if is_br else "Task"
        container_bg = "#fffbeb" if is_br else "#f1f5f9"
        
        content = f"""
            <p style="font-size: 16px; color: #475569; margin: 0 0 16px;">{greeting}</p>
            <p style="font-size: 15px; color: #334155; line-height: 1.6; margin: 0 0 24px;">{intro}</p>
            
            <table style="width: 100%; border-collapse: collapse; margin-bottom: 24px; background-color: {container_bg}; border-radius: 6px; overflow: hidden;">
                <tr>
                    <td style="padding: 12px 16px; font-weight: 600; color: #475569; border-bottom: 1px solid #e2e8f0; width: 120px;">{label}</td>
                    <td style="padding: 12px 16px; color: #0f172a; border-bottom: 1px solid #e2e8f0;">{task_title}</td>
                </tr>
                <tr>
                    <td style="padding: 12px 16px; font-weight: 600; color: #475569; border-bottom: 1px solid #e2e8f0;">Source</td>
                    <td style="padding: 12px 16px; color: #0f172a; border-bottom: 1px solid #e2e8f0;">{meeting_title}</td>
                </tr>
                <tr>
                    <td style="padding: 12px 16px; font-weight: 600; color: #475569;">Deadline</td>
                    <td style="padding: 12px 16px; color: #0f172a; font-weight: 600;">{deadline or 'Not specified'}</td>
                </tr>
            </table>
            
            <p style="font-size: 15px; color: #334155; line-height: 1.6; margin: 0;">Please ensure the above resolution item is tracked for compliance. Contact Corporate Governance for details.</p>
        """
        html = get_base_template("Task Assignment", content, is_br=is_br)
        await EmailService.send_email(to_email, subject, html)

    @staticmethod
    async def send_deadline_reminder(to_email: str, task_title: str, deadline: str):
        subject = f"Reminder: Task '{task_title}' deadline approaching"
        content = f"""
            <p style="font-size: 16px; color: #475569; margin: 0 0 16px;">Dear Team Member,</p>
            <div style="background-color: #fef3c7; border-left: 4px solid #f59e0b; padding: 16px; border-radius: 4px; margin-bottom: 24px;">
                <p style="font-size: 15px; color: #92400e; margin: 0;">This is a friendly reminder that your task <strong>{task_title}</strong> is due on <strong>{deadline}</strong>.</p>
            </div>
            <p style="font-size: 15px; color: #334155; line-height: 1.6; margin: 0;">Please ensure it is completed on time. If you require any assistance or an extension, please reach out to the HR Department proactively.</p>
        """
        html = get_base_template("Task Deadline Reminder", content)
        html = html.replace('color: #3b82f6;', 'color: #d97706;') # Change title color to amber
        await EmailService.send_email(to_email, subject, html)

    @staticmethod
    async def send_overdue_alert(to_email: str, task_title: str, deadline: str):
        subject = f"OVERDUE: Task '{task_title}'"
        content = f"""
            <p style="font-size: 16px; color: #475569; margin: 0 0 16px;">Dear Team Member,</p>
            <div style="background-color: #fee2e2; border-left: 4px solid #ef4444; padding: 16px; border-radius: 4px; margin-bottom: 24px;">
                <p style="font-size: 15px; color: #991b1b; margin: 0;"><strong>Critical Alert:</strong> Your task <strong>{task_title}</strong> was due on <strong>{deadline}</strong> and is currently marked as overdue.</p>
            </div>
            <p style="font-size: 15px; color: #334155; line-height: 1.6; margin: 0;">Kindly contact the HR Department immediately to provide a status update on this pending item.</p>
        """
        html = get_base_template("Overdue Task Alert", content)
        html = html.replace('color: #3b82f6;', 'color: #ef4444;') # Change title color to red
        await EmailService.send_email(to_email, subject, html)

    @staticmethod
    async def send_absence_warning(to_email: str, user_name: str, absent_count: int):
        subject = f"Attendance Notice: {user_name}"
        content = f"""
            <p style="font-size: 16px; color: #475569; margin: 0 0 16px;">Dear HR / Management,</p>
            <div style="background-color: #f1f5f9; padding: 16px; border-radius: 6px; margin-bottom: 24px;">
                <p style="font-size: 15px; color: #334155; margin: 0;">This is an automated notice regarding meeting attendance.</p>
                <p style="font-size: 15px; color: #0f172a; margin: 12px 0 0; font-weight: 500;">
                    Team member <span style="color: #4f46e5;">{user_name}</span> has been marked absent from <span style="color: #ef4444; font-weight: 600;">{absent_count}</span> scheduled meetings.
                </p>
            </div>
            <p style="font-size: 15px; color: #334155; line-height: 1.6; margin: 0;">Please review their attendance record and take necessary administrative actions.</p>
        """
        html = get_base_template("Attendance Notice", content)
        html = html.replace('color: #3b82f6;', 'color: #8b5cf6;') # Change title color to purple
        await EmailService.send_email(to_email, subject, html)

    @staticmethod
    async def send_meeting_invitation(to_email: str, recipient_name: str, meeting_title: str, date: str, time: str, venue: str, remarks: Optional[str] = None, is_br: bool = False):
        subject = f"Official Board Resolution Invitation: {meeting_title}" if is_br else f"Meeting Invitation: {meeting_title}"
        intro = "You are hereby formally invited to review and deliberate upon an upcoming Board Resolution." if is_br else "You have been officially invited to the upcoming scheduled meeting."
        meeting_label = "RESOLUTION TITLE" if is_br else "MEETING TITLE"
        
        remarks_html = ""
        if remarks:
            remarks_style = "background-color: #fffbeb; border: 1px solid #fde68a; color: #92400e;" if is_br else "background-color: #f0f9ff; border: 1px solid #bae6fd; color: #0369a1;"
            remarks_html = f"""
            <div style="{remarks_style} padding: 16px; border-radius: 6px; margin-bottom: 24px;">
                <p style="margin: 0; font-size: 14px; line-height: 1.6;"><strong>Personal Note for you:</strong> {remarks}</p>
            </div>
            """

        content = f"""
            <p style="font-size: 16px; color: #475569; margin: 0 0 16px;">Dear {recipient_name},</p>
            <p style="font-size: 15px; color: #334155; line-height: 1.6; margin: 0 0 18px;">{intro}</p>
            
            {remarks_html}

            <table style="width: 100%; border-collapse: collapse; margin-bottom: 24px; border: 1px solid #e2e8f0; border-radius: 6px; overflow: hidden;">
                <tr>
                    <td colspan="2" style="background-color: #f8fafc; padding: 12px 16px; border-bottom: 1px solid #e2e8f0; font-weight: 600; color: #0f172a; font-size: 16px;">
                        <span style="font-size: 11px; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px; display: block; margin-bottom: 4px;">{meeting_label}</span>
                        {meeting_title}
                    </td>
                </tr>
                <tr>
                    <td style="padding: 12px 16px; font-weight: 600; color: #475569; border-bottom: 1px solid #e2e8f0; width: 120px;">Scheduled Date</td>
                    <td style="padding: 12px 16px; color: #0f172a; border-bottom: 1px solid #e2e8f0;"><strong>{date}</strong></td>
                </tr>
                <tr>
                    <td style="padding: 12px 16px; font-weight: 600; color: #475569; border-bottom: 1px solid #e2e8f0;">Time</td>
                    <td style="padding: 12px 16px; color: #0f172a; border-bottom: 1px solid #e2e8f0;"><strong>{time}</strong></td>
                </tr>
                <tr>
                    <td style="padding: 12px 16px; font-weight: 600; color: #475569;">Venue / Portal</td>
                    <td style="padding: 12px 16px; color: #0f172a;">{venue}</td>
                </tr>
            </table>
            
            <p style="font-size: 15px; color: #334155; line-height: 1.6; margin: 0;">Your presence and counsel are requested. Please acknowledge your attendance in the board portal.</p>
        """
        html = get_base_template("Official Invitation", content, is_br=is_br)
        await EmailService.send_email(to_email, subject, html)

    @staticmethod
    async def send_meeting_rescheduled(to_email: str, recipient_name: str, meeting_title: str, old_date: str, old_time: str, new_date: str, new_time: str, is_br: bool = False):
        subject = f"BOARD RESOLUTION RESCHEDULED: {meeting_title}" if is_br else f"RESCHEDULED: {meeting_title}"
        intro_text = f"The Board Resolution session <strong>{meeting_title}</strong> has been rescheduled due to administrative requirements." if is_br else f"The meeting <strong>{meeting_title}</strong> has been rescheduled."
        
        content = f"""
            <p style="font-size: 16px; color: #475569; margin: 0 0 16px;">Dear {recipient_name},</p>
            <div style="background-color: #fef3c7; border-left: 4px solid #f59e0b; padding: 16px; border-radius: 4px; margin-bottom: 24px;">
                <p style="font-size: 15px; color: #92400e; margin: 0;"><strong>Important:</strong> {intro_text}</p>
            </div>
            
            <table style="width: 100%; border-collapse: collapse; margin-bottom: 24px; border: 1px solid #e2e8f0; border-radius: 6px; overflow: hidden;">
                <tr>
                    <td style="padding: 12px 16px; font-weight: 600; color: #64748b; border-bottom: 1px solid #e2e8f0; width: 120px; background-color: #f8fafc;">Previous Time</td>
                    <td style="padding: 12px 16px; color: #94a3b8; border-bottom: 1px solid #e2e8f0; text-decoration: line-through;">{old_date} at {old_time}</td>
                </tr>
                <tr>
                    <td style="padding: 12px 16px; font-weight: 600; color: #475569; border-bottom: 1px solid #e2e8f0; background-color: #fffbeb;">NEW DATE</td>
                    <td style="padding: 12px 16px; color: #0f172a; border-bottom: 1px solid #e2e8f0; font-weight: 700;">{new_date}</td>
                </tr>
                <tr>
                    <td style="padding: 12px 16px; font-weight: 600; color: #475569; background-color: #fffbeb;">NEW TIME</td>
                    <td style="padding: 12px 16px; color: #0f172a; font-weight: 700;">{new_time}</td>
                </tr>
            </table>
            
            <p style="font-size: 15px; color: #334155; line-height: 1.6; margin: 0;">Please update your official calendar. We apologize for any inconvenience.</p>
        """
        html = get_base_template("Schedule Amendment", content, is_br=is_br)
        await EmailService.send_email(to_email, subject, html)

    @staticmethod
    async def send_meeting_cancellation(to_email: str, recipient_name: str, meeting_title: str, is_br: bool = False):
        subject = f"BOARD RESOLUTION CANCELLED: {meeting_title}" if is_br else f"CANCELLED: {meeting_title}"
        intro_text = f"The Board Resolution session for <strong>{meeting_title}</strong> has been officially cancelled and the resolution will not be moved at this time." if is_br else f"Please be advised that the meeting <strong>{meeting_title}</strong> has been <strong>CANCELLED</strong>."
        
        content = f"""
            <p style="font-size: 16px; color: #475569; margin: 0 0 16px;">Dear {recipient_name},</p>
            <div style="background-color: #fee2e2; border-left: 4px solid #ef4444; padding: 16px; border-radius: 4px; margin-bottom: 24px;">
                <p style="font-size: 15px; color: #991b1b; margin: 0;">{intro_text}</p>
            </div>
            <p style="font-size: 15px; color: #334155; line-height: 1.6; margin: 0 0 24px;">The scheduled session will no longer take place. If the resolution is to be proposed again, a fresh notice will be issued.</p>
            <p style="font-size: 15px; color: #334155; line-height: 1.6; margin: 0;">You may remove this item from your corporate records.</p>
        """
        html = get_base_template("Cancellation Notice", content, is_br=is_br)
        await EmailService.send_email(to_email, subject, html)

    @staticmethod
    async def send_meeting_summary(to_email: str, recipient_name: str, meeting_title: str, is_absent: bool, summary: str, task_html: str, pdf_data: Optional[bytes] = None, pdf_name: Optional[str] = None, is_br: bool = False):
        subject = f"Official Resolution Wording & MOM: {meeting_title}" if is_br else f"MOM & Summary: {meeting_title}"
        
        if is_absent:
            greeting_box = f"""
            <div style="background-color: #fef2f2; border-left: 4px solid #ef4444; padding: 12px 16px; margin-bottom: 24px;">
                <p style="font-size: 14px; color: #991b1b; margin: 0;"><strong>Note:</strong> You were unable to attend this session. Please review the formal resolutions and mandates below.</p>
            </div>
            """
        else:
            greeting_box = f"""
            <p style="font-size: 15px; color: #334155; line-height: 1.6; margin: 0 0 24px;">Please find the formal Minutes of Meeting (MOM) and passed resolutions for your records.</p>
            """
            
        styled_task_html = task_html.replace(
            '<table border="1"', '<table style="width: 100%; border-collapse: collapse; margin-top: 12px; font-size: 14px; text-align: left;"'
        ).replace(
            '<th', '<th style="background-color: #f1f5f9; padding: 10px; border: 1px solid #cbd5e1; color: #334155;"'
        ).replace(
            '<td', '<td style="padding: 10px; border: 1px solid #e2e8f0; color: #1e293b;"'
        )
        
        attachment_notice = ""
        if pdf_data:
            attachment_notice = """
            <div style="margin-top: 24px; padding: 16px; background-color: #f0fdf4; border-left: 4px solid #22c55e; border-radius: 4px;">
                <p style="font-size: 14px; color: #166534; margin: 0;"><strong>Attached:</strong> The officially signed/formatted PDF document is attached for Board repository purposes.</p>
            </div>
            """

        discussion_label = "Resolution Summary / Wording" if is_br else "Discussion Summary"
        content = f"""
            <p style="font-size: 16px; color: #475569; margin: 0 0 16px;">Dear {recipient_name},</p>
            {greeting_box}
            
            <h3 style="color: #1e293b; font-size: 16px; margin: 0 0 12px; padding-bottom: 8px; border-bottom: 1px solid #e2e8f0;">{discussion_label}</h3>
            <div style="background-color: #f8fafc; padding: 16px; border-radius: 6px; margin-bottom: 24px; border: 1px solid #e2e8f0;">
                <p style="margin: 0; font-size: 14px; color: #334155; line-height: 1.6; white-space: pre-wrap;">{summary or 'No formal wording documented.'}</p>
            </div>
            
            <h3 style="color: #1e293b; font-size: 16px; margin: 0 0 12px; padding-bottom: 8px; border-bottom: 1px solid #e2e8f0;">Action Mandates</h3>
            {styled_task_html}
            {attachment_notice}
        """
        html = get_base_template(f"MOM Archive: {meeting_title}" if is_br else f"MOM: {meeting_title}", content, is_br=is_br)
        await EmailService.send_email(to_email, subject, html, attachment_data=pdf_data, attachment_name=pdf_name)

    @staticmethod
    async def send_cs_mom(to_email: str, meeting_title: str, pdf_data: bytes, pdf_name: str, is_br: bool = False):
        """Specially formatted email for Company Secretary."""
        subject = f"GOVERNANCE COMPLIANCE: Finalized Resolution - {meeting_title}" if is_br else f"FOR RECORDS: Finalized MOM - {meeting_title}"
        target_entity = "Board of Directors" if is_br else "HR/Management Committee"
        
        content = f"""
            <p style="font-size: 16px; color: #475569; margin: 0 0 16px;">Dear Company Secretary,</p>
            <p style="font-size: 15px; color: #334155; line-height: 1.6; margin: 0 0 24px;">
                The administrative review for <strong>{meeting_title}</strong> is now complete. 
                The attached document has been formally finalized and is now submitted for your corporate records and compliance filing.
            </p>
            <div style="background-color: #f1f5f9; border-left: 4px solid #1e293b; padding: 16px; border-radius: 4px; margin-bottom: 24px;">
                <p style="font-size: 14px; color: #1e293b; margin: 0;"><strong>Source Entity:</strong> {target_entity}</p>
                <p style="font-size: 14px; color: #1e293b; margin: 4px 0 0;"><strong>Submission Date:</strong> {datetime.now().strftime('%B %d, %Y')}</p>
            </div>
            <p style="font-size: 14px; color: #64748b; font-style: italic;">Note: This document is system-generated and has been verified by the meeting administrator.</p>
        """
        html = get_base_template("Governance Filing Submission", content, is_br=is_br)
        await EmailService.send_email(to_email, subject, html, attachment_data=pdf_data, attachment_name=pdf_name)
