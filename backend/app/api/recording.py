from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
import os
import shutil
import uuid
import logging
import threading
from datetime import datetime
from pydantic import BaseModel

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

# Stage definitions for progress tracking
PIPELINE_STAGES = {
    "uploading": {"step": 1, "total": 6, "label": "Uploading audio..."},
    "transcribing": {"step": 2, "total": 6, "label": "Transcribing audio with AI..."},
    "summarizing": {"step": 3, "total": 6, "label": "Generating AI summary..."},
    "generating_pdfs": {"step": 4, "total": 6, "label": "Creating intelligence reports..."},
    "uploading_assets": {"step": 5, "total": 6, "label": "Uploading assets to Drive..."},
    "finalizing": {"step": 6, "total": 6, "label": "Finalizing & syncing data..."},
    "completed": {"step": 6, "total": 6, "label": "Processing Complete"},
    "failed": {"step": 0, "total": 6, "label": "Processing failed."},
}

pipeline_tracker: dict = {}

def _update_stage(mid: int, mtype: str, stage: str):
    """Update processing_stage on the meeting row for frontend polling."""
    tracker_key = f"{mtype}_{mid}"
    pipeline_tracker[tracker_key] = stage

    sheet = "BR_Meetings" if mtype == "BR" else "Meetings"
    SheetsDB.update_row(sheet, mid, {"processing_stage": stage})
    logger.info(f"[PIPELINE] Stage updated -> {stage} for meeting {mid}")

