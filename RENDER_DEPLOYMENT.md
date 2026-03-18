# 🚀 Render Deployment Guide (Full System)

This guide provides the complete, step-by-step process for deploying the MOM AI Assistant to [Render.com](https://render.com).

---

## 🏗 Prerequisites
1.  **Render Account**: Sign up at [render.com](https://render.com).
2.  **GitHub Repository**: Ensure your code (both `backend/` and `frontend/` folders) is pushed to a private GitHub repository.
3.  **Google Credentials**: You must have your `google_credentials.json` ready (as explained in `CREDENTIALS_GUIDE.md`).

---

## 📦 1. Preparing the Code for Deployment

### 1.1 Backend (`backend/app/main.py`)
CORS settings are now dynamic. The backend will automatically allow any URL you set in the **`FRONTEND_URL`** environment variable on Render. No code change is needed for new domains.

### 1.2 Frontend API Base URL
Ensure your frontend uses an environment variable for the API URL. In `frontend/src/api/index.ts` (or wherever you initialize axios), it should look like:
```typescript
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'
});
```

---

## 🖥 2. Deploying the Backend (Web Service)

1.  Log in to **Render Dashboard**.
2.  Click **New +** > **Web Service**.
3.  Connect your GitHub repository.
4.  **Configure Service**:
    *   **Name**: `mom-backend`
    *   **Runtime**: `Python 3`
    *   **Root Directory**: `backend` (CRITICAL)
    *   **Build Command**: `pip install -r requirements.txt`
    *   **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5.  **Environment Variables**:
    Click **Advanced** > **Add Environment Variable** and add ALL keys from your `.env` file:
    *   `OPENAI_API_KEY`: `...`
    *   `ASSEMBLY_AI_API_KEY`: `...`
    *   `SPREADSHEET_ID`: `...`
    *   `DRIVE_FOLDER_ID`: `...`
    *   `DRIVE_FOLDER_ID`: `...`
    *   `CLIENT_NAME`: `...`
    *   `CLIENT_ADDRESS`: `...`
    *   `CLIENT_CS_EMAIL`: `...`
    *   `PORT`: `10000` (Render's default)
6.  **Google Credentials Secret File**:
    *   Go to **Secret Files** tab in Render.
    *   Filename: `google_credentials.json`
    *   Contents: Paste the ENTIRE content of your local `google_credentials.json` file.
7.  Click **Deploy Web Service**.
8.  **Wait**: Note down the URL Render provides (e.g., `https://mom-backend.onrender.com`).

---

## 🌐 3. Deploying the Frontend (Static Site)

1.  Click **New +** > **Static Site**.
2.  Connect the same GitHub repository.
3.  **Configure Site**:
    *   **Name**: `mom-frontend`
    *   **Root Directory**: `frontend` (CRITICAL)
    *   **Build Command**: `npm install && npm run build`
    *   **Publish Directory**: `dist`
4.  **Environment Variables**:
    Click **Advanced** > **Add Environment Variable**:
    *   `VITE_API_BASE_URL`: `https://mom-backend.onrender.com/api/v1` (Paste your Backend URL here + `/api/v1`)
5.  **Redirects/Rewrites**:
    *   Go to **Redirects** tab.
    *   Source: `/*`
    *   Destination: `/index.html`
    *   Action: `Rewrite` (This ensures React Router works after refresh).
6.  Click **Deploy Static Site**.

> [!IMPORTANT]
> **If you see "Not Found" on the frontend:**
> Ensure you have added the **Redirects/Rewrites** rule (Source: `/*`, Destination: `/index.html`, Action: `Rewrite`) in the Render dashboard. This is required for React routing to work.

---

Once your frontend is deployed (e.g., `https://agentic-mom-system.onrender.com`), you must tell the backend to allow requests from it.

1.  Go to your **Backend Service** on Render.
2.  Go to **Environment Variables**.
3.  Add/Update:
    *   `FRONTEND_URL`: `https://agentic-mom-system.onrender.com` (Use YOUR actual frontend URL)
4.  The backend will automatically redeploy and CORS errors will disappear.

---

## 🛠 Troubleshooting Render

*   **Build Fails**: Check if you set the **Root Directory** correctly (`backend` or `frontend`).
*   **API Errors**: Ensure `VITE_API_BASE_URL` in the frontend has `https://` and ends with `/api/v1`.
*   **Google Auth 403**: Ensure your Render Backend environment variables (Spreadsheet ID, etc.) match exactly.
*   **Email Errors**: Ensure you have set up the **Google Apps Script** as described in `SETUP.md`. If emails aren't sending, check the `EmailQueue` tab in your Google Sheet—if the status remains 'pending', the Apps Script trigger is not running.
*   **Quota Errors (429)**: Google Sheets has a limit of 60 reads/min. The system uses a 10-second cache to stay within these limits. Avoid having too many tabs open at once.

---
*Botivate Services LLP © 2026. Secure Deployment on Autopilot.*
