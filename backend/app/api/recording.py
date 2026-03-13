from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
import os
import shutil
import uuid
import logging
from app.services.ai_service import AIService
from app.services.google_sheets_service import upload_to_drive, SheetsDB, ensure_subfolder
from app.services.br_meeting_service import BRService
from app.services.meeting_service import MeetingService
from app.notifications.notification_service import NotificationService
from app.utils.pdf_generator import generate_any_pdf, generate_transcript_pdf, generate_audit_log_pdf, generate_summary_pdf
from app.config import get_settings

router = APIRouter()
logger = logging.getLogger("recording_api")
settings = get_settings()

@router.post("/process")
async def process_meeting_recording(
    background_tasks: BackgroundTasks,
    meeting_id: int = Form(...),
    meeting_type: str = Form(...), # "Regular" or "BR"
    audio_file: UploadFile = File(...)
):
    """
    Accepts a complete meeting recording file, saves it to Drive,
    and triggers local AI transcription and summarization in the background.
    """
    logger.info(f"Received request to process recording: MeetingID={meeting_id}, Type={meeting_type}, Filename={audio_file.filename}")
    
    # 1. Save temporary locally
    temp_dir = "temp_recordings"
    os.makedirs(temp_dir, exist_ok=True)
    temp_path = os.path.join(temp_dir, f"{uuid.uuid4()}_{audio_file.filename}")
    
    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(audio_file.file, buffer)
        logger.info(f"Temporary file saved to: {temp_path}")
    except Exception as e:
        logger.error(f"Failed to save temporary audio file: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save audio: {e}")

    # 2. Identify meeting and its Drive folder
    try:
        if meeting_type == "BR":
            meeting = await BRService.get_br(None, meeting_id)
            parent_root = "BR Meetings"
        else:
            meeting = await MeetingService.get_meeting(None, meeting_id)
            parent_root = "Meetings"
    except Exception as e:
        logger.error(f"Database error while fetching meeting {meeting_id}: {e}")
        if os.path.exists(temp_path): os.remove(temp_path)
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

    if not meeting:
        logger.warning(f"Meeting not found: ID={meeting_id}, Type={meeting_type}")
        if os.path.exists(temp_path): os.remove(temp_path)
        raise HTTPException(status_code=404, detail="Meeting not found")

    # Access drive_folder_id safely (ensures MeetingService mapping is correct)
    dfid = getattr(meeting, 'drive_folder_id', None)
    logger.info(f"Fetched meeting data. Title='{meeting.title}', DriveFolderID='{dfid}'")

    # Start background task for AI processing
    background_tasks.add_task(
        run_ai_pipeline,
        meeting_id,
        meeting_type,
        temp_path,
        meeting.title,
        str(meeting.date),
        str(meeting.time),
        dfid,
        parent_root
    )
    
    logger.info(f"AI Pipeline triggered in background for meeting {meeting_id}")
    return {"status": "Processing started", "detail": "Audio uploaded and AI pipeline triggered."}