@router.get("/status/{meeting_id}")
async def get_processing_status(meeting_id: int, meeting_type: str = "Regular"):
    """Returns the current processing stage of a meeting's AI pipeline."""
    tracker_key = f"{meeting_type}_{meeting_id}"
    sheet = "BR_Meetings" if meeting_type == "BR" else "Meetings"
    m = SheetsDB.get_by_id(sheet, meeting_id)
    if not m:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    # Overwrite with real-time memory tracker if available to prevent Sheets DB lag
    stage_key = pipeline_tracker.get(tracker_key) or m.get("processing_stage", "")
    stage_info = PIPELINE_STAGES.get(stage_key, {"step": 0, "total": 6, "label": "Waiting..."})
    
    return {
        "meeting_id": meeting_id,
        "stage": stage_key,
        "step": stage_info["step"],
        "total": stage_info["total"],
        "label": stage_info["label"],
        "status": m.get("status", "Scheduled"),
        "error": m.get("processing_error", ""),
    }

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

    # Mark upload stage
    _update_stage(meeting_id, meeting_type, "uploading")

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
        _update_stage(mid, mtype, "transcribing")
        logger.info(f"[STAGE 1/6] Starting local transcription using Faster-Whisper...")
        transcript_text = await AIService.transcribe_audio(path)
        logger.info(f"[STAGE 1/6] Transcription complete. Length: {len(transcript_text.split())} words.")
        
        # 2. Local Summarization (FLAN-T5) with Chunk Logs
        _update_stage(mid, mtype, "summarizing")
        logger.info(f"[STAGE 2/6] Starting local hierarchical summarization...")
        ai_results = await AIService.summarize_transcript(transcript_text)
        logger.info(f"[STAGE 2/6] Summarization complete.")
        
        # 3. Prepare 3 separate PDF files for Drive (MOM report is handled manually by Admin)
        _update_stage(mid, mtype, "generating_pdfs")
        logger.info(f"[STAGE 3/6] Packaging 3-Asset Intelligence Archive (PDFs)...")
        
        # Prepare filenames with prefix and ID
        doc_tag = f"BR #{mid}" if mtype == "BR" else f"MOM #{mid}"
        file_tag = f"BR_{mid}" if mtype == "BR" else f"MOM_{mid}"

        # PDF 1: Full Verbatim Transcript (🎤 Monospace Line-Numbered Layout)
        transcript_filename = f"Transcript_{file_tag}_{title}_{mdate}.pdf"
        transcript_pdf = generate_transcript_pdf(f"TRANSCRIPT for {doc_tag}", mdate, transcript_text)

        # PDF 2: AI Auditing Logs (🔍 Segmented Process Trail)
        chunks_filename = f"AI_Auditing_Logs_{file_tag}_{title}_{mdate}.pdf"
        chunks_pdf = generate_audit_log_pdf(f"AUDITING LOG for {doc_tag}", mdate, ai_results['chunk_summaries'])

        # PDF 3: Executive Summary Briefing (📊 Green-Accented Narrative)
        formatted_filename = f"Executive_Briefing_{file_tag}_{title}_{mdate}.pdf"
        formatted_pdf = generate_summary_pdf(f"EXECUTIVE BRIEFING for {doc_tag}", mdate, ai_results['formatted_summary'])
        
        # 4. Upload Assets directly to the meeting folder
        _update_stage(mid, mtype, "uploading_assets")
        logger.info(f"[STAGE 4/6] Uploading Assets directly to meeting folder ID: {folder_id}")
        
        root_folder_id = ensure_subfolder(parent_root, parent_id=settings.DRIVE_FOLDER_ID)
        
        if not folder_id:
            folder_name = f"{mid} - {title} - {mdate} {mtime}"
            folder_id = ensure_subfolder(folder_name, parent_id=root_folder_id)

        # A. Upload the Audio Recording itself
        audio_filename = f"Recording_{title}_{mdate}.webm"
        with open(path, "rb") as f:
            audio_bytes = f.read()
        res_audio = upload_to_drive(audio_bytes, audio_filename, "audio/webm", subfolder_name=None, parent_id=folder_id)
        recording_link = res_audio.get("webViewLink")

        # B. Upload the 3 PDFs
        res_t = upload_to_drive(transcript_pdf, transcript_filename, "application/pdf", subfolder_name=None, parent_id=folder_id)
        res_a = upload_to_drive(chunks_pdf, chunks_filename, "application/pdf", subfolder_name=None, parent_id=folder_id)
        res_f = upload_to_drive(formatted_pdf, formatted_filename, "application/pdf", subfolder_name=None, parent_id=folder_id)
        
        transcript_link = res_t.get("webViewLink")
        logs_link = res_a.get("webViewLink")
        formatted_link = res_f.get("webViewLink")
        
        logger.info(f"[STAGE 4/6] Audio and 3 PDFs Uploaded directly to folder.")
        
        # 5. Update Sheet with Intelligence Asset Links (Mark as Processing)
        _update_stage(mid, mtype, "finalizing")
        logger.info(f"[STAGE 5/6] Syncing intelligence links and marking as Processing...")
        # Update Meeting/BR Status
        status_update = {
            "status": "Processing",
            "pdf_link": formatted_link, # Assuming formatted_link is the main PDF link
            "recording_link": recording_link,
            "ai_summary_link": formatted_link,
            "drive_logs_link": logs_link,
            "drive_transcript_id": transcript_link,
            "drive_folder_id": folder_id, # Add folder ID to update
        }

        sheet_name = "BR_Meetings" if mtype == "BR" else "Meetings"
        SheetsDB.update_row(sheet_name, mid, status_update)
        
        # FINAL STAGE
        _update_stage(mid, mtype, "completed") # Discussion Summary
        logger.info(f"[STAGE 6/6] Syncing intelligence assets...")
        
        # Dashboard Autofill: Use the detailed formatted narrative summary
        # This replaces the old short point-wise brief summary
        detailed_summary = ai_results.get('formatted_summary', 'Detailed summary not available.')
        discussion_update = {"summary_text": detailed_summary}
        
        if mtype == "BR":
            existing = SheetsDB.get_by_field("BR_Discussions", "meeting_id", mid)
            if existing: 
                SheetsDB.update_row("BR_Discussions", int(existing[0]['id']), discussion_update)
            else: 
                SheetsDB.append_row("BR_Discussions", {"meeting_id": mid, "summary_text": detailed_summary})
        else:
            existing = SheetsDB.get_by_field("Discussions", "meeting_id", mid)
            if existing: 
                SheetsDB.update_row("Discussions", int(existing[0]['id']), discussion_update)
            else: 
                SheetsDB.append_row("Discussions", {"meeting_id": mid, "summary_text": detailed_summary})

        _update_stage(mid, mtype, "completed")
        logger.info(f"✨ AI PIPELINE FULLY COMPLETED FOR '{title}' (ID: {mid})")
        
    except Exception as e:
        error_msg = str(e)[:500]  # Truncate for sheet cell limit
        logger.error(f"!!! CRITICAL: AI Pipeline failed for meeting {mid}: {e}", exc_info=True)
        sheet = "BR_Meetings" if mtype == "BR" else "Meetings"
        SheetsDB.update_row(sheet, mid, {
            "processing_stage": "failed",
            "processing_error": error_msg,
        })
    finally:
        if os.path.exists(path):
            os.remove(path)
            logger.info(f"Cleaned up temporary file: {path}")
