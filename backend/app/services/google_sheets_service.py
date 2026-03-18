"""Google Sheets Service – Generic CRUD layer replacing SQLite.

This module provides a generic, reusable interface for reading/writing data
to Google Sheets.  Every "table" is a separate tab (worksheet) inside a
single Spreadsheet.  Adding a new entity in the future (e.g. BR Meetings,
Rescheduling logs) is as simple as defining a new SHEET_SCHEMA entry.

Design principles
─────────────────
1. **Single source of truth** – the Google Spreadsheet.
2. **Adaptable** – new sheets/columns are config-driven via SHEET_SCHEMAS.
3. **ID generation** – auto-incrementing integer IDs managed in-sheet.
4. **Thread-safe client** – gspread client is cached per-process.
"""

import logging
import os
from datetime import datetime, date, time
from typing import Any, Optional

import gspread
from google.oauth2.service_account import Credentials

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# ── Google Auth ────────────────────────────────────────────────────────

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

CREDENTIALS_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "google_credentials.json",
)

# These are now fetched from settings for dynamic configuration
SPREADSHEET_ID = settings.SPREADSHEET_ID
DRIVE_FOLDER_ID = settings.DRIVE_FOLDER_ID

# ── Sheet Schemas (column definitions) ────────────────────────────────
# Each key is a worksheet tab name.  The value is an ordered list of
# column headers.  When you need a new entity, just add a new entry here.

SHEET_SCHEMAS: dict[str, list[str]] = {
    "Meetings": [
        "id", "title", "organization", "meeting_type", "meeting_mode",
        "date", "time", "venue", "hosted_by", "file_path",
        "created_by", "created_at", "pdf_link", "drive_file_id",
        "drive_folder_id", "recording_link", "drive_recording_id",
        "drive_transcript_id", "ai_summary_link", "drive_logs_link", "status", "sent_to_cs",
        "processing_stage", "processing_error",
    ],
    "Attendees": [
        "id", "meeting_id", "user_name", "email", "designation",
        "whatsapp_number", "remarks", "attendance_status",
    ],
    "Agenda": [
        "id", "meeting_id", "topic", "description",
    ],
    "Discussions": [
        "id", "meeting_id", "summary_text",
    ],
    "Tasks": [
        "id", "meeting_id", "title", "description",
        "responsible_person", "responsible_email",
        "deadline", "status", "created_at",
    ],
    "TaskHistory": [
        "id", "task_id", "previous_status", "new_status",
        "changed_at", "changed_by",
    ],
    "NextMeeting": [
        "id", "meeting_id", "next_date", "next_time",
    ],
    "Users": [
        "id", "name", "email", "hashed_password", "role",
        "phone", "is_active", "created_at",
    ],
    "Notifications": [
        "id", "user_id", "recipient_email", "message",
        "notification_type", "is_read", "sent_at",
    ],
    "Files": [
        "id", "meeting_id", "file_path", "file_type", "uploaded_at",
    ],
    "EmailQueue": [
        "id", "to_email", "subject", "body", "status", "created_at"
    ],
    # ── Board Resolution (BR) Sheets ──────────────────────────────────
    "BR_Meetings": [
        "id", "title", "organization", "meeting_type", "meeting_mode",
        "date", "time", "venue", "hosted_by", "file_path",
        "created_by", "created_at", "pdf_link", "drive_file_id",
        "drive_folder_id", "recording_link", "drive_recording_id",
        "drive_transcript_id", "ai_summary_link", "drive_logs_link", "status", "sent_to_cs",
        "processing_stage", "processing_error",
    ],
    "BR_Directors": [
        "id", "meeting_id", "user_name", "email", "designation",
        "whatsapp_number", "remarks", "attendance_status",
    ],
    "BR_Agenda": [
        "id", "meeting_id", "topic", "description",
    ],
    "BR_Discussions": [
        "id", "meeting_id", "summary_text",
    ],
    "BR_Tasks": [
        "id", "meeting_id", "title", "description", "responsible_person",
        "responsible_email", "deadline", "status", "created_at",
    ],
    "BR_NextMeeting": [
        "id", "meeting_id", "next_date", "next_time",
    ],
    "BR_Files": [
        "id", "meeting_id", "file_path", "file_type", "uploaded_at", "drive_file_id",
    ],
}


