# ⚙️ Environment Setup & Deployment Guide

This document outlines the prerequisites, local development environment setup, and deployment processes for the Botivate Agentic MOM System.

---

## 🛑 Prerequisites

Ensure your system possesses the following dependencies before proceeding:

1. **Node.js** (v18.0.0 or higher) for React + Vite Frontend
2. **Python** (v3.10.0 or higher) for FastAPI Backend
3. **npm** (comes bundled with Node.js)
4. **PostgreSQL Server** (running locally or accessible via a remote connection string)
5. **Git** (for version control and repository management)

---

## 🔑 Environment Secrets Configuration

Both the Frontend and Backend components rely on `.env` files. Ensure you construct these files in their respective roots before initiating any servers.

### Backend (`/backend/.env`)
Create a file named `.env` inside the `/backend` directory:

```ini
# PostgreSQL Database Connection URL
DATABASE_URL=postgresql://postgres:user123@localhost/mom_botivate

# CORS Configuration (Allows frontend to interact with backend)
CORS_ORIGINS=["http://localhost:5173", "http://localhost:3000"]

# FastAPI Application Settings
DEBUG=True
API_V1_STR=/api/v1

# Secure SMTP Mail Configuration (For Automated PDF Dispatch)
MAIL_USERNAME=your-botivate-agent@gmail.com
MAIL_PASSWORD=your-secure-app-password
MAIL_FROM=your-botivate-agent@gmail.com
MAIL_PORT=587
MAIL_SERVER=smtp.gmail.com
MAIL_STARTTLS=True
MAIL_SSL_TLS=False
USE_CREDENTIALS=True
```

### Frontend (`/frontend/.env` - Optional)
*(Optional, if you wish to override standard configurations)*
```ini
# Base API Router
VITE_API_BASE_URL=http://localhost:8000
```

---

## 💻 Local Development Setup

We highly recommend utilizing isolated environments (Virtual Environments) to prevent dependency conflicts during Python installation.

### 1. Backend Initialization (FastAPI)

1. **Navigate to the Backend Directory:**
   ```bash
   cd backend
   ```

2. **Initialize a Virtual Environment:**
   ```bash
   python -m venv .venv
   ```

3. **Activate the Virtual Environment:**
   - **Windows:** `.venv\Scripts\activate`
   - **macOS/Linux:** `source .venv/bin/activate`

4. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

5. **Initiate Development Server:**
   ```bash
   uvicorn app.main:app --reload
   ```
   *The backend will boot up at `http://localhost:8000`. You can explore the interactive API schema at `http://localhost:8000/docs`.*

### 2. Frontend Initialization (React + Vite)

1. **Navigate to the Frontend Directory:**
   ```bash
   cd frontend
   ```

2. **Install Node Modules:**
   ```bash
   npm install
   ```

3. **Initiate Development Server:**
   ```bash
   npm run dev
   ```
   *The stunning Glassmorphic UI will now be active at `http://localhost:5173`.*

---

## 🚀 Building for Production

When scaling Botivate for enterprise operation, you must compile an optimized production artifact.

### Compiling Frontend Artifacts
```bash
cd frontend
npm run build
```
This routine triggers a rigorous TypeScript validation phase (`tsc`) followed by the Vite builder. The final optimized bundle (`html`, `js`, `css`, and brand assets) will output precisely into the `/dist` directory.

### Production Environment Readiness
- The Backend `FastAPI` instance should transition from `uvicorn` (with `--reload`) to an industrial-grade worker process array like `gunicorn`, paired with `UvicornWorker`.
- Ensure `DEBUG=False` in the Backend `.env`.
- Ensure your `CORS_ORIGINS` parameter mirrors your actual domain.

---
*Botivate Services LLP © 2026. Code securely.*
