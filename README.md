# Recipe Extractor & Meal Planner (Beginner Version)

A full-stack project that takes a recipe blog URL and converts it into structured recipe data.

## Features

- `POST /extract`: scrape recipe pages with BeautifulSoup, enrich with Gemini (LangChain), and save to PostgreSQL.
- `GET /recipes`: list saved recipe history.
- `GET /recipes/{id}`: full recipe details.
- `POST /meal-planner` (bonus): combine shopping lists from 3-5 selected recipes.
- React UI with two tabs:
  - Extract Recipe
  - Saved Recipes (table + details modal)

## Tech Stack

- Backend: FastAPI, SQLAlchemy
- AI: LangChain + Gemini (`langchain-google-genai`)
- Scraping: BeautifulSoup + requests
- DB: PostgreSQL
- Frontend: React + Vite

## Project Structure

```text
backend/
  app/
    ai.py
    config.py
    database.py
    main.py
    models.py
    scraper.py
    schemas.py
  requirements.txt
  .env.example
frontend/
  src/
    components/
      ExtractTab.jsx
      SavedTab.jsx
      RecipeModal.jsx
    api.js
    App.jsx
    main.jsx
    styles.css
  package.json
  .env.example
prompts/
  recipe_extraction_prompt.txt
  recipe_enhancement_prompt.txt
sample_data/
  sample_extract_response.json
screenshots/
  README.txt
docker-compose.yml
README.md
```

## Setup

### 1) Start PostgreSQL

```bash
docker compose up -d
```

### 2) Backend

```bash
cd backend
python -m venv .venv
# Windows
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload
```

Backend runs on `http://localhost:8000`.

### 3) Frontend

```bash
cd frontend
npm install
copy .env.example .env
npm run dev
```

Frontend runs on `http://localhost:5173`.

## Environment Variables

### backend/.env

- `DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/recipes_db`
- `FRONTEND_URL=http://localhost:5173`
- `GOOGLE_API_KEY=your_google_api_key` (optional)
- `GEMINI_MODEL=gemini-1.5-flash`

If `GOOGLE_API_KEY` is empty, the app uses fallback enrichment logic so the app still works.

## API Examples

### Extract

```http
POST /extract
Content-Type: application/json

{
  "url": "https://example.com/recipe"
}
```

### List

```http
GET /recipes
```

### Detail

```http
GET /recipes/1
```

### Bonus Meal Planner

```http
POST /meal-planner
Content-Type: application/json

{
  "recipe_ids": [1, 2, 3]
}
```

## Beginner Milestones

1. URL -> scrape title + ingredients
2. Add AI enrichment
3. Save to DB
4. Build frontend tabs + modal

## Notes

- No external recipe APIs are used.
- Node.js is used only for frontend tooling (React + Vite), not backend logic.
- Add screenshots to the `screenshots/` folder before submission.