# ── Singleton Client ──────────────────────────────────────────────────

_client: gspread.Client | None = None
_spreadsheet: gspread.Spreadsheet | None = None
_worksheets: dict[str, gspread.Worksheet] = {}


def _get_client() -> gspread.Client:
    global _client
    if _client is None:
        creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
        _client = gspread.authorize(creds)
        logger.info("Google Sheets client authorised.")
    return _client


def _get_spreadsheet() -> gspread.Spreadsheet:
    global _spreadsheet
    if _spreadsheet is None:
        _spreadsheet = _get_client().open_by_key(SPREADSHEET_ID)
        logger.info("Opened spreadsheet: %s", _spreadsheet.title)
    return _spreadsheet


def get_worksheet(sheet_name: str) -> gspread.Worksheet:
    """Return (or create) a worksheet tab by name, ensuring headers exist."""
    global _worksheets
    if sheet_name in _worksheets:
        return _worksheets[sheet_name]

    ss = _get_spreadsheet()
    try:
        ws = ss.worksheet(sheet_name)
    except gspread.WorksheetNotFound:
        cols = SHEET_SCHEMAS.get(sheet_name, ["id"])
        ws = ss.add_worksheet(title=sheet_name, rows=1000, cols=len(cols))
        ws.update("A1", [cols])
        ws.format("A1:Z1", {"textFormat": {"bold": True}})
        logger.info("Created new worksheet: %s", sheet_name)
    
    _worksheets[sheet_name] = ws
    return ws


# ── Helper Converters ─────────────────────────────────────────────────

def _serialise(value: Any) -> str:
    """Convert a Python value to a string for Google Sheets storage."""
    if value is None:
        return ""
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, time):
        return value.isoformat()
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, (int, float)):
        return str(value)
    # Enum-like objects
    if hasattr(value, "value"):
        return str(value.value)
    return str(value)


def _to_int(val: str) -> int | None:
    if not val or val.strip() == "":
        return None
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return None


def _to_bool(val: str) -> bool:
    return val.strip().lower() in ("true", "1", "yes")


def _row_to_dict(headers: list[str], row: list[str]) -> dict[str, str]:
    """Zip headers and row values into a dict, padding short rows."""
    padded = row + [""] * (len(headers) - len(row))
    return dict(zip(headers, padded))


import time as time_module

_CACHE_TTL = 1  # Reduced to 1 second for responsive progress tracking
_sheets_cache = {}

def _get_sheet_values(sheet_name: str) -> list[list[str]]:
    now = time_module.time()
    if sheet_name in _sheets_cache:
        data, ts = _sheets_cache[sheet_name]
        if now - ts < _CACHE_TTL:
            return data
    ws = get_worksheet(sheet_name)
    all_vals = ws.get_all_values()
    _sheets_cache[sheet_name] = (all_vals, now)
    return all_vals

def _invalidate_cache(sheet_name: str):
    _sheets_cache.pop(sheet_name, None)

def _update_cache(sheet_name: str, new_rows: list[list[str]]):
    """Update cache with new rows instead of just invalidating, to save read quota."""
    now = time_module.time()
    if sheet_name in _sheets_cache:
        old_vals, ts = _sheets_cache[sheet_name]
        # Only update if the cache is still relatively fresh
        if now - ts < _CACHE_TTL:
            updated_vals = old_vals + new_rows
            _sheets_cache[sheet_name] = (updated_vals, ts)
            return
    
    # If not in cache or expired, we just leave it empty. 
    # The next read will fetch the whole truth.
    _invalidate_cache(sheet_name)

# ── Core CRUD ─────────────────────────────────────────────────────────

