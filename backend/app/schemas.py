from datetime import datetime
from typing import Any

from pydantic import BaseModel, HttpUrl


class ExtractRequest(BaseModel):
    url: HttpUrl


class MealPlannerRequest(BaseModel):
    recipe_ids: list[int]


class RecipeSummary(BaseModel):
    id: int
    title: str
    cuisine: str | None = None
    difficulty: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class RecipeDetail(BaseModel):
    id: int
    url: str
    title: str
    cuisine: str | None = None
    difficulty: str | None = None
    created_at: datetime
    data: dict[str, Any]

    class Config:
        from_attributes = True


class ExtractResponse(BaseModel):
    recipe_id: int
    data: dict[str, Any]


class MealPlannerResponse(BaseModel):
    selected_recipes: list[RecipeSummary]
    combined_shopping_list: dict[str, list[str]]
