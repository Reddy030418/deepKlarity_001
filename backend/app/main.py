from collections import defaultdict
import logging
import time

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from .ai import enrich_recipe
from .config import settings
from .database import Base, engine, get_db
from .models import Recipe
from .schemas import (
    ExtractRequest,
    ExtractResponse,
    MealPlannerRequest,
    MealPlannerResponse,
    RecipeDetail,
    RecipeSummary,
)
from .scraper import ScrapeError, scrape_recipe

logger = logging.getLogger(__name__)

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://127.0.0.1:5173"],
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def init_database(max_retries: int = 10, delay_seconds: int = 2) -> None:
    for attempt in range(1, max_retries + 1):
        try:
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            Base.metadata.create_all(bind=engine)
            logger.info("Database connection established.")
            return
        except OperationalError as exc:
            logger.warning(
                "Database not available (attempt %s/%s): %s",
                attempt,
                max_retries,
                exc,
            )
            if attempt < max_retries:
                time.sleep(delay_seconds)
            else:
                raise RuntimeError(
                    "Cannot connect to database at "
                    f"{settings.database_url}. Verify DB settings and retry."
                ) from exc


@app.on_event("startup")
def on_startup() -> None:
    init_database()


@app.get("/")
def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name}


@app.post("/extract", response_model=ExtractResponse)
def extract_recipe(payload: ExtractRequest, db: Session = Depends(get_db)) -> ExtractResponse:
    try:
        scraped = scrape_recipe(str(payload.url))
    except ScrapeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    data = enrich_recipe(scraped)

    recipe = Recipe(
        url=str(payload.url),
        title=data.get("title") or scraped.title,
        cuisine=data.get("cuisine"),
        difficulty=data.get("difficulty"),
        data=data,
    )
    db.add(recipe)
    db.commit()
    db.refresh(recipe)

    return ExtractResponse(recipe_id=recipe.id, data=data)


@app.get("/recipes", response_model=list[RecipeSummary])
def get_recipes(db: Session = Depends(get_db)) -> list[RecipeSummary]:
    return db.query(Recipe).order_by(Recipe.created_at.desc()).all()


@app.get("/recipes/{recipe_id}", response_model=RecipeDetail)
def get_recipe(recipe_id: int, db: Session = Depends(get_db)) -> RecipeDetail:
    recipe = db.query(Recipe).filter(Recipe.id == recipe_id).first()
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return recipe


@app.post("/meal-planner", response_model=MealPlannerResponse)
def meal_planner(payload: MealPlannerRequest, db: Session = Depends(get_db)) -> MealPlannerResponse:
    recipes = db.query(Recipe).filter(Recipe.id.in_(payload.recipe_ids)).all()
    if not recipes:
        raise HTTPException(status_code=404, detail="No recipes found for provided ids")

    combined: dict[str, set[str]] = defaultdict(set)

    for recipe in recipes:
        shopping = (recipe.data or {}).get("shopping_list", {})
        if isinstance(shopping, dict):
            for category, items in shopping.items():
                if isinstance(items, list):
                    for item in items:
                        if isinstance(item, str) and item.strip():
                            combined[category].add(item.strip())

    combined_sorted = {k: sorted(v) for k, v in combined.items()}

    selected = [RecipeSummary.model_validate(r) for r in recipes]
    return MealPlannerResponse(selected_recipes=selected, combined_shopping_list=combined_sorted)
