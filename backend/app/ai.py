import json
from pathlib import Path
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from .config import settings
from .scraper import ScrapedRecipe, parse_ingredient_line

PROMPT_DIR = Path(__file__).resolve().parents[2] / "prompts"

NUTRITION_HINTS: dict[str, dict[str, float]] = {
    "chicken": {"calories": 220, "protein": 27, "carbs": 0, "fat": 12},
    "beef": {"calories": 280, "protein": 26, "carbs": 0, "fat": 18},
    "paneer": {"calories": 265, "protein": 18, "carbs": 6, "fat": 20},
    "cheese": {"calories": 110, "protein": 7, "carbs": 1, "fat": 9},
    "rice": {"calories": 180, "protein": 4, "carbs": 39, "fat": 1},
    "pasta": {"calories": 210, "protein": 7, "carbs": 42, "fat": 1},
    "potato": {"calories": 120, "protein": 3, "carbs": 27, "fat": 0},
    "butter": {"calories": 100, "protein": 0, "carbs": 0, "fat": 11},
    "oil": {"calories": 120, "protein": 0, "carbs": 0, "fat": 14},
    "milk": {"calories": 90, "protein": 5, "carbs": 7, "fat": 5},
    "egg": {"calories": 70, "protein": 6, "carbs": 0, "fat": 5},
    "flour": {"calories": 110, "protein": 3, "carbs": 23, "fat": 0},
    "sugar": {"calories": 50, "protein": 0, "carbs": 13, "fat": 0},
}

PRODUCE_KEYS = {
    "onion",
    "tomato",
    "garlic",
    "ginger",
    "lemon",
    "lime",
    "cilantro",
    "coriander",
    "spinach",
    "carrot",
    "potato",
    "chili",
    "pepper",
}
DAIRY_KEYS = {"milk", "butter", "cheese", "paneer", "cream", "yogurt", "curd"}
BAKERY_KEYS = {"bread", "bun", "roll", "tortilla", "pita"}


def _load_prompt(name: str, fallback: str) -> str:
    path = PROMPT_DIR / name
    if path.exists():
        return path.read_text(encoding="utf-8")
    return fallback


SYSTEM_PROMPT = _load_prompt(
    "recipe_extraction_prompt.txt",
    "You are a cooking assistant. Return strict JSON only.",
)

ENHANCEMENT_PROMPT = _load_prompt(
    "recipe_enhancement_prompt.txt",
    "Enhance recipe details and return strict JSON only.",
)


def _strip_json(text: str) -> str:
    cleaned = (text or "").strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.replace("```json", "").replace("```", "").strip()
    return cleaned


def _normalize_ingredients(raw_ingredients: Any) -> list[dict[str, str]]:
    if not isinstance(raw_ingredients, list):
        return []

    normalized: list[dict[str, str]] = []
    for entry in raw_ingredients:
        if isinstance(entry, dict):
            quantity = str(entry.get("quantity", "")).strip()
            unit = str(entry.get("unit", "")).strip()
            item = str(entry.get("item", "")).strip()
            if item:
                normalized.append({"quantity": quantity, "unit": unit, "item": item})
        elif isinstance(entry, str):
            parsed = parse_ingredient_line(entry)
            if parsed["item"]:
                normalized.append(parsed)

    return normalized


def _normalize_instructions(raw_instructions: Any) -> list[str]:
    if not isinstance(raw_instructions, list):
        return []

    steps: list[str] = []
    for step in raw_instructions:
        if isinstance(step, str) and step.strip():
            steps.append(step.strip())
        elif isinstance(step, dict):
            text = step.get("text") or step.get("name")
            if isinstance(text, str) and text.strip():
                steps.append(text.strip())

    return steps


def _estimate_nutrition(ingredients: list[dict[str, str]]) -> dict[str, str]:
    calories = 0.0
    protein = 0.0
    carbs = 0.0
    fat = 0.0

    for ing in ingredients:
        item_lower = ing.get("item", "").lower()
        for key, values in NUTRITION_HINTS.items():
            if key in item_lower:
                calories += values["calories"]
                protein += values["protein"]
                carbs += values["carbs"]
                fat += values["fat"]
                break

    if calories == 0:
        calories = 320
        protein = 10
        carbs = 35
        fat = 14

    return {
        "calories": f"{int(round(calories))} kcal",
        "protein": f"{int(round(protein))} g",
        "carbs": f"{int(round(carbs))} g",
        "fat": f"{int(round(fat))} g",
    }


def _infer_difficulty(ingredient_count: int, step_count: int) -> str:
    score = ingredient_count + step_count
    if score <= 8:
        return "Easy"
    if score <= 16:
        return "Medium"
    return "Hard"


def _generate_substitutions(ingredients: list[dict[str, str]]) -> list[str]:
    items = " ".join(ing.get("item", "").lower() for ing in ingredients)
    suggestions: list[str] = []

    if "butter" in items:
        suggestions.append("Replace butter with olive oil for a lighter option.")
    if "cream" in items or "milk" in items:
        suggestions.append("Use unsweetened almond milk or coconut milk as a dairy alternative.")
    if "flour" in items:
        suggestions.append("Swap all-purpose flour with oat flour for a gluten-friendly variation.")
    if "sugar" in items:
        suggestions.append("Replace sugar with honey or maple syrup in equal sweetness.")
    if "chicken" in items:
        suggestions.append("Use paneer or tofu instead of chicken for a vegetarian version.")

    defaults = [
        "Use olive oil in place of butter where possible.",
        "Use whole wheat options for higher fiber.",
        "Adjust spice level by replacing hot chili with paprika.",
    ]

    for default in defaults:
        if len(suggestions) >= 3:
            break
        suggestions.append(default)

    return suggestions[:3]