class SheetsDB:
    """Generic CRUD operations on any worksheet tab."""

    # ── Next ID ───────────────────────────────────────────────────────

    @staticmethod
    def next_id(sheet_name: str) -> int:
        """Auto-increment integer ID for a sheet."""
        all_data = _get_sheet_values(sheet_name)
        all_vals = [row[0] if row else "" for row in all_data]  # Column A = "id"
        if len(all_vals) <= 1:
            return 1
        ids = []
        for v in all_vals[1:]:
            n = _to_int(v)
            if n is not None:
                ids.append(n)
        return max(ids, default=0) + 1

    # ── Append Row ────────────────────────────────────────────────────

    @staticmethod
    def append_row(sheet_name: str, data: dict[str, Any]) -> dict[str, str]:
        """Append a new row.  Auto-sets 'id' if not provided."""
        ws = get_worksheet(sheet_name)
        headers = SHEET_SCHEMAS.get(sheet_name)
        if not headers:
            # Fallback - try to get from first row of cached data
            all_vals = _get_sheet_values(sheet_name)
            headers = all_vals[0] if all_vals else ["id"]

        if "id" not in data or not data["id"]:
            data["id"] = SheetsDB.next_id(sheet_name)

        row = [_serialise(data.get(col)) for col in headers]
        ws.append_row(row, value_input_option="USER_ENTERED")
        
        # Smart update: append to cache instead of invalidating and refetching immediately
        _update_cache(sheet_name, [row])
        
        logger.info("Appended row to %s with id=%s", sheet_name, data.get("id"))
        return _row_to_dict(headers, row)

    @staticmethod
    def append_rows(sheet_name: str, data_list: list[dict[str, Any]]) -> list[dict[str, str]]:
        """Append multiple rows in one API call."""
        if not data_list:
            return []
            
        ws = get_worksheet(sheet_name)
        headers = SHEET_SCHEMAS.get(sheet_name)
        if not headers:
            all_vals = _get_sheet_values(sheet_name)
            headers = all_vals[0] if all_vals else ["id"]

        start_id = SheetsDB.next_id(sheet_name)
        rows_to_append = []
        result_dicts = []
        
        for i, data in enumerate(data_list):
            if "id" not in data or not data["id"]:
                data["id"] = start_id + i
            
            row = [_serialise(data.get(col)) for col in headers]
            rows_to_append.append(row)
            result_dicts.append(_row_to_dict(headers, row))

        ws.append_rows(rows_to_append, value_input_option="USER_ENTERED")
        
        # Batch cache update
        _update_cache(sheet_name, rows_to_append)
        
        logger.info("Batch appended %d rows to %s starting at id=%s", len(rows_to_append), sheet_name, start_id)
        return result_dicts

    # ── Get All Rows ──────────────────────────────────────────────────

    @staticmethod
    def get_all(sheet_name: str) -> list[dict[str, str]]:
        """Return all rows as list of dicts."""
        all_vals = _get_sheet_values(sheet_name)
        if len(all_vals) <= 1:
            return []
        headers = all_vals[0]
        results = []
        for row in all_vals[1:]:
            if not any(str(cell).strip() for cell in row):
                continue
            results.append(_row_to_dict(headers, row))
        return results

    # ── Get By ID ─────────────────────────────────────────────────────

    @staticmethod
    def get_by_id(sheet_name: str, record_id: int) -> dict[str, str] | None:
        all_vals = _get_sheet_values(sheet_name)
        if len(all_vals) <= 1:
            return None
        headers = all_vals[0]
        for row in all_vals[1:]:
            d = _row_to_dict(headers, row)
            if _to_int(str(d.get("id", ""))) == record_id:
                return d
        return None

    # ── Get By Field ──────────────────────────────────────────────────

    @staticmethod
    def get_by_field(sheet_name: str, field: str, value: Any) -> list[dict[str, str]]:
        """Return all rows where field == value."""
        str_val = _serialise(value)
        all_data = SheetsDB.get_all(sheet_name)
        return [r for r in all_data if str(r.get(field, "")) == str_val]

    # ── Update Row ────────────────────────────────────────────────────

    @staticmethod
    def update_row(sheet_name: str, record_id: int, updates: dict[str, Any]) -> dict[str, str] | None:
        """Update specific fields of a row by id."""
        ws = get_worksheet(sheet_name)
        all_vals = _get_sheet_values(sheet_name)
        headers = SHEET_SCHEMAS.get(sheet_name, all_vals[0] if all_vals else ["id"])

        if len(all_vals) <= 1:
            return None

        for row_idx, row in enumerate(all_vals[1:], start=2):
            if _to_int(row[0] if row else "") == record_id:
                for col_name, new_val in updates.items():
                    if col_name in headers:
                        col_idx = headers.index(col_name) + 1
                        ws.update_cell(row_idx, col_idx, _serialise(new_val))
                _invalidate_cache(sheet_name)
                # Re-fetch
                updated_row = ws.row_values(row_idx)
                return _row_to_dict(headers, updated_row)
        return None

    # ── Delete Row ────────────────────────────────────────────────────

    @staticmethod
    def delete_row(sheet_name: str, record_id: int) -> bool:
        ws = get_worksheet(sheet_name)
        all_vals = _get_sheet_values(sheet_name)
        for row_idx, row in enumerate(all_vals[1:], start=2):
            if _to_int(row[0] if row else "") == record_id:
                ws.delete_rows(row_idx)
                _invalidate_cache(sheet_name)
                logger.info("Deleted row %d from %s", row_idx, sheet_name)
                return True
        return False

    # ── Delete By Field ───────────────────────────────────────────────

    @staticmethod
    def delete_by_field(sheet_name: str, field: str, value: Any) -> int:
        """Delete all rows matching field==value. Returns count deleted."""
        ws = get_worksheet(sheet_name)
        all_vals = _get_sheet_values(sheet_name)
        headers = SHEET_SCHEMAS.get(sheet_name, all_vals[0] if all_vals else ["id"])
        if field not in headers:
            return 0
        col_idx = headers.index(field)
        str_val = _serialise(value)
        rows_to_delete = []
        for row_idx, row in enumerate(all_vals[1:], start=2):
            cell_val = row[col_idx] if col_idx < len(row) else ""
            if str(cell_val) == str(str_val):
                rows_to_delete.append(row_idx)

        # Delete from bottom up so indices remain valid
        for r in reversed(rows_to_delete):
            ws.delete_rows(r)

        if rows_to_delete:
            _invalidate_cache(sheet_name)
        return len(rows_to_delete)

    # ── Count ─────────────────────────────────────────────────────────

    @staticmethod
    def count(sheet_name: str) -> int:
        all_vals = _get_sheet_values(sheet_name)
        return max(len(all_vals) - 1, 0)

    # ── Count By Field ────────────────────────────────────────────────

    @staticmethod
    def count_by_field(sheet_name: str, field: str, value: Any) -> int:
        return len(SheetsDB.get_by_field(sheet_name, field, value))


