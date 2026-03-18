# Botivate: Agentic Minutes of Meeting (MOM) System

![Botivate Logo](frontend/public/botivate-logo-cropped.png)

Botivate is an intelligent, agentic system designed to autonomously handle, analyze, and document your meeting minutes on autopilot. By leveraging cutting-edge AI capabilities (OpenAI and AssemblyAI), Botivate transforms unstructured meeting interactions into highly structured, actionable intelligence, now fully integrated with Google Workspace for seamless enterprise cloud storage.

## 🚀 Key Features

- **Agentic Summarization:** The system autonomously drafts MOMs (Minutes of Meeting), identifies key topics, and maps conversations to specific agendas using advanced LangChain LLM pipelines.
- **Flawless Speech-to-Text:** Uses AssemblyAI Cloud STT for highly accurate multilingual transcription (Hindi, English, Hinglish).
- **Intelligent Task Extraction:** Action items are automatically isolated, categorized, and assigned to respective owners without manual intervention.
- **Google Cloud Integration:** Full archival system using **Google Sheets** as a comprehensive database and **Google Drive** for secure document storage.
- **Board Resolution (BR) Management:** Specialized workflow for high-stakes resolutions with meeting-specific folder archival and governance evidence tracking.
- **Automated Notifications:** Botivate automatically dispatches professional summary emails, task assignments, and absence warnings. It uses a **Google Sheets-backed Queue** processed by **Google Apps Script** to ensure 100% email delivery bypasses cloud platform port restrictions.
- **Dynamic PDF Integration:** Emails include direct, secure **Google Drive download links** for dynamically generated, meticulously styled MOM and Executive Briefing PDFs.
- **Rich Analytics Dashboard:** Gain deep insights into team productivity, meeting frequency trends, attendance rates, and action-item completion metrics.
- **Dynamic White-Labeling:** Fully customizable branding (Company Name, Address, Logo) and optional "Powered by Botivate" attribution via environment variables.
- **Modern & Premium UI:** Designed with a sleek, minimalist dark/light mode interface characterized by glassmorphism, dynamic animations, and brand-consistent styling.

---

## 🧠 System Architecture & Workflow

Below is the high-level workflow of the Botivate Agentic MOM System, outlining how raw data translates into automated cloud-backed archival.

```mermaid
graph TD
    classDef user fill:#eef7ff,stroke:#399dff,stroke-width:2px,color:#000
    classDef agent fill:#bcdeff,stroke:#1b80f5,stroke-width:2px,color:#000
    classDef db fill:#0d1117,stroke:#399dff,stroke-width:2px,color:#fff
    classDef external fill:#f59e0b,stroke:#b45309,stroke-width:2px,color:#000

    A(Admin / HR) -->|"1. Schedules Meeting"| B[Botivate Dashboard]
    B -->|"2. API Router"| C(FastAPI Backend)
    C <-->|"3. Persists Data"| D[(Google Sheets Engine)]
    
    A -->|"4. Uploads Recording"| E{AI Processing Pipeline}
    
    subgraph Intelligence Core
        E -->|"STT Processing"| F[AssemblyAI Transcriber]
        F --> G{LangChain Mapping & Reduction}
        G -->|"Analyzes Context"| H[Aggregated MOM & Executive Brief]
        G -->|"Identifies Tasks"| I[Action Mandates]
    end
    
    H --> J[Finalized Documentation]
    I --> J
    
    J -->|"5. Triggers PDF Engine"| K[ReportLab Generator]
    K -->|"Uploads Archive"| L[Google Drive Storage]
    
    L -->|"6. Triggers Mailer"| M[Automated Email Agent]
    M -->|"7. Dispatches Secure Email"| N((Stakeholders))

    class A,N user;
    class E,F,G,H,I,M agent;
    class D,L db;
    class B,C external;
```

---

## 🛠 Tech Stack

### Frontend
- **React 18** + **Vite**
- **TypeScript**
- **Tailwind CSS v3** (Custom Brand System)
- **Recharts** for Analytics
- **Heroicons / Radix Icons**
- **Zustand** for State Management
- **React Query** for Data Fetching & Caching

### Backend
- **Python 3.10+**
- **FastAPI** (High-performance API framework)
- **LangChain & OpenAI API** (GPT-4o-mini for logical synthesis and mapping/reducing)
- **AssemblyAI** (For highly accurate cloud-based Audio Transcription)
- **Google Sheets API v4** (Real-time Cloud Database and **Email Queuing System**)
- **Google Drive API v3** (Hierarchical Document Storage and Sharing)
- **ReportLab** (Dynamic, aesthetic PDF generation)
- **Google Apps Script** (Automated serverless email processing & delivery)

---

## 📂 Project Structure

```text
📦 MOM_AI_Assistant
 ┣ 📂 backend
 ┃ ┣ 📂 app
 ┃ ┃ ┣ 📂 ai                # Langchain logic, STT config, LLM Prompts
 ┃ ┃ ┣ 📂 api               # FastAPI route endpoints (Meetings, Analytics, Dashboard)
 ┃ ┃ ┣ 📂 models            # Enums & Pydantic validation schemas
 ┃ ┃ ┣ 📂 services          # Core logic (Google Sheets, AssemblyAI, Automation)
 ┃ ┃ ┣ 📂 notifications     # SMTP Email agent & PDF design engine 
 ┃ ┃ ┗ 📜 main.py           # Application entrypoint
 ┃ ┣ 📜 requirements.txt    # Python dependencies
 ┃ ┣ 📜 .env                # API Keys & Cloud Credentials
 ┃ ┗ 📜 google_credentials.json # Service Account Secret
 ┣ 📂 frontend
 ┃ ┣ 📂 src
 ┃ ┃ ┣ 📂 components        # Reusable UI elements (Drawers, Cards, Modals)
 ┃ ┃ ┣ 📂 pages             # Application views (Dashboard, Meeting workflows)
 ┃ ┃ ┣ 📜 App.tsx           # Router configuration
 ┃ ┃ ┗ 📜 index.css         # Global Tailwind directives & Brand tokens
 ┃ ┣ 📜 tailwind.config.js  # Deep-customized brand theme
 ┃ ┗ 📜 package.json        # Node dependencies
 ┣ 📜 README.md             # Project Overview
 ┗ 📜 SETUP.md              # Installation & Deployment instructions
```

---

## ℹ️ Setup & Installation

Please refer to the [SETUP.md](SETUP.md) for local installation and the [CREDENTIALS_GUIDE.md](CREDENTIALS_GUIDE.md) for a detailed step-by-step on obtaining all necessary API keys (OpenAI, AssemblyAI, Gmail SMTP, Google Cloud).

---
*Botivate Services LLP © 2026. Powering Businesses On Autopilot.*