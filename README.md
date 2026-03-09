# Botivate: Agentic Minutes of Meeting (MOM) System

![Botivate Logo](frontend/public/botivate-logo-cropped.png)

Botivate is an intelligent, agentic system designed to autonomously handle, analyze, and document your meeting minutes on autopilot. By leveraging AI capabilities, Botivate transforms unstructured meeting interactions into highly structured, actionable intelligence.

## 🚀 Key Features

- **Agentic Summarization:** The system autonomously drafts MOMs (Minutes of Meeting), identifies key topics, and maps conversations to specific agendas.
- **Intelligent Task Extraction:** Action items are automatically isolated, categorized, and assigned to respective owners without manual intervention.
- **Automated Notifications & Execution:** Botivate automatically sends professional summary emails with dynamically generated, meticulously styled **PDF attachments** directly to stakeholders.
- **Rich Analytics Dashboard:** Gain deep insights into team productivity, meeting frequency trends, attendance rates, and action-item completion metrics.
- **Modern & Premium UI:** Designed with a sleek, minimalist dark/light mode interface characterized by glassmorphism, dynamic animations, and brand-consistent `#399dff` styling.

---

## 🧠 System Architecture & Workflow

Below is the high-level workflow of the Botivate Agentic MOM System, outlining how raw data translates into automated task resolution.

```mermaid
graph TD
    classDef user fill:#eef7ff,stroke:#399dff,stroke-width:2px,color:#000
    classDef agent fill:#bcdeff,stroke:#1b80f5,stroke-width:2px,color:#000
    classDef db fill:#0d1117,stroke:#399dff,stroke-width:2px,color:#fff
    classDef external fill:#f59e0b,stroke:#b45309,stroke-width:2px,color:#000

    A(HR / System Administrator) -->|"1. Schedules Meeting"| B[Botivate Dashboard]
    B -->|"2. Meeting API"| C(FastAPI Backend)
    C <-->|"3. Persists Data"| D[(PostgreSQL Database)]
    
    A -->|"4. Triggers Record MOM"| E{Agentic MOM Processor}
    
    subgraph AI Processing Core
        E -->|"Analyzes Context & Sentiment"| F[Agenda Extraction]
        E -->|"Identifies Action Items"| G[Task Generation]
        E -->|"Calculates Metrics"| H[Analytic Aggregation]
    end
    
    F --> I[Finalized Documentation]
    G --> I
    H --> I
    
    I -->|"5. Triggers PDF Engine"| J[PDF Generator Module]
    J -->|"Generates & Encrypts"| K[Structured MOM PDF]
    
    K -->|"6. Triggers Mailer"| L[Automated Email Agent]
    L -->|"7. Dispatches Secure Email"| M((Stakeholders / Attendees))

    class A,M user;
    class E,F,G,H,J,L agent;
    class D db;
    class B,C external;
```

---

## 🛠 Tech Stack

### Frontend
- **React 18** + **Vite**
- **TypeScript**
- **Tailwind CSS v3** (Custom Brand System)
- **Recharts** for Analytics
- **Heroicons** for SVG Iconography
- **Zustand** for State Management
- **React Query** for Data Fetching & Caching

### Backend
- **Python 3.10+**
- **FastAPI** (High-performance API framework)
- **SQLAlchemy ORM** + **PostgreSQL**
- **ReportLab** for dynamic, aesthetic PDF Generation
- **FastAPI-Mail** for asynchronous Email Delivery

---

## 📂 Project Structure

```text
📦 MOM_AI_Assistant
 ┣ 📂 backend
 ┃ ┣ 📂 app
 ┃ ┃ ┣ 📂 api               # FastAPI route endpoints
 ┃ ┃ ┣ 📂 models            # SQLAlchemy database schemas
 ┃ ┃ ┣ 📂 schemas           # Pydantic validation schemas
 ┃ ┃ ┣ 📂 services          # Core business logic & Agentic services
 ┃ ┃ ┣ 📂 notifications     # Email server & PDF Generation logic
 ┃ ┃ ┣ 📜 main.py           # Application entrypoint
 ┃ ┃ ┗ 📜 database.py       # DB Connection pooling
 ┃ ┣ 📜 requirements.txt    # Python dependencies
 ┃ ┗ 📜 .env                # Environment variables
 ┣ 📂 frontend
 ┃ ┣ 📂 src
 ┃ ┃ ┣ 📂 components        # Reusable UI components (Stats, Drawers, Layout)
 ┃ ┃ ┣ 📂 pages             # Application views (Dashboard, Meetings, Detail)
 ┃ ┃ ┣ 📂 store             # Zustand global state (Theme)
 ┃ ┃ ┣ 📜 App.tsx           # Router configuration
 ┃ ┃ ┗ 📜 index.css         # Global Tailwind directives & Brand tokens
 ┃ ┣ 📜 tailwind.config.js  # Deep-customized brand theme
 ┃ ┣ 📜 vite.config.ts      # Vite bundler config
 ┃ ┗ 📜 package.json        # Node dependencies
 ┣ 📜 README.md             # Project Overview
 ┗ 📜 SETUP.md              # Installation & Deployment instructions
```

---

## ℹ️ Setup & Installation

Please refer to the [SETUP.md](SETUP.md) file for comprehensive, step-by-step instructions on running Botivate locally and deploying it to production servers.

---
*Botivate Services LLP © 2026. Powering Businesses On Autopilot.*