# ── Initialise sheets on import ───────────────────────────────────────

def init_sheets():
    """Ensure all defined sheet tabs exist and headers match the schema.
    This ensures that new columns added to SHEET_SCHEMAS are reflected in the actual Google Sheet.
    """
    global _worksheets
    try:
        ss = _get_spreadsheet()
        # Single read call to fetch all worksheets
        existing_wss = ss.worksheets()
        existing_titles = {ws.title: ws for ws in existing_wss}
        
        for name, expected_cols in SHEET_SCHEMAS.items():
            if name not in existing_titles:
                # Create missing worksheet
                ws = ss.add_worksheet(title=name, rows=1000, cols=len(expected_cols))
                ws.update("A1", [expected_cols])
                ws.format("A1:Z1", {"textFormat": {"bold": True}})
                _worksheets[name] = ws
                logger.info("Created missing worksheet: %s", name)
            else:
                # Sync headers if they changed
                ws = existing_titles[name]
                _worksheets[name] = ws
                current_headers = ws.row_values(1)
                if current_headers != expected_cols:
                    logger.info("Syncing headers for sheet: %s", name)
                    # We only update headers if they are different. 
                    # Note: This doesn't migrate data, just ensures the header row matches schema.
                    ws.update("A1", [expected_cols])
        
        logger.info("All Google Sheet tabs verified/synced.")
    except Exception as e:
        logger.error("Failed to initialise Google Sheets: %s", e)


# ── Google Drive Upload ───────────────────────────────────────────────

