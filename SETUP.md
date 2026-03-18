# ⚙️ Environment Setup & Configuration Guide

This document outlines the prerequisites, Google Cloud configuration, backend artificial intelligence setup, local development environment setup, and deployment processes for the **Botivate Agentic MOM System**.

---

## 🛑 Prerequisites

Ensure your system processes the following dependencies before proceeding:

1. **Node.js** (v18.0.0 or higher) - Required for React + Vite Frontend compilation.
2. **Python** (v3.10.0 or higher) - Required for FastAPI Backend and AI libraries.
3. **Google Account** - To manage Google Sheets databases and Google Drive archival storage.
4. **Git** - For version control and deployment.
5. **OpenAI Account** - For LangChain LLM capabilities.
6. **AssemblyAI Account** - For cloud-based Speech-to-Text accuracy.

---

## ☁️ 1. Google Cloud Setup (CRITICAL)

Botivate uses **Google Sheets** as a database and **Google Drive** for file and generated PDF archival. Follow these steps meticulously:

### Step 1.1: Create a Google Cloud Project
- Navigate to the [Google Cloud Console](https://console.cloud.google.com/).
- Create a new project named (e.g., `MOM-AI-Assistant-DB`).

### Step 1.2: Enable APIs
Enable the following two APIs in your newly created project via the "API Library":
- **Google Sheets API**
- **Google Drive API**

### Step 1.3: Create a Service Account
- Navigate to **IAM & Admin > Service Accounts**.
- Click **Create Service Account** and assign it a name (e.g., `botivate-agent`).
- Complete creation. *No special optional roles are strictly needed at this point.*

### Step 1.4: Download the JSON Credential Key
- Click on your new Service Account from the list.
- Navigate to the **Keys** tab.
- Click **Add Key > Create New Key**, select **JSON**, and download the file.
- **IMPORTANT**: Rename this JSON file to exactly `google_credentials.json` and place it inside the `/backend` directory of this repository. *Do not commit this file to GitHub!*

### Step 1.5: Prepare Cloud Storage Directories & DB
- Open [Google Sheets](https://docs.google.com/spreadsheets/u/0/) and create a new, completely blank Spreadsheet.
  - Copy its **Spreadsheet ID** from the URL (the random string of alphanumeric characters between `/d/` and `/edit`).
- Open [Google Drive](https://drive.google.com/drive/u/0/) and create a new top-level Folder to store MOM Archive assets (PDFs and Recordings).
  - Copy its **Drive Folder ID** from the URL (the string after `/folders/`).
- **SHARING PERMISSIONS (MANDATORY)**: Copy the email address of the Service Account you created in Step 1.3 (e.g., `botivate-agent@your-project.iam.gserviceaccount.com`). Go to the top right corner of your Google Sheet, click "Share", enter that email address, and give it **Editor** permissions. Do the exact same for the Google Drive Folder.

---

## 🤖 2. Artificial Intelligence Pipeline Setup

Botivate's intelligence relies on two core Cloud vendors for processing audio.

### Step 2.1: AssemblyAI Configuration (Audio Processing STT)
- Create an account on [AssemblyAI](https://www.assemblyai.com/).
- Navigate to your dashboard and copy your **AssemblyAI API Key**.
- This enables state-of-the-art multilingual transcriptions (Hindi and English).

### Step 2.2: OpenAI Configuration (MOM Mapping & Reduction)
- Create a developer account on [OpenAI Platform](https://platform.openai.com/).
- Ensure your billing is active and fund your account.
- Navigate to the "API keys" section to generate a new secret key.
- Save your **OpenAI API Key**.

---

## ✉️ 3. Email Automation Setup (Google Apps Script)

To bypass cloud port restrictions (on Render/HF), Botivate uses a **Google Sheets Email Queue**. A Google Apps Script processes this queue and sends emails via your Gmail account.

### Step 3.1: Create & Deploy the Apps Script
1.  Open the Google Sheet you created in Step 1.5.
2.  Go to **Extensions > Apps Script**.
3.  Delete any existing code and paste the following:
    ```javascript
    /**
     * Automatically sends emails from the EmailQueue sheet
     * Trigger: Time-driven (every 1 minute)
     */
    function processEmailQueue() {
      var ss = SpreadsheetApp.getActiveSpreadsheet();
      var sheet = ss.getSheetByName("EmailQueue");
      if (!sheet) return;

      var data = sheet.getDataRange().getValues();
      if (data.length <= 1) return; // Only headers

      var headers = data[0];
      var toIdx = headers.indexOf("to_email");
      var subIdx = headers.indexOf("subject");
      var bodyIdx = headers.indexOf("body");
      var statusIdx = headers.indexOf("status");

      for (var i = 1; i < data.length; i++) {
        var row = data[i];
        if (row[statusIdx] === "pending") {
          try {
            MailApp.sendEmail({
              to: row[toIdx],
              subject: row[subIdx],
              htmlBody: row[bodyIdx]
            });
            sheet.getRange(i + 1, statusIdx + 1).setValue("sent");
            sheet.getRange(i + 1, headers.indexOf("sent_at") + 1).setValue(new Date());
          } catch (e) {
            sheet.getRange(i + 1, statusIdx + 1).setValue("error: " + e.toString());
          }
        }
      }
    }

    /**
     * Run this ONCE to set up the 1-minute automation
     */
    function setupTrigger() {
      var triggers = ScriptApp.getProjectTriggers();
      for (var i = 0; i < triggers.length; i++) {
        ScriptApp.deleteTrigger(triggers[i]);
      }
      ScriptApp.newTrigger('processEmailQueue')
        .timeBased()
        .everyMinutes(1)
        .create();
    }
    ```
4.  Click **Save** (disk icon) and name the project "MOM Email Automator".
5.  In the toolbar, select **`setupTrigger`** from the dropdown and click **Run**.
6.  Grant permissions when prompted. The bot is now 100% automated!

---

## 🔑 4. Environment Variables Checklist

Now that all external services are configured, create a `.env` file in the `/backend` root folder:

```ini
# Core Configuration
APP_NAME="Botivate MOM Agent"
ENVIRONMENT="development"
DEBUG=True
API_V1_PREFIX="/api/v1"
SECRET_KEY="your-secret-key-here"

# Google Cloud Configuration
# (Identified from Step 1)
SPREADSHEET_ID="your_google_sheet_id_here"
DRIVE_FOLDER_ID="your_google_drive_folder_id_here"
GOOGLE_CREDENTIALS_FILE="google_credentials.json"

# AI Configuration (Identified from Step 2)
OPENAI_API_KEY="sk-your-openai-api-key-here"
OPENAI_MODEL="gpt-4o-mini"
ASSEMBLY_AI_API_KEY="your-assembly-ai-api-key-here"

# Mail Configuration (LEGACY - No longer required if using Apps Script)
# SMTP_USER="your-email@gmail.com"
# SMTP_PASSWORD="your-16-char-app-password"
# EMAIL_FROM="Botivate Governance <your-email@gmail.com>"
# SMTP_HOST="smtp.gmail.com"
# SMTP_PORT=587

# Branding & White-Labeling (Identified from Step 6)
CLIENT_NAME="Your Client Name"
CLIENT_ADDRESS="Full Address, Multi-line, with commas"
CLIENT_CS_EMAIL="cs@client.com"
SHOW_BOTIVATE_BRANDING=true
BOTIVATE_SIGNATURE="Powered by Botivate Services LLP"

# App Constants
FRONTEND_URL="http://localhost:5173"
```

---

## 💻 5. Running the Application Locally

### Step 5.1: Backend Initialization (FastAPI)
1. Open a terminal and navigate to exactly `backend/`.
2. Create and activate a dedicated virtual environment:
   ```bash
   python -m venv .venv

   # For Windows PowerShell
   .\.venv\Scripts\Activate.ps1
   
   # For macOS/Linux Git Bash
   source .venv/bin/activate
   ```
3. Install the application's required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Start the Uvicorn web server:
   ```bash
   uvicorn app.main:app --reload
   ```
   *The backend will be live at `http://localhost:8000` with Swagger Docs at `/docs`.*

### Step 5.2: Frontend Initialization (React/Vite)
1. Open a separate terminal window and switch to `frontend/`.
2. Install package node modules:
   ```bash
   npm install
   ```
3. Run the development environment:
   ```bash
   npm run dev
   ```
   *Navigate your browser to `http://localhost:5173` to see the rich Botivate UI.*

---

## 🚀 6. Typical Usage & Verification Walkthrough

1. **Verify Connection**: Launch the app and visit the Dashboard. If the KPIs and charts are visible and no `500` errors are rendered, your Google Sheets linkage is highly likely correct.
2. **Schedule**: Visit the "Meetings" tab. Create a new "Board Resolution" meeting. Submit attendees.
3. **Execute AI Logs**: Start the meeting, run the audio. Finally click **Record MOM** on the Meeting tile action bar. Provide the audio file recorded in a `.webm` or `.m4a` format to the File Dropzone.
4. **Processing Watch**: Wait 2-3 minutes while the Dashboard tile shows "Processing". Under the hood, the backend evaluates Assembly STT, LLM map-reduces, creates PDFs, uploads natively to Google Drive subfolders, updates Sheets database properties, and emails everyone individually!

---

## 🆘 Troubleshooting & Common Flaws

1. **`googleapiclient.errors.HttpError 403`**: Caused immediately when attempting to create a meeting. This guarantees your Google Drive Folder or Sheet is entirely missing the *Editor* role given to your `.json` service credential's email address.
2. **`assemblyai.errors.UnauthorizedError`**: Incorrect STT token. Verify `ASSEMBLY_AI_API_KEY` without trailing spaces.
3. **`aiosmtplib.errors.SMTPAuthenticationError`**: Your newly generated Google App password has spaces in it. Make sure inside the `.env` the token is squished together (e.g., `abcdefghijklmnop`).
4. **Missing Sheet Headers:** To allow dynamic column syncing, ensure on your first run that if there is a `KeyError: row index out of bound`, it means the actual visible header titles inside the blank Spreadsheet tabs at row 1 don't match the Python script enums. Ensure your tabs are specifically named `Meetings`, `Attendees`, `Tasks`, `Agenda`, `Discussions`, `Global_Settings`, `Notifications`, `Users`, `BR_Meetings`, `BR_Tasks`, `BR_Discussions`.
5. **Branding Not Reflecting:** Ensure you have restarted the backend server after modifying `.env` variables.

---
## 📄 Documentation Reference
- [CREDENTIALS_GUIDE.md](CREDENTIALS_GUIDE.md): Detailed steps for API keys.
- [RENDER_DEPLOYMENT.md](RENDER_DEPLOYMENT.md): Guide for cloud deployment.
- [WHITE_LABEL_GUIDE.md](WHITE_LABEL_GUIDE.md): Detailed white-label architecture.
---
*Botivate Services LLP © 2026. Secure Governance on Autopilot.*