async def run_ai_pipeline(mid, mtype, path, title, mdate, mtime, folder_id, parent_root):
    try:
        logger.info(f">>> STARTING AI PIPELINE for '{title}' (Meeting ID: {mid})")
        
        # 1. Local Transcription (Whisper)
        logger.info(f"[STAGE 1/6] Starting local transcription using Faster-Whisper...")
        transcript_text = await AIService.transcribe_audio(path)
        logger.info(f"[STAGE 1/6] Transcription complete. Length: {len(transcript_text.split())} words.")
        
        # 2. Local Summarization (FLAN-T5) with Chunk Logs
        logger.info(f"[STAGE 2/6] Starting local hierarchical summarization...")
        ai_results = await AIService.summarize_transcript(transcript_text)
        logger.info(f"[STAGE 2/6] Summarization complete.")
        
        # 3. Prepare 4 separate PDF files for Drive
        logger.info(f"[STAGE 3/6] Packaging Intelligence Assets (4 PDFs)...")
        
        # PDF 1: Full Verbatim Transcript (🎤 Monospace Line-Numbered Layout)
        transcript_filename = f"Transcript_{title}_{mdate}.pdf"
        transcript_pdf = generate_transcript_pdf(title, mdate, transcript_text)

        # PDF 2: AI Auditing Logs (🔍 Segmented Process Trail)
        chunks_filename = f"AI_Auditing_Logs_{title}_{mdate}.pdf"
        chunks_pdf = generate_audit_log_pdf(title, mdate, ai_results['chunk_summaries'])

        # PDF 3: Professional MOM Report (📋 Standard Botivate Branded)
        mom_filename = f"MOM_Professional_Report_{title}_{mdate}.pdf"
        mom_pdf = generate_any_pdf(f"Minutes of Meeting: {title}", f"Date: {mdate} | Time: {mtime}", ai_results['final_summary'])

        # PDF 4: Executive Summary Briefing (📊 Green-Accented Narrative)
        formatted_filename = f"Final_Formatted_Summary_{title}_{mdate}.pdf"
        formatted_pdf = generate_summary_pdf(title, mdate, ai_results['formatted_summary'])
        
        # 4. Upload all 4 PDFs to Drive
        logger.info(f"[STAGE 4/6] Uploading 4 PDFs directly to meeting folder...")
        root_folder_id = ensure_subfolder(parent_root, parent_id="0AAgyfuup7OPSUk9PVA")
        
        if not folder_id:
            folder_name = f"{mid} - {title} - {mdate} {mtime}"
            folder_id = ensure_subfolder(folder_name, parent_id=root_folder_id)

        # Uploads directly to folder_id (Removing Intelligence Reports subfolder)
        res_t = upload_to_drive(transcript_pdf, transcript_filename, "application/pdf", folder_id)
        res_a = upload_to_drive(chunks_pdf, chunks_filename, "application/pdf", folder_id)
        res_f = upload_to_drive(formatted_pdf, formatted_filename, "application/pdf", folder_id)
        
        transcript_link = res_t.get("webViewLink")
        logs_link = res_a.get("webViewLink")
        formatted_link = res_f.get("webViewLink")
        
        # Main professional report is the one linked to UI
        drive_res = upload_to_drive(mom_pdf, mom_filename, "application/pdf", folder_id)
        report_link = drive_res.get("webViewLink")
        
        logger.info(f"[STAGE 4/6] 4 PDFs Uploaded. Primary Report: {report_link}")
        
        # 5. Update Sheet with all 4 Asset Links (Keep as Processing, NOT Completed)
        logger.info(f"[STAGE 5/6] Syncing all 4 intelligence links and marking as Processing...")
        update_data = {
            "recording_link": report_link,         # Professional MOM PDF
            "ai_summary_link": formatted_link,     # Formatted Narrative Summary PDF
            "drive_transcript_id": transcript_link,# Verbatim Transcript PDF
            "drive_logs_link": logs_link,          # AI Audit Logs PDF
            "drive_recording_id": drive_res.get("id"),
            "drive_folder_id": folder_id,
            "status": "Processing"                 # <--- STAY IN PROCESSING UNTIL ADMIN SAVES MOM
        }
        if mtype == "BR":
            SheetsDB.update_row("BR_Meetings", mid, update_data)
        else:
            SheetsDB.update_row("Meetings", mid, update_data)

        # Stage 6: Populate Discussion Summary
        logger.info(f"[STAGE 6/6] Syncing intelligence assets...")
        
        # Dashboard Autofill: Use the point-wise brief summary
        discussion_update = {"summary_text": ai_results['brief_summary']}
        if mtype == "BR":
            existing = SheetsDB.get_by_field("BR_Discussions", "meeting_id", mid)
            if existing: 
                SheetsDB.update_row("BR_Discussions", int(existing[0]['id']), discussion_update)
            else: 
                SheetsDB.append_row("BR_Discussions", {"meeting_id": mid, "summary_text": ai_results['brief_summary']})
        else:
            existing = SheetsDB.get_by_field("Discussions", "meeting_id", mid)
            if existing: 
                SheetsDB.update_row("Discussions", int(existing[0]['id']), discussion_update)
            else: 
                SheetsDB.append_row("Discussions", {"meeting_id": mid, "summary_text": ai_results['brief_summary']})

        logger.info(f"✨ AI PIPELINE FULLY COMPLETED FOR '{title}' (ID: {mid})")
        
    except Exception as e:
        logger.error(f"!!! CRITICAL: AI Pipeline failed for meeting {mid}: {e}", exc_info=True)
    finally:
        if os.path.exists(path):
            os.remove(path)
            logger.info(f"Cleaned up temporary file: {path}")