def upload_to_drive(file_bytes: bytes, filename: str, mimetype: str = "application/pdf", subfolder_name: str | None = "Standard MOMs", parent_id: str = DRIVE_FOLDER_ID) -> dict:
    """Upload a file to a specific subfolder inside the configured Google Drive folder.
    
    If subfolder_name is None, it uploads directly to parent_id.
    If the subfolder doesn't exist, it creates it automatically inside the parent_id.
    Returns dict with 'id' and 'webViewLink'.
    """
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaInMemoryUpload

    creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
    drive_service = build("drive", "v3", credentials=creds)

    target_folder_id = parent_id

    # 1. Check if we need to find/create a subfolder
    if subfolder_name:
        query = f"'{parent_id}' in parents and name = '{subfolder_name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
        results = drive_service.files().list(
            q=query, 
            spaces='drive', 
            fields='files(id, name)',
            supportsAllDrives=True,
            includeItemsFromAllDrives=True
        ).execute()
        folders = results.get('files', [])

        if not folders:
            # Create the subfolder
            folder_metadata = {
                'name': subfolder_name,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [parent_id]
            }
            folder = drive_service.files().create(
                body=folder_metadata, 
                fields='id',
                supportsAllDrives=True
            ).execute()
            target_folder_id = folder.get('id')
            logger.info("Created new Drive subfolder: %s", subfolder_name)
        else:
            target_folder_id = folders[0].get('id')

    # 2. Upload the new file to the correct subfolder
    file_metadata = {
        "name": filename,
        "parents": [target_folder_id],
    }
    media = MediaInMemoryUpload(file_bytes, mimetype=mimetype)

    file = drive_service.files().create(
        body=file_metadata,
        media_body=media,
        fields="id, webViewLink",
        supportsAllDrives=True
    ).execute()

    # Make file publicly readable
    import time
    from googleapiclient.errors import HttpError
    for attempt in range(5):
        try:
            drive_service.permissions().create(
                fileId=file["id"],
                body={"type": "anyone", "role": "reader"},
                supportsAllDrives=True
            ).execute()
            break  # Success
        except HttpError as error:
            if error.resp.status in [500, 502, 503, 504] and attempt < 4:
                logger.warning(f"Transient error setting permissions for {filename}, retrying in {2 ** attempt}s...")
                time.sleep(2 ** attempt)
            else:
                logger.error(f"Failed to set permissions for {filename} after {attempt + 1} attempts.")
                raise

    logger.info("Uploaded %s to Drive -> %s: %s", filename, subfolder_name, file.get("webViewLink"))
    return {"id": file["id"], "webViewLink": file.get("webViewLink", "")}


def ensure_subfolder(subfolder_name: str, parent_id: str = DRIVE_FOLDER_ID) -> str:
    """Find or create a subfolder in Google Drive."""
    from googleapiclient.discovery import build
    creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
    drive_service = build("drive", "v3", credentials=creds)

    query = f"'{parent_id}' in parents and name = '{subfolder_name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    results = drive_service.files().list(
        q=query, 
        spaces='drive', 
        fields='files(id, name)',
        supportsAllDrives=True,
        includeItemsFromAllDrives=True
    ).execute()
    folders = results.get('files', [])

    if folders:
        return folders[0].get('id')

    folder_metadata = {
        'name': subfolder_name,
        'mimeType': 'application/vnd.google-apps.folder',
        'parents': [parent_id]
    }
    folder = drive_service.files().create(
        body=folder_metadata, 
        fields='id',
        supportsAllDrives=True
    ).execute()
    return folder.get('id')


def delete_from_drive(file_id: str):
    """Delete a file or folder from Google Drive."""
    if not file_id:
        return
    try:
        from googleapiclient.discovery import build
        creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
        drive_service = build("drive", "v3", credentials=creds)
        # Using delete (permanent) instead of trash for cleanup
        drive_service.files().delete(fileId=file_id, supportsAllDrives=True).execute()
        logger.info("Permanently deleted object from Drive: %s", file_id)
    except Exception as e:
        logger.warning("Failed to delete object from Drive (%s): %s", file_id, e)


def delete_drive_folder(folder_id: str):
    """Alias for delete_from_drive for semantic clarity."""
    delete_from_drive(folder_id)
