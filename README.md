# Recipe Extractor & Meal Planner

Full-stack app to extract structured recipe data from blog URLs, enrich it, store it, and show it in a clean UI.

## Stack
- Frontend: React + Vite
- Backend: FastAPI + SQLAlchemy
- Scraping: BeautifulSoup + requests
- LLM: Gemini via LangChain (optional key)
- Database: SQLite (local quick start) or PostgreSQL (production)

## Features
- `POST /extract`
- `GET /recipes`
- `GET /recipes/{id}`
- `POST /meal-planner` (bonus)
- Extract tab + Saved History tab + Details modal

## Local Run

### One command
```powershell
powershell -ExecutionPolicy Bypass -File .\run-app.ps1
```

### URLs
- Frontend: `http://localhost:5173`
- Backend: `http://localhost:8000/docs`

## Environment Variables

### `backend/.env`
```env
APP_NAME="Recipe Extractor & Meal Planner"
APP_ENV="dev"
DATABASE_URL="sqlite:///./recipes.db"
FRONTEND_URL="http://localhost:5173"
FRONTEND_URLS=""
GOOGLE_API_KEY=""
GEMINI_MODEL="gemini-1.5-flash"
```

For production PostgreSQL:
```env
DATABASE_URL="postgresql+psycopg2://user:password@host:5432/dbname"
```
(If provider gives `postgres://...`, app auto-normalizes it.)

### `frontend/.env`
```env
VITE_API_BASE=http://localhost:8000
```

## Deploy (Vercel + Render)

### 1) Push repo to GitHub
```powershell
git init
git add .
git commit -m "Deploy-ready setup"
git branch -M main
git remote add origin https://github.com/<your-username>/<your-repo>.git
git push -u origin main
```

### 2) Deploy backend on Render
- Create **Web Service** from this repo.
- Set **Root Directory**: `backend`
- Start Command:
```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```
- Add env vars in Render:
  - `DATABASE_URL` = your Neon/Supabase/Render Postgres URL
  - `FRONTEND_URL` = `https://<your-app>.vercel.app`
  - `FRONTEND_URLS` = optional comma-separated preview URLs
  - `GOOGLE_API_KEY` = optional
  - `GEMINI_MODEL` = `gemini-1.5-flash`

### 3) Deploy frontend on Vercel
- Import same GitHub repo in Vercel
- Set **Root Directory**: `frontend`
- Framework: `Vite`
- Build Command: `npm run build`
- Output Directory: `dist`
- Env var:
  - `VITE_API_BASE=https://<your-backend>.onrender.com`

Redeploy and open your Vercel app URL.

## Required Assignment Folders
- `sample_data/`
- `prompts/`
- `screenshots/`

## Notes
- Use recipe article/blog links, not YouTube/Instagram links.
- No external recipe APIs are used.
- Backend is Python-only (FastAPI).