def _categorize_item(item: str) -> str:
    lowered = item.lower()
    if any(key in lowered for key in PRODUCE_KEYS):
        return "Produce"
    if any(key in lowered for key in DAIRY_KEYS):
        return "Dairy"
    if any(key in lowered for key in BAKERY_KEYS):
        return "Bakery"
    if any(k in lowered for k in ["salt", "pepper", "oil", "flour", "rice", "sugar", "spice"]):
        return "Pantry"
    return "Other"


def _build_shopping_list(ingredients: list[dict[str, str]]) -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = {"Produce": [], "Dairy": [], "Bakery": [], "Pantry": [], "Other": []}

    for ing in ingredients:
        item = ing.get("item", "").strip()
        if not item:
            continue
        category = _categorize_item(item)
        if item not in grouped[category]:
            grouped[category].append(item)

    return {key: val for key, val in grouped.items() if val}


def _related_from_context(title: str, cuisine: str, ingredients: list[dict[str, str]]) -> list[str]:
    t = (title or "").lower()
    c = (cuisine or "").lower()
    items = " ".join(ing.get("item", "").lower() for ing in ingredients)

    if "pasta" in t or "ital" in c:
        return ["Garlic Bread", "Minestrone Soup", "Caprese Salad"]
    if "curry" in t or "indian" in c:
        return ["Jeera Rice", "Cucumber Raita", "Dal Tadka"]
    if "sandwich" in t or "bread" in items:
        return ["Tomato Soup", "Corn Salad", "Herb Potato Wedges"]
    if "chicken" in items:
        return ["Lemon Rice", "Sauteed Vegetables", "Yogurt Dip"]
    return ["Fresh Green Salad", "Roasted Vegetables", "Classic Soup"]


def _normalize_payload(raw: dict[str, Any], scraped: ScrapedRecipe) -> dict[str, Any]:
    ingredients = _normalize_ingredients(raw.get("ingredients") or scraped.ingredients)
    instructions = _normalize_instructions(raw.get("instructions") or scraped.instructions)

    title = str(raw.get("title") or scraped.title or "Untitled Recipe")
    cuisine = str(raw.get("cuisine") or scraped.cuisine or "Unknown")
    prep_time = str(raw.get("prep_time") or scraped.prep_time or "Unknown")
    cook_time = str(raw.get("cook_time") or scraped.cook_time or "Unknown")
    total_time = str(raw.get("total_time") or scraped.total_time or "Unknown")
    servings = str(raw.get("servings") or scraped.servings or "Unknown")

    difficulty = str(raw.get("difficulty") or "").strip()
    if not difficulty:
        difficulty = _infer_difficulty(len(ingredients), len(instructions))

    nutrition = raw.get("nutrition") or raw.get("nutrition_estimate")
    if not isinstance(nutrition, dict):
        nutrition = _estimate_nutrition(ingredients)

    substitutions = raw.get("substitutions")
    if not isinstance(substitutions, list) or not substitutions:
        substitutions = _generate_substitutions(ingredients)

    shopping_list = raw.get("shopping_list")
    if not isinstance(shopping_list, dict) or not shopping_list:
        shopping_list = _build_shopping_list(ingredients)

    related = raw.get("related_recipes")
    if not isinstance(related, list) or not related:
        related = _related_from_context(title, cuisine, ingredients)

    return {
        "title": title,
        "cuisine": cuisine,
        "prep_time": prep_time,
        "cook_time": cook_time,
        "total_time": total_time,
        "servings": servings,
        "difficulty": difficulty,
        "ingredients": ingredients,
        "instructions": instructions,
        "nutrition": {
            "calories": str(nutrition.get("calories", "Unknown")),
            "protein": str(nutrition.get("protein", "Unknown")),
            "carbs": str(nutrition.get("carbs", "Unknown")),
            "fat": str(nutrition.get("fat", "Unknown")),
        },
        "substitutions": [str(v) for v in substitutions][:3],
        "shopping_list": shopping_list,
        "related_recipes": [str(v) for v in related][:3],
    }


def enrich_recipe(scraped: ScrapedRecipe) -> dict[str, Any]:
    if not settings.google_api_key:
        return _normalize_payload({}, scraped)

    llm = ChatGoogleGenerativeAI(
        model=settings.gemini_model,
        google_api_key=settings.google_api_key,
        temperature=0.1,
    )

    payload = {
        "source_url": scraped.source_url,
        "title": scraped.title,
        "cuisine": scraped.cuisine,
        "prep_time": scraped.prep_time,
        "cook_time": scraped.cook_time,
        "total_time": scraped.total_time,
        "servings": scraped.servings,
        "ingredients": scraped.ingredients,
        "instructions": scraped.instructions,
        "text_excerpt": scraped.text[:5000],
    }

    user_prompt = f"""
Raw recipe content:
{json.dumps(payload, ensure_ascii=False)}

Task A:
{SYSTEM_PROMPT}

Task B:
{ENHANCEMENT_PROMPT}

Return one JSON object with keys:
title, cuisine, prep_time, cook_time, total_time, servings, difficulty,
ingredients (as list of objects with quantity, unit, item), instructions,
nutrition, substitutions, shopping_list, related_recipes.
"""

    try:
        response = llm.invoke(
            [
                SystemMessage(content="You are a strict JSON generator for cooking data."),
                HumanMessage(content=user_prompt),
            ]
        )
        parsed = json.loads(_strip_json(response.content))
        return _normalize_payload(parsed, scraped)
    except Exception:
        return _normalize_payload({}, scraped)