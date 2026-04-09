"""Meeting CRUD endpoints + PDF generation – Google Sheets backed."""

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
import os
import logging
import io
from datetime import datetime
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib.utils import ImageReader
from reportlab.lib.enums import TA_RIGHT, TA_LEFT, TA_CENTER

# Register Noto Sans for Unicode support (Rupee ₹, etc.)
FONT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'utils')
pdfmetrics.registerFont(TTFont('NotoSans', os.path.join(FONT_DIR, 'NotoSans-Regular.ttf')))
pdfmetrics.registerFont(TTFont('NotoSans-Bold', os.path.join(FONT_DIR, 'NotoSans-Bold.ttf')))
pdfmetrics.registerFontFamily('NotoSans', normal='NotoSans', bold='NotoSans-Bold')

from app.schemas.schemas import MeetingCreate, MeetingResponse, MeetingListResponse, MeetingMOMUpdate, RescheduleMeeting, GlobalTaskResponse
from app.services.meeting_service import MeetingService
from app.services.br_meeting_service import BRService
from app.services.google_sheets_service import upload_to_drive, ensure_subfolder
from app.notifications.notification_service import NotificationService
from app.config import get_settings

settings = get_settings()

router = APIRouter()


# PDF endpoint
def draw_header_footer(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(colors.HexColor("#60a5fa"))
    canvas.rect(0, 830, 297, 12, fill=1, stroke=0)
    canvas.setFillColor(colors.HexColor("#4f46e5"))
    canvas.rect(297, 830, 298, 12, fill=1, stroke=0)

    canvas.setFillColor(colors.HexColor("#60a5fa"))
    p1 = canvas.beginPath()
    p1.moveTo(0, 0); p1.lineTo(200, 0); p1.lineTo(220, 15); p1.lineTo(0, 15); p1.close()
    canvas.drawPath(p1, stroke=0, fill=1)

    canvas.setFillColor(colors.HexColor("#4f46e5"))
    p2 = canvas.beginPath()
    p2.moveTo(200, 0); p2.lineTo(595.27, 0); p2.lineTo(595.27, 25); p2.lineTo(230, 25); p2.close()
    canvas.drawPath(p2, stroke=0, fill=1)

    logo_path = r"c:\Users\prabh\Desktop\MOM_AI_Assistant\B PNG.png"
    if os.path.exists(logo_path):
        logo = ImageReader(logo_path)
        canvas.drawImage(logo, 30, 755, width=60, height=60, preserveAspectRatio=True, mask='auto')
        canvas.setStrokeColor(colors.HexColor("#1e293b"))
        canvas.setLineWidth(1.5)
        canvas.line(100, 760, 100, 805)
        canvas.setFillColor(colors.HexColor("#000000"))
        canvas.setFont("Helvetica-Bold", 24)
        canvas.drawString(110, 785, "Botivate")
        canvas.setFont("Helvetica-Oblique", 11)
        canvas.drawString(110, 770, "Powering Businesses")
        canvas.drawString(110, 757, "On Autopilot")

    canvas.setFillColor(colors.HexColor("#1e293b"))
    canvas.setFont("NotoSans-Bold", 12)
    canvas.drawRightString(565, 790, settings.CLIENT_NAME.upper())
    canvas.setFont("NotoSans", 10)
    canvas.setFillColor(colors.HexColor("#4f46e5"))
    # Render full address with wrapping (Right Aligned)
    addr_style = ParagraphStyle('AddrStyle', fontName='NotoSans', fontSize=9, textColor=colors.HexColor("#4f46e5"), leading=11, alignment=TA_RIGHT)
    addr_p = Paragraph(settings.CLIENT_ADDRESS, addr_style)
    w, h = addr_p.wrap(250, 100) # Width of 250, max height 100
    addr_p.drawOn(canvas, 565 - w, 785 - h)

    canvas.setStrokeColor(colors.HexColor("#4f46e5"))
    canvas.setLineWidth(1.5)
    canvas.line(30, 735, 565, 735)

    canvas.setFillColor(colors.HexColor("#000000"))
    canvas.setFont("NotoSans-Bold", 12)
    canvas.drawString(30, 45, "HR Department")
    canvas.setFont("NotoSans-Bold", 10)
    canvas.setFillColor(colors.HexColor("#475569"))
    canvas.drawString(30, 32, settings.CLIENT_NAME)

    # Powered by Botivate (Watermark)
    if settings.SHOW_BOTIVATE_BRANDING:
        canvas.setFont("NotoSans", 8)
        canvas.setFillColor(colors.HexColor("#94a3b8"))
        canvas.drawRightString(A4[0] - 30, 32, settings.BOTIVATE_SIGNATURE)

    canvas.restoreState()


def generate_meeting_pdf(meeting) -> tuple:
    """Generate a Botivate-branded MOM PDF in-memory."""
    import re as _re

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=120, bottomMargin=120)

    styles = getSampleStyleSheet()
    h1_style = ParagraphStyle('BotivateH1', parent=styles['Heading1'], fontName='NotoSans-Bold', fontSize=14, textColor=colors.HexColor("#1e293b"), spaceAfter=12)
    h2_style = ParagraphStyle('BotivateH2', parent=styles['Heading2'], fontName='NotoSans-Bold', fontSize=11, textColor=colors.HexColor("#334155"), spaceAfter=8, spaceBefore=12)
    normal_style = ParagraphStyle('BotivateNormal', parent=styles['Normal'], fontName='NotoSans', fontSize=10, textColor=colors.HexColor("#475569"), leading=14, spaceAfter=6)

    table_style = TableStyle([
        ('FONTNAME', (0,0), (-1,-1), 'NotoSans'),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('TEXTCOLOR', (0,0), (-1,-1), colors.HexColor("#334155")),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#e2e8f0")),
        ('FONTNAME', (0,0), (-1,0), 'NotoSans-Bold'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
    ])

    def clean_markdown_pdf(text: str) -> str:
        """Helper to convert **bold** to <b>bold</b> for ReportLab."""
        import re as _re
        if not text: return ""
        # Handle **bold** (Robust regex)
        text = _re.sub(r"\*\*\s*(.*?)\s*\*\*", r"<b>\1</b>", text)
        # Strip stray markdown symbols
        text = text.replace('###', '').replace('##', '').replace('# ', '')
        # Basic character cleanup (emojis/boxes that cause errors in Helvetica)
        text = _re.sub(r'[^\x00-\x7F\u0900-\u097F₹\u2022\s]', '', text)
        return text.strip()

    elements = []

    # Determine Document Title and Prefix
    is_br = getattr(meeting, 'meeting_type', '') == "Board Resolution"
    doc_code = f"BR-{meeting.id:03d}" if is_br else f"MOM-{meeting.id:03d}"
    
    elements.append(Paragraph(f"<b>{doc_code}</b>", h1_style))
    elements.append(Paragraph(f"<b>Subject:</b> {meeting.title}", normal_style))
    elements.append(Spacer(1, 10))
    elements.append(Paragraph(f"<b>Dear Team,</b>", normal_style))
    elements.append(Paragraph(
        f"Please find the details and minutes of the <b>{doc_code}</b> entitled <b>{meeting.title}</b> held on "
        f"<b>{meeting.date}</b> at <b>{meeting.time}</b> below:", normal_style))
    elements.append(Spacer(1, 10))

    org_name = meeting.organization or settings.CLIENT_NAME
    elements.append(Paragraph(f"• <b>Organization:</b> {org_name}", normal_style))
    pdf_meeting_type = meeting.meeting_type if meeting.meeting_type else ("Board Resolution" if is_br else "Regular Meeting")
    elements.append(Paragraph(f"• <b>Meeting Type:</b> {pdf_meeting_type}", normal_style))
    elements.append(Paragraph(f"• <b>Meeting Mode:</b> {getattr(meeting, 'meeting_mode', 'N/A') or 'N/A'}", normal_style))
    elements.append(Paragraph(f"• <b>Venue/Location:</b> {meeting.venue or 'N/A'}", normal_style))
    elements.append(Paragraph(f"• <b>Hosted By:</b> {getattr(meeting, 'hosted_by', 'N/A') or 'N/A'}", normal_style))
    elements.append(Spacer(1, 10))

    # Next Meeting
    if meeting.next_meeting and (meeting.next_meeting.next_date or meeting.next_meeting.next_time):
        elements.append(Paragraph("<b>Schedule for Next Meeting</b>", h2_style))
        nd = meeting.next_meeting.next_date.strftime('%B %d, %Y') if hasattr(meeting.next_meeting.next_date, 'strftime') and meeting.next_meeting.next_date else str(meeting.next_meeting.next_date or 'TBD')
        nt = meeting.next_meeting.next_time.strftime('%I:%M %p') if hasattr(meeting.next_meeting.next_time, 'strftime') and meeting.next_meeting.next_time else str(meeting.next_meeting.next_time or 'TBD')
        elements.append(Paragraph(f"• <b>Date:</b> {nd}", normal_style))
        elements.append(Paragraph(f"• <b>Time:</b> {nt}", normal_style))
        elements.append(Spacer(1, 15))

    # Attendees
    elements.append(Paragraph("<b>Attendance</b>", h2_style))
    attendees_data = [["Name", "Email", "Status"]]
    for a in meeting.attendees:
        st = str(a.attendance_status).split('.')[-1].capitalize() if 'AttendanceStatus' in str(a.attendance_status) else str(a.attendance_status).capitalize()
        attendees_data.append([a.user_name, a.email or "N/A", st])
    if len(attendees_data) > 1:
        att_table = Table(attendees_data, colWidths=[180, 200, 100], hAlign='LEFT')
        att_table.setStyle(table_style)
        elements.append(att_table)
    else:
        elements.append(Paragraph("No attendees recorded.", normal_style))
    elements.append(Spacer(1, 10))

    # Agenda
    elements.append(Paragraph("<b>Agenda Items</b>", h2_style))
    if meeting.agenda_items:
        for idx, item in enumerate(meeting.agenda_items, 1):
            desc = f" - {item.description}" if item.description else ""
            elements.append(Paragraph(f"{idx}. {item.topic}{desc}", normal_style))
    else:
        elements.append(Paragraph("No agenda items.", normal_style))
    elements.append(Spacer(1, 10))

    # Discussion
    elements.append(Paragraph("<b>Discussion Summary</b>", h2_style))
    if meeting.discussion and meeting.discussion.summary_text:
        for point in meeting.discussion.summary_text.split('\n'):
            if point.strip():
                elements.append(Paragraph(clean_markdown_pdf(point.strip()), normal_style))
    else:
        elements.append(Paragraph("No discussion summary recorded.", normal_style))
    elements.append(Spacer(1, 10))

    # Tasks
    elements.append(Paragraph("<b>Action Items / Tasks</b>", h2_style))
    action_items_data = [["Task", "Responsible", "Deadline", "Status"]]
    for t in meeting.tasks:
        st = str(t.status).split('.')[-1].capitalize() if 'TaskStatus' in str(t.status) else str(t.status).capitalize()
        dl = t.deadline.strftime('%d-%m-%Y') if hasattr(t.deadline, 'strftime') and t.deadline else str(t.deadline or 'N/A')
        action_items_data.append([Paragraph(t.title, normal_style), t.responsible_person or "N/A", dl, st])
    if len(action_items_data) > 1:
        task_table = Table(action_items_data, colWidths=[200, 130, 80, 70], hAlign='LEFT')
        task_table.setStyle(table_style)
        elements.append(task_table)
    else:
        elements.append(Paragraph("No action items recorded.", normal_style))
    elements.append(Spacer(1, 15))

    doc.build(elements, onFirstPage=draw_header_footer, onLaterPages=draw_header_footer)
    pdf_bytes = buffer.getvalue()
    buffer.close()

    safe_date = str(meeting.date).replace('-', '') if meeting.date else 'NoDate'
    safe_time = str(meeting.time).replace(':', '') if meeting.time else 'NoTime'
    
    prefix_code = "BR" if is_br else "MOM"
    pdf_filename = f"{prefix_code}_{meeting.id}_{safe_date}_{safe_time}.pdf"
    
    return pdf_bytes, pdf_filename


@router.get("/{meeting_id}/pdf", response_class=StreamingResponse)
async def download_meeting_pdf(meeting_id: int):
    try:
        meeting = await MeetingService.get_meeting(None, meeting_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal error during meeting retrieval")
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    pdf_bytes, pdf_filename = generate_meeting_pdf(meeting)

    # Upload PDF to Google Drive and update the sheet
    try:
        folder_name = f"{meeting.id} - {meeting.title} - {meeting.date} {meeting.time}"
        root_id = ensure_subfolder("Meetings", parent_id=settings.DRIVE_FOLDER_ID)
        meeting_folder_id = ensure_subfolder(folder_name, parent_id=root_id)
        
        drive_result = upload_to_drive(
            pdf_bytes, pdf_filename, 
            subfolder_name=folder_name, 
            parent_id=root_id
        )
        await MeetingService.update_meeting_pdf_link(
            meeting_id,
            pdf_link=drive_result.get("webViewLink", ""),
            drive_file_id=drive_result.get("id", ""),
            drive_folder_id=meeting_folder_id
        )
    except Exception as e:
        logging.getLogger("meetings_api").error("Drive upload failed: %s", e)

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={pdf_filename}"}
    )


@router.post("/", response_model=MeetingResponse, status_code=status.HTTP_201_CREATED)
async def create_meeting(data: MeetingCreate):
    """Create a meeting manually (Manual MOM creation)."""
    logger = logging.getLogger("meeting_creation")
    logger.info("Received meeting creation payload: %s", data.dict())
    try:
        meeting = await MeetingService.create_meeting(None, data, created_by=None)
        logger.info("Meeting created successfully: id=%s", meeting.id)
    except Exception as e:
        logger.error("Meeting creation failed: %s", str(e))
        raise

    # Send notifications
    is_rescheduled_invite = str(getattr(meeting, "status", "")).strip().lower() == "rescheduled"
    for attendee in meeting.attendees:
        if attendee.email:
            await NotificationService.notify_meeting_invitation(
                None, email=attendee.email, user_name=attendee.user_name,
                meeting_title=meeting.title,
                date=str(meeting.date) if meeting.date else "TBD",
                time=str(meeting.time) if meeting.time else "TBD",
                venue=meeting.venue or "TBD",
                remarks=getattr(attendee, "remarks", None),
                is_rescheduled=is_rescheduled_invite,
            )

    for task in meeting.tasks:
        await NotificationService.notify_task_assigned(None, task, meeting.title)

    return meeting


@router.post("/{meeting_id}/mom", response_model=MeetingResponse)
async def add_mom_to_meeting(meeting_id: int, data: MeetingMOMUpdate):
    """Add MOM data to an existing scheduled meeting."""
    meeting = await MeetingService.add_mom_to_meeting(None, meeting_id, data)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    # Generate PDF
    pdf_data, pdf_name = generate_meeting_pdf(meeting)

    # Upload to Drive
    try:
        folder_name = f"{meeting.id} - {meeting.title} - {meeting.date} {meeting.time}"
        root_id = ensure_subfolder("Meetings", parent_id=settings.DRIVE_FOLDER_ID)
        meeting_folder_id = ensure_subfolder(folder_name, parent_id=root_id)
        
        drive_result = upload_to_drive(
            pdf_data, pdf_name, 
            subfolder_name=folder_name, 
            parent_id=root_id
        )
        await MeetingService.update_meeting_pdf_link(
            meeting_id,
            pdf_link=drive_result.get("webViewLink", ""),
            drive_file_id=drive_result.get("id", ""),
            drive_folder_id=meeting_folder_id
        )
    except Exception as e:
        logging.getLogger("meetings_api").error("Drive upload failed: %s", e)

    # Task HTML for email
    task_html = ""
    if meeting.tasks:
        task_html = "<table style='border-collapse:collapse;width:100%;margin:16px 0;'><tr style='background:#f0f4f8;'><th style='padding:10px;text-align:left;'>Task</th><th style='padding:10px;text-align:left;'>Owner</th><th style='padding:10px;text-align:left;'>Deadline</th></tr>"
        for t in meeting.tasks:
            task_html += f"<tr><td style='padding:10px;border-bottom:1px solid #e0e0e0;'>{t.title}</td><td style='padding:10px;border-bottom:1px solid #e0e0e0;'>{t.responsible_person or 'None'}</td><td style='padding:10px;border-bottom:1px solid #e0e0e0;'>{t.deadline or 'None'}</td></tr>"
        task_html += "</table>"
    else:
        task_html = "<p>No tasks assigned.</p>"

    # Send notifications
    for attendee in meeting.attendees:
        if attendee.email:
            is_absent = (str(attendee.attendance_status).strip() != "Present")
            await NotificationService.notify_meeting_summary(
                None, email=attendee.email, user_name=attendee.user_name,
                meeting_title=meeting.title, is_absent=is_absent,
                summary=meeting.discussion.summary_text if meeting.discussion else "",
                task_html=task_html, pdf_data=pdf_data, pdf_name=pdf_name,
                pdf_link=drive_result.get("webViewLink", "")
            )

    # Notify task assignees
    if meeting.tasks:
        for db_task in meeting.tasks:
            if getattr(db_task, "responsible_email", None):
                await NotificationService.notify_task_assigned(None, db_task, meeting.title)

    return meeting


@router.get("/", response_model=list[MeetingListResponse])
async def list_meetings(skip: int = 0, limit: int = 50):
    meetings = await MeetingService.list_meetings(None, skip=skip, limit=limit)
    return [
        MeetingListResponse(
            id=m.id, title=m.title, organization=m.organization,
            date=m.date, time=m.time, venue=m.venue,
            created_at=m.created_at,
            task_count=len(m.tasks) if hasattr(m, 'tasks') and m.tasks else 0,
            pending_tasks=len([t for t in m.tasks if str(t.status).split('.')[-1] == 'PENDING' or str(t.status) == 'Pending']) if hasattr(m, 'tasks') and m.tasks else 0,
            in_progress_tasks=len([t for t in m.tasks if str(t.status).split('.')[-1] == 'IN_PROGRESS' or str(t.status) == 'In Progress']) if hasattr(m, 'tasks') and m.tasks else 0,
            completed_tasks=len([t for t in m.tasks if str(t.status).split('.')[-1] == 'COMPLETED' or str(t.status) == 'Completed']) if hasattr(m, 'tasks') and m.tasks else 0,
            status=m.status if hasattr(m, 'status') else "Scheduled",
            sent_to_cs=m.sent_to_cs if hasattr(m, 'sent_to_cs') else False
        )
        for m in meetings
    ]

@router.post("/{meeting_id}/cancel")
async def cancel_meeting(meeting_id: int):
    meeting = await MeetingService.get_meeting(None, meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
        
    await MeetingService.cancel_meeting(meeting_id)
    
    # Notify attendees
    for attendee in meeting.attendees:
        if attendee.email:
            await NotificationService.notify_meeting_cancellation(
                None, email=attendee.email, user_name=attendee.user_name, meeting_title=meeting.title
            )
            
    return {"detail": "Meeting cancelled"}

@router.post("/{meeting_id}/reschedule")
async def reschedule_meeting(meeting_id: int, data: RescheduleMeeting):
    meeting = await MeetingService.get_meeting(None, meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
        
    old_date = str(meeting.date)
    old_time = str(meeting.time)
    
    await MeetingService.reschedule_meeting(meeting_id, data.date, data.time)
    
    # Notify attendees
    for attendee in meeting.attendees:
        if attendee.email:
            await NotificationService.notify_meeting_rescheduled(
                None, email=attendee.email, user_name=attendee.user_name, 
                meeting_title=meeting.title,
                old_date=old_date, old_time=old_time,
                new_date=str(data.date), new_time=str(data.time)
            )
            
    return {"detail": "Meeting rescheduled"}


@router.get("/{meeting_id}", response_model=MeetingResponse)
async def get_meeting(meeting_id: int):
    meeting = await MeetingService.get_meeting(None, meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return meeting


@router.delete("/{meeting_id}")
async def delete_meeting(meeting_id: int):
    deleted = await MeetingService.delete_meeting(None, meeting_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return {"detail": "Meeting deleted"}

@router.get("/global/tasks", response_model=list[GlobalTaskResponse])
async def get_global_tasks():
    """Retrieve every action item across both Regular and BR meetings."""
    regular_tasks = await MeetingService.get_all_tasks()
    br_tasks = await BRService.get_all_tasks()
    
    # Combine and Sort by created_at descending
    combined = regular_tasks + br_tasks
    combined.sort(key=lambda x: x.created_at if hasattr(x, 'created_at') and x.created_at else datetime.min, reverse=True)
    return combined
