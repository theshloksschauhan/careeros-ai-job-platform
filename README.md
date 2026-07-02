<div align="center">
  
  # 🚀 CareerOS
  **The Next-Generation AI-Powered Job Application Platform**
  
  [![React](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=black)](https://react.dev/)
  [![FastAPI](https://img.shields.io/badge/FastAPI-0.110-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
  [![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-47A248?logo=mongodb&logoColor=white)](https://www.mongodb.com/)
  [![Tailwind CSS](https://img.shields.io/badge/Tailwind-CSS-38B2AC?logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)
  [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

  <p align="center">
    Fit Analysis • Resume Rewrite • Cover Letters • Interview Prep • Salary Negotiation • ATS Scoring
  </p>

</div>

---

## 🌟 Live Demo
* **Live Web App:** <paste deployed frontend URL here>
* **Backend API:** <paste deployed backend URL here>

---

## ✨ Core Features
CareerOS utilizes a pipeline of 5 parallel AI agents to supercharge your job hunt:

- 📊 **Fit Analysis & ATS Scoring:** Evaluates your resume against a target job description to generate a real-time match rate.
- ✍️ **Resume Rewrite:** Intelligently suggests optimized, impact-driven bullet points tailored to bypass ATS filters.
- ✉️ **Cover Letter Generation:** Drafts compelling, modern cover letters with engaging hooks tailored to the company.
- 🎯 **Mock Interview Pack:** Generates personalized behavioral and technical interview questions using the STAR method.
- 💰 **Salary Negotiation Coach:** Estimates your market value and scripts negotiation scenarios based on your exact profile.
- 🎙️ **Voice Mock Interview (Stretch):** Practice your interview answers live using browser speech recognition.
- 📅 **Calendar Integration (Stretch):** Export a 1-week follow-up reminder directly as an `.ics` file.

---

## 🛠️ Technology Stack

### Frontend
- **Framework:** React 19
- **Styling:** Tailwind CSS, shadcn/ui
- **Animation:** Framer Motion
- **Hosting:** Vercel

### Backend
- **Framework:** FastAPI (Python)
- **Database:** MongoDB (Motor Asyncio)
- **Performance:** Gzip compression, Advanced Security Headers
- **AI Core:** OpenAI API compatibility layer (`asyncio.gather` for parallel agent execution)
- **Hosting:** Render

---

## 🐳 Quick Start (Docker)

The fastest way to get CareerOS running locally is via Docker.

1. **Configure Environment Variables**
   ```bash
   cp backend/.env.example backend/.env
   cp frontend/.env.example frontend/.env
   ```
   *Edit the `.env` files to include your MongoDB URI, JWT Secret, and AI API keys.*

2. **Spin up the stack**
   ```bash
   docker compose up --build
   ```

* 🌐 **Frontend:** `http://localhost:3000`
* ⚙️ **Backend API:** `http://localhost:8000/api`
* 🔑 **Default Admin Email:** `admin@careeros.ai` *(Password will be logged to the terminal if not explicitly set).*

---

## 💻 Local Development (Without Docker)

### Prerequisites
- Node.js 20+ & Yarn
- Python 3.11+
- MongoDB instance

### Backend Setup
```bash
cd backend
python -m venv venv

# Activate Virtual Environment
# Windows: venv\Scripts\activate
# macOS/Linux: source venv/bin/activate

pip install -r requirements.txt
cp .env.example .env   # Configure MONGO_URL, JWT_SECRET, OPENROUTER_API_KEY
uvicorn server:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup
```bash
cd frontend
yarn install
cp .env.example .env
yarn start
```

---

## ⚙️ Environment Variables

| Variable | Location | Description |
|----------|----------|-------------|
| `MONGO_URL` | backend | MongoDB connection string |
| `DB_NAME` | backend | Database name |
| `JWT_SECRET` | backend | Secret for JWT signing |
| `OPENROUTER_API_KEY` | backend | Primary AI API key |
| `FRONTEND_URL` | backend | Comma-separated CORS origins |
| `COOKIE_SECURE` | backend | `true` in production HTTPS |
| `ADMIN_EMAIL` | backend | Initial admin email |
| `ADMIN_PASSWORD` | backend | Initial admin password or generated fallback |
| `REACT_APP_BACKEND_URL` | frontend | Backend base URL |

---

## 🚀 Deployment Guide

1. **Database:** Create a free MongoDB Atlas cluster and grab the connection string.
2. **Backend (Render):** Deploy using `render.yaml`. Set `MONGO_URL`, `JWT_SECRET`, `OPENROUTER_API_KEY`, `FRONTEND_URL` (to your Vercel URL), and `COOKIE_SECURE=true`.
3. **Frontend (Vercel):** Deploy the `/frontend` directory. Set `REACT_APP_BACKEND_URL` as a Vercel build-time environment variable.
4. **CORS Validation:** Once the frontend is live, update the `FRONTEND_URL` on Render to match the Vercel domain and redeploy.

---

## 📡 API Overview

| Method | Path | Description |
|--------|------|-------------|
| **POST** | `/api/auth/register` | Create account |
| **POST** | `/api/auth/login` | Sign in |
| **GET** | `/api/auth/me` | Current user |
| **PATCH** | `/api/auth/profile` | Update name/password |
| **POST** | `/api/applications` | Create application |
| **GET** | `/api/applications` | List applications (paginated) |
| **POST** | `/api/applications/{id}/run` | Run 5-agent AI pipeline |
| **GET** | `/api/health` | Health check |
| **GET** | `/api/admin/stats` | Admin system stats |

---

## 📋 Pre-Flight Submission Checklist
*For Capstone Evaluation purposes:*
- [ ] **Incognito Test:** All live links open in an incognito window without forcing a login.
- [ ] **Public Repo:** The GitHub repository is set to Public.
- [ ] **Structure:** The repo contains both `/frontend` and `/backend` folders and this `README.md`.
- [ ] **Video:** Demo video is under 5 minutes long.
- [ ] **Presentation:** Presentation slide links are set to "anyone with the link can view".

---
*Built with ❤️ for the Capstone Project.*
