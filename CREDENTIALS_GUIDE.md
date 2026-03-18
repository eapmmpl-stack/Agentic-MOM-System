# Credentials & API Integration Guide

This guide provides step-by-step instructions to obtain the necessary credentials for the MOM AI Assistant.

---

## 1. OpenAI API (AI Summarization & Extraction)
OpenAI powers the intelligence behind meeting summaries and action item extraction.

1.  Go to [OpenAI Platform](https://platform.openai.com/).
2.  Sign in or create an account.
3.  Navigate to **API Keys** in the sidebar.
4.  Click **+ Create new secret key**.
5.  **Copy the key** and add it to `.env` as `OPENAI_API_KEY`.

---

## 2. AssemblyAI (Audio Transcription)
Used to convert recorded meeting audio into text.

1.  Go to [AssemblyAI Dashboard](https://www.assemblyai.com/dashboard).
2.  Sign up/Log in.
3.  Your **API Key** is visible on the home dashboard.
4.  Add it to `.env` as `ASSEMBLY_AI_API_KEY`.

---

## 3. Email Automation (Google Apps Script)
To ensure reliable email delivery (bypassing cloud port restrictions), we use a Google Apps Script that triggers every minute.

1.  Open your **Google Sheet** (the one used for the database).
2.  Go to **Extensions > Apps Script**.
3.  Paste the Code:
    *   (The code is available in `SETUP.md` under Section 3).
4.  Setup Automation:
    *   Select `setupTrigger` from the dropdown in the toolbar.
    *   Click **Run**.
    *   Authorize the script.
5.  **Status**: Your emails will now be automatically sent from your Gmail account whenever the backend adds them to the `EmailQueue` tab.

---

## 4. Google Cloud (Drive & Sheets Storage)
Used to store PDFs, logs, and meeting data in Google Sheets.

1.  Go to [Google Cloud Console](https://console.cloud.google.com/).
2.  Create a **New Project**.
3.  Enable APIs:
    *   Search for **Google Sheets API** and click **Enable**.
    *   Search for **Google Drive API** and click **Enable**.
4.  Create a Service Account:
    *   Go to **IAM & Admin > Service Accounts**.
    *   Click **Create Service Account**.
    *   Name it "MOM-Assistant" and click **Create and Continue**.
    *   Role: Select **Editor** or **Owner**.
5.  Generate JSON Key:
    *   Click on the newly created Service Account.
    *   Go to the **Keys** tab.
    *   Click **Add Key > Create new key**.
    *   Select **JSON** and click **Create**.
    *   Rename the downloaded file to `credentials.json` and place it in `backend/`.
6.  **Find the Client Email**:
    *   Open the `credentials.json` (or `google_credentials.json`) file you just downloaded.
    *   Look for the field `"client_email"`. It will look something like: `mom-assistant@project-id.iam.gserviceaccount.com`.
    *   **Copy this email address.**

7.  **Share Google Sheet (Database)**:
    *   Open the Google Sheet you created for the database.
    *   Click the **Share** button in the top-right corner.
    *   **Paste the Client Email** you copied in the "Add people and groups" box.
    *   Ensure the role is set to **Editor**.
    *   Click **Send** (you can uncheck "Notify people").

8.  **Share Google Drive Folder (Storage)**:
    *   Open your Google Drive and find the folder where you want to store PDFs/Recordings.
    *   Right-click the folder and select **Share**.
    *   **Paste the Client Email** again.
    *   Ensure the role is set to **Editor**.
    *   Click **Send**.

### 💡 Alternative: Using Shared Drives (Recommended for Teams)
If the standard "Share" doesn't work or you are in a professional Google Workspace:
1.  Create a **Shared Drive** (not just a folder).
2.  Click **Manage members** at the top right.
3.  **Add the Client Email** (`...gserviceaccount.com`).
4.  Set the role to **Content Manager** (necessary for creating/deleting files).
5.  All folders created inside this Shared Drive will automatically be accessible by the AI.

> [!TIP]
> **Why is this necessary?**
> The system uses the Service Account to talk to Google. If you don't share the folder/sheet with that specific email, the system will get an "Access Denied" error because it doesn't have permission to see your files.

---

## 5. White-Labeling Settings
Update these in `.env` to brand the system for your client:

```bash
CLIENT_NAME="Company Name"
CLIENT_ADDRESS="Full Address, with, commas, for, lines"
CLIENT_CS_EMAIL="cs@company.com"
SHOW_BOTIVATE_BRANDING=true  # Set to false for premium white-label
```
