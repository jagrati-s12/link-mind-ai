# LinkMind AI — Personal AI Learning & Opportunity Intelligence Platform

LinkMind AI is an advanced, full-stack personal intelligence platform designed to aggregate, structure, and synthesize learning resources, career opportunities, skills, and roadmaps. Built with a robust FastAPI backend and a modern React & Tailwind CSS frontend, LinkMind AI transforms messy career data into actionable, personalized growth paths.

---

## 🌟 Key Features

- **AI-Powered Opportunity Intelligence & Extraction**: Ingests, parses, and extracts structured skills, requirements, and metadata from job boards, GitHub repositories, and custom URLs using intelligent LLM adapters.
- **Personalized Skill Roadmaps & Growth Tracks**: Generates tailored multi-track roadmaps (including Core Backend SDE, Cloud DevOps, AI Engineer, and Advanced Algorithms) with interactive milestones, subtopics, importance levels, and progress tracking.
- **Course Tracker & Resource Hub**: Manages learning resources, courses, tutorials, hackathons, internships, and job applications with deep automated categorization and relationship mapping.
- **Interactive AI Assistant**: Chat with an AI assistant grounded in your personal library and skills profile to get career guidance, course recommendations, and roadmap adjustments.
- **Collections & Automated Resource Routing**: Organizes resources into smart collections with automatic tagging, auto-connect recommendations, and feedback loops.
- **Analytics & Dashboard**: Comprehensive stats dashboard tracking skill acquisition, application progress, and learning momentum.

---

## 🏗️ Architecture & Tech Stack

### Backend (`/backend`)
- **Framework**: FastAPI (Python) with async lifespan support and SQLAlchemy ORM.
- **Database**: SQLite (local development) / SQLAlchemy with Alembic migrations.
- **Intelligence & Processing**: Custom LLM adapters, heuristic extractors, skill extraction pipelines, and automated source fetching (GitHub raw readmes, job boards, and web pages).
- **Security & Core**: JWT authentication, password hashing, SSRF protection (`ssrf.py`), and CORS middleware.

### Frontend (`/frontend`)
- **Framework**: React (Vite) with Tailwind CSS.
- **Components & Views**: Rich modular views including Dashboard, Assistant, Roadmaps, Courses, CourseTracker, Jobs, Internships, Hackathons, Collections, Resources, Profile, Settings, and CaptureModal.
- **State & Context**: React Context providers (`AuthProvider`, `ThemeProvider`) and centralized API services (`frontend/src/services/api.js`).

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+ & npm

### 1. Backend Setup
```bash
cd backend
python -m venv venv
# Activate virtual environment
# On Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# On macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt # (or install dependencies via pyproject.toml / site-packages)
uvicorn app.main:app --reload --port 8000
```

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

---

## 🔌 API Endpoints (v1)
- **Auth**: `/api/v1/auth` (Register, Login, Token generation)
- **Profile**: `/api/v1/profile` (User profile management)
- **Resources**: `/api/v1/resources` & `/api/v1/sources` (Resource management & URL ingestion)
- **Collections**: `/api/v1/collections` (Smart resource grouping)
- **Skills & Roadmaps**: `/api/v1/skills`, `/api/v1/roadmaps` (Skill intelligence & career tracks)
- **Applications & Tracker**: `/api/v1/applications`, `/api/v1/course-tracker` (Job/Internship tracking & course progress)
- **Assistant**: `/api/v1/assistant` (RAG-powered conversational learning assistant)
- **Stats & Feedback**: `/api/v1/stats`, `/api/v1/feedback` (User metrics and submission feedback)

---

## 📄 License
This project is open-source and available under the MIT License.
