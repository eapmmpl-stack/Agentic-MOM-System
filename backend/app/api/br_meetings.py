"""Board Resolution (BR) API endpoints."""

from fastapi import APIRouter, HTTPException, status, UploadFile, File, Form
from fastapi.responses import StreamingResponse
import io
import logging
import json
from pathlib import Path
from datetime import datetime
from typing import List

from app.schemas.schemas import MeetingCreate, MeetingResponse, MeetingListResponse, MeetingMOMUpdate, ExtractedMOM, RescheduleMeeting, TaskUpdate, SendCSRequest
from app.services.br_meeting_service import BRService
from app.services.google_sheets_service import upload_to_drive, SheetsDB, ensure_subfolder
from app.api.meetings import generate_meeting_pdf
from app.services.file_service import FileService
from app.workflows.mom_workflow import get_mom_workflow
from app.notifications.notification_service import NotificationService
from app.config import get_settings

router = APIRouter()
logger = logging.getLogger("br_api")
settings = get_settings()

@router.get("/", response_model=list[MeetingListResponse])
async def list_br_meetings(skip: int = 0, limit: int = 100):
    meetings = await BRService.list_brs(None, skip, limit)
    return [
        MeetingListResponse(
            id=m.id, 
            title=m.title, 
            organization=m.organization,
            date=m.date, 
            time=m.time, 
            venue=m.venue,
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

@router.post("/", response_model=MeetingResponse, status_code=status.HTTP_201_CREATED)
async def create_br_meeting(data: MeetingCreate):
    br = await BRService.create_br(None, data)
    is_rescheduled_invite = str(getattr(br, "status", "")).strip().lower() == "rescheduled"
    
    # Notify directors
    for attendee in br.attendees:
        if attendee.email:
            await NotificationService.notify_meeting_invitation(
                None, email=attendee.email, user_name=attendee.user_name,
                meeting_title=br.title,
                date=str(br.date) if br.date else "TBD",
                time=str(br.time) if br.time else "TBD",
                venue=br.venue or "TBD",
                remarks=getattr(attendee, "remarks", None),
                is_br=True,
                is_rescheduled=is_rescheduled_invite,
            )
    return br

@router.get("/{br_id}", response_model=MeetingResponse)
async def get_br_details(br_id: int):
    br = await BRService.get_br(None, br_id)
    if not br:
        raise HTTPException(status_code=404, detail="Board Resolution not found")
    return br

@router.get("/{br_id}/pdf")
async def download_br_pdf(br_id: int):
    """Generate and download the Board Resolution PDF."""
    br = await BRService.get_br(None, br_id)
    if not br:
        raise HTTPException(status_code=404, detail="Board Resolution not found")
    
    pdf_bytes, pdf_filename = generate_meeting_pdf(br)
    
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={pdf_filename}"}
    )

@router.delete("/{br_id}", status_code=status.HTTP_200_OK)
async def delete_br_meeting(br_id: int):
    success = await BRService.delete_br(None, br_id)
    if not success:
        raise HTTPException(status_code=404, detail="Board Resolution not found")
    return {"message": "Board Resolution deleted successfully"}

@router.post("/{br_id}/mom", response_model=MeetingResponse)
async def update_br_with_resolution(
    br_id: int, 
    data_str: str = Form(...), 
    files: List[UploadFile] = File(None)
):
    """Save resolution details, generate formal PDF, and upload supporting documents."""
    try:
        # Parse JSON data from form field
        parsed_data = json.loads(data_str)
        data = MeetingMOMUpdate(**parsed_data)

        # Add MOM and basic updates to DB
        br = await BRService.add_mom_to_br(None, br_id, data)
        if not br:
            raise HTTPException(status_code=404, detail="Board Resolution not found")
        
        # Create/Ensure meeting-specific folder on Drive with Descriptive name
        # Format: [ID] - [Title] - [Date] [Time]
        meeting_date = str(br.date) if br.date else "NoDate"
        meeting_time = str(br.time).replace(":", "") if br.time else "NoTime"
        folder_name = f"{br_id} - {br.title} - {meeting_date} {meeting_time}"
        
        # Root logic: Ensure 'BR Meetings' exists inside AI MOM Storage
        br_root_id = ensure_subfolder("BR Meetings", parent_id=settings.DRIVE_FOLDER_ID)
        meeting_folder_id = ensure_subfolder(folder_name, parent_id=br_root_id) 

        # Process manually uploaded files and send to DRIVE
        if files:
            now = datetime.utcnow().isoformat()
            for file in files:
                content = await file.read()
                ext = Path(file.filename).suffix.lower().replace(".", "")
                
                # Upload to Drive in the specific folder inside 'BR Meetings'
                drive_file = upload_to_drive(
                    content, 
                    file.filename, 
                    mimetype=file.content_type or "application/octet-stream", 
                    subfolder_name=folder_name,
                    parent_id=br_root_id
                )

                # Save metadata to BR_Files sheet with Drive Link
                SheetsDB.append_row("BR_Files", {
                    "meeting_id": br_id,
                    "file_path": drive_file.get("webViewLink", ""),
                    "file_type": ext,
                    "uploaded_at": now,
                    "drive_file_id": drive_file.get("id")
                })

        # Generate and Upload Final Resolution PDF to the SAME folder
        pdf_bytes, pdf_name = generate_meeting_pdf(br)
        drive_result = upload_to_drive(pdf_bytes, pdf_name, subfolder_name=folder_name, parent_id=br_root_id)
        await BRService.update_br_pdf_link(
            br_id,
            pdf_link=drive_result.get("webViewLink", ""),
            drive_file_id=drive_result.get("id", ""),
            drive_folder_id=meeting_folder_id
        )
        
        # Refresh BR object with new data
        br = await BRService.get_br(None, br_id)
        
        # Send notifications
        task_html = ""
        if br.tasks:
            task_html = "<table style='border-collapse:collapse;width:100%;margin:16px 0;'><tr style='background:#fef3c7;'><th style='padding:10px;text-align:left;'>Action Item</th><th style='padding:10px;text-align:left;'>Owner</th><th style='padding:10px;text-align:left;'>Deadline</th></tr>"
            for t in br.tasks:
                task_html += f"<tr><td style='padding:10px;border-bottom:1px solid #e0e0e0;'>{t.title}</td><td style='padding:10px;border-bottom:1px solid #e0e0e0;'>{t.responsible_person or 'None'}</td><td style='padding:10px;border-bottom:1px solid #e0e0e0;'>{t.deadline or 'None'}</td></tr>"
            task_html += "</table>"
        else:
            task_html = "<p>No action items assigned.</p>"

        for attendee in br.attendees:
            if attendee.email:
                is_absent = (str(attendee.attendance_status).strip() != "Present")
                await NotificationService.notify_meeting_summary(
                    None, email=attendee.email, user_name=attendee.user_name,
                    meeting_title=br.title, is_absent=is_absent,
                    summary=br.discussion.summary_text if br.discussion else "",
                    task_html=task_html, pdf_data=pdf_bytes, pdf_name=pdf_name,
                    is_br=True, pdf_link=drive_result.get("webViewLink", "")
                )
        
        # Notify task assignees
        if br.tasks:
            for db_task in br.tasks:
                if getattr(db_task, "responsible_email", None):
                    await NotificationService.notify_task_assigned(None, db_task, br.title, is_br=True)

        return br
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Drive upload or notification failed for BR: %s", e)
        # If we have the BR, we still try to return it
        try:
            return await BRService.get_br(None, br_id)
        except:
            raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload", response_model=MeetingResponse)
async def upload_br_resolution(file: UploadFile = File(...)):
    """Upload a Board Resolution for AI Extraction."""
    ext = Path(file.filename).suffix.lower()
    content = await file.read()
    file_path = await FileService.save_upload(content, file.filename)

    try:
        workflow = get_mom_workflow()
        result = await workflow.ainvoke({"file_path": file_path})
        
        if result.get("error"):
            raise HTTPException(status_code=422, detail=result["error"])

        extracted_mom: ExtractedMOM = result.get("extracted_mom")
        if not extracted_mom:
            raise HTTPException(status_code=422, detail="AI extraction returned no data")
            
        # Override type to ensure it's categorized as BR
        extracted_mom.meeting_type = "Board Resolution"
        
        # Save to BR Sheets
        br = await BRService.create_br_from_extraction(
            None, extracted_mom, file_path=file_path
        )
        
        # Create/Ensure nested folder architecture
        meeting_date = str(br.date) if br.date else "NoDate"
        meeting_time = str(br.time).replace(":", "") if br.time else "NoTime"
        folder_name = f"{br.id} - {br.title} - {meeting_date} {meeting_time}"

        # Root logic: Ensure 'BR Meetings' exists inside AI MOM Storage
        br_root_id = ensure_subfolder("BR Meetings", parent_id=settings.DRIVE_FOLDER_ID)
        meeting_folder_id = ensure_subfolder(folder_name, parent_id=br_root_id)
        
        # MUST generate PDF first
        pdf_bytes, pdf_name = generate_meeting_pdf(br)

        # Upload to the specific meeting folder inside BR Meetings
        drive_result = upload_to_drive(
            file_bytes=pdf_bytes,
            filename=pdf_name,
            mimetype="application/pdf",
            subfolder_name=folder_name,
            parent_id=br_root_id
        )
        
        # Update link
        if drive_result.get("webViewLink"):
            await BRService.update_br_pdf_link(
                br.id,
                pdf_link=drive_result.get("webViewLink"),
                drive_file_id=drive_result.get("id"),
                drive_folder_id=meeting_folder_id
            )
            return await BRService.get_br(None, br.id)
            
        return br
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("BR Upload pipeline failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Processing pipeline failed: {str(e)}")

@router.post("/{br_id}/cancel")
async def cancel_br_meeting(br_id: int):
    br = await BRService.get_br(None, br_id)
    if not br:
        raise HTTPException(status_code=404, detail="Board Resolution not found")
        
    await BRService.cancel_br(br_id)
    
    # Notify directors
    for attendee in br.attendees:
        if attendee.email:
            await NotificationService.notify_meeting_cancellation(
                None, email=attendee.email, user_name=attendee.user_name, meeting_title=br.title, is_br=True
            )
            
    return {"detail": "Board Resolution cancelled"}

@router.post("/{br_id}/reschedule")
async def reschedule_br_meeting(br_id: int, data: RescheduleMeeting):
    br = await BRService.get_br(None, br_id)
    if not br:
        raise HTTPException(status_code=404, detail="Board Resolution not found")
        
    old_date = str(br.date)
    old_time = str(br.time)

    await BRService.reschedule_br(br_id, data.date, data.time)
    
    # Notify directors
    for attendee in br.attendees:
        if attendee.email:
            await NotificationService.notify_meeting_rescheduled(
                None, email=attendee.email, user_name=attendee.user_name, 
                meeting_title=br.title,
                old_date=old_date, old_time=old_time,
                new_date=str(data.date), new_time=str(data.time),
                is_br=True
            )
            
    return {"detail": "Board Resolution rescheduled"}

@router.put("/tasks/{task_id}")
async def update_br_task_status(task_id: int, data: TaskUpdate):
    updated = await BRService.update_br_task(task_id, data.status)
    if not updated:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"detail": "Task status updated"}

@router.post("/{br_id}/send-to-cs")
async def send_br_to_cs(br_id: int, data: SendCSRequest):
    from app.config import get_settings
    settings = get_settings()
    
    br = await BRService.get_br(None, br_id)
    if not br:
        raise HTTPException(status_code=404, detail="Board Resolution not found")
    
    target_email = data.email or settings.CLIENT_CS_EMAIL
    if not target_email:
        raise HTTPException(status_code=400, detail="No CS email provided and no default configured")

    # Generate current PDF
    pdf_bytes, pdf_filename = generate_meeting_pdf(br)
    
    await NotificationService.notify_cs_mom(
        None, 
        email=target_email, 
        meeting_title=br.title, 
        pdf_data=pdf_bytes, 
        pdf_name=pdf_filename,
        is_br=True,
        pdf_link=br.pdf_link
    )
    
    # Mark as sent in DB
    await BRService.mark_sent_to_cs(br_id)
    
    return {"detail": f"Resolution sent to CS at {target_email}"}
