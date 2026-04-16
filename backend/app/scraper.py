import json
import re
from dataclasses import dataclass
from typing import Any

import requests
from bs4 import BeautifulSoup


@dataclass
class ScrapedRecipe:
    source_url: str
    title: str
    text: str
    ingredients: list[str]
    instructions: list[str]
    prep_time: str
    cook_time: str
    total_time: str
    servings: str
    cuisine: str


class ScrapeError(Exception):
    pass


VIDEO_HOST_HINTS = [
    "youtube.com",
    "youtu.be",
    "instagram.com",
    "tiktok.com",
    "facebook.com",
]

COMMON_UNITS = {
    "cup",
    "cups",
    "tbsp",
    "tablespoon",
    "tablespoons",
    "tsp",
    "teaspoon",
    "teaspoons",
    "g",
    "kg",
    "oz",
    "lb",
    "lbs",
    "ml",
    "l",
    "clove",
    "cloves",
    "slice",
    "slices",
    "piece",
    "pieces",
    "can",
    "cans",
}


def _clean_lines(value: str) -> list[str]:
    lines = [line.strip(" -•\t") for line in value.splitlines()]
    return [line for line in lines if line]


def _to_human_duration(value: str | None) -> str:
    if not value:
        return "Unknown"
    raw = value.strip()
    if not raw:
        return "Unknown"
    if not raw.upper().startswith("PT"):
        return raw

    h_match = re.search(r"(\d+)H", raw.upper())
    m_match = re.search(r"(\d+)M", raw.upper())
    hours = int(h_match.group(1)) if h_match else 0
    minutes = int(m_match.group(1)) if m_match else 0

    if hours == 0 and minutes == 0:
        return "Unknown"
    if hours and minutes:
        return f"{hours} hr {minutes} mins"
    if hours:
        return f"{hours} hr"
    return f"{minutes} mins"


def parse_ingredient_line(line: str) -> dict[str, str]:
    cleaned = re.sub(r"\s+", " ", (line or "").strip())
    if not cleaned:
        return {"quantity": "", "unit": "", "item": ""}

    pattern = (
        r"^\s*"
        r"(?P<quantity>\d+\s+\d+\/\d+|\d+\/\d+|\d+(?:\.\d+)?)?"
        r"\s*"
        r"(?P<unit>[a-zA-Z]+)?"
        r"\s*"
        r"(?P<item>.*)$"
    )
    match = re.match(pattern, cleaned)
    if not match:
        return {"quantity": "", "unit": "", "item": cleaned}

    quantity = (match.group("quantity") or "").strip()
    unit = (match.group("unit") or "").strip().lower()
    item = (match.group("item") or "").strip(" ,-")

    if unit and unit not in COMMON_UNITS:
        item = f"{unit} {item}".strip()
        unit = ""

    if not item:
        item = cleaned

    return {"quantity": quantity, "unit": unit, "item": item}


def _iter_json_nodes(payload: Any) -> list[dict[str, Any]]:
    nodes: list[dict[str, Any]] = []
    stack: list[Any] = [payload]

    while stack:
        current = stack.pop()
        if isinstance(current, list):
            stack.extend(current)
            continue
        if isinstance(current, dict):
            nodes.append(current)
            if "@graph" in current and isinstance(current["@graph"], list):
                stack.extend(current["@graph"])
            if "itemListElement" in current and isinstance(current["itemListElement"], list):
                stack.extend(current["itemListElement"])

    return nodes


def _extract_instructions(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value.strip()] if value.strip() else []
    if not isinstance(value, list):
        return []

    steps: list[str] = []
    for step in value:
        if isinstance(step, str):
            if step.strip():
                steps.append(step.strip())
            continue

        if isinstance(step, dict):
            text = step.get("text") or step.get("name")
            if isinstance(text, str) and text.strip():
                steps.append(text.strip())

            nested = step.get("itemListElement")
            if nested:
                steps.extend(_extract_instructions(nested))

    return steps


def _extract_from_ld_json(soup: BeautifulSoup) -> dict[str, Any]:
    result: dict[str, Any] = {
        "title": "",
        "ingredients": [],
        "instructions": [],
        "prep_time": "Unknown",
        "cook_time": "Unknown",
        "total_time": "Unknown",
        "servings": "Unknown",
        "cuisine": "Unknown",
    }

    for script in soup.find_all("script", type="application/ld+json"):
        try:
            payload = json.loads(script.string or script.get_text() or "")
        except Exception:
            continue

        for item in _iter_json_nodes(payload):
            rtype = item.get("@type")
            is_recipe = rtype == "Recipe" or (isinstance(rtype, list) and "Recipe" in rtype)
            if not is_recipe:
                continue

            result["title"] = item.get("name") or result["title"]
            result["ingredients"] = item.get("recipeIngredient") or result["ingredients"]
            result["instructions"] = _extract_instructions(item.get("recipeInstructions")) or result["instructions"]

            if item.get("prepTime"):
                result["prep_time"] = _to_human_duration(item.get("prepTime"))
            if item.get("cookTime"):
                result["cook_time"] = _to_human_duration(item.get("cookTime"))
            if item.get("totalTime"):
                result["total_time"] = _to_human_duration(item.get("totalTime"))

            recipe_yield = item.get("recipeYield")
            if isinstance(recipe_yield, list):
                result["servings"] = ", ".join(str(v) for v in recipe_yield if v) or result["servings"]
            elif recipe_yield:
                result["servings"] = str(recipe_yield)

            cuisine = item.get("recipeCuisine")
            if isinstance(cuisine, list):
                result["cuisine"] = ", ".join(str(v) for v in cuisine if v) or result["cuisine"]
            elif cuisine:
                result["cuisine"] = str(cuisine)

    return result


def _extract_heuristic(soup: BeautifulSoup) -> tuple[list[str], list[str]]:
    ingredients: list[str] = []
    instructions: list[str] = []

    ingredient_sections = soup.find_all(
        lambda tag: tag.name in ["ul", "ol"]
        and tag.get("class")
        and any("ingredient" in cls.lower() for cls in tag.get("class", []))
    )
    for section in ingredient_sections:
        for li in section.find_all("li"):
            text = li.get_text(" ", strip=True)
            if text:
                ingredients.append(text)

    instruction_sections = soup.find_all(
        lambda tag: tag.name in ["ol", "ul", "div"]
        and tag.get("class")
        and any(
            key in cls.lower()
            for cls in tag.get("class", [])
            for key in ["instruction", "direction", "method", "step"]
        )
    )
    for section in instruction_sections:
        for li in section.find_all(["li", "p"]):
            text = li.get_text(" ", strip=True)
            if text:
                instructions.append(text)

    if not ingredients:
        text = soup.get_text("\n")
        maybe_ingredients = re.findall(
            r"(?im)^\s*(?:\d+\/?\d*\s+)?(?:cup|tbsp|tsp|gram|g|kg|oz|ml|l)?\s*[a-z][^\n]{2,}$",
            text,
        )
        ingredients = [item.strip() for item in maybe_ingredients[:20]]

    return ingredients[:60], instructions[:80]


def scrape_recipe(url: str) -> ScrapedRecipe:
    lowered_url = url.lower()
    if any(host in lowered_url for host in VIDEO_HOST_HINTS):
        raise ScrapeError("Please provide a recipe blog/article URL, not a video/social link.")

    try:
        response = requests.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
    except Exception as exc:
        raise ScrapeError(f"Failed to fetch URL: {exc}") from exc

    soup = BeautifulSoup(response.text, "html.parser")
    doc_title = (soup.title.string or "").strip() if soup.title else "Untitled Recipe"

    ld = _extract_from_ld_json(soup)
    h_ingredients, h_instructions = _extract_heuristic(soup)

    title = ld["title"] or doc_title
    ingredients = ld["ingredients"] or h_ingredients
    instructions = ld["instructions"] or h_instructions

    text_content = "\n".join(_clean_lines(soup.get_text("\n")))

    if not ingredients and not instructions:
        raise ScrapeError("No recipe-like content found on this page.")

    return ScrapedRecipe(
        source_url=url,
        title=title,
        text=text_content[:20000],
        ingredients=[i for i in ingredients if i][:60],
        instructions=[s for s in instructions if s][:60],
        prep_time=ld["prep_time"],
        cook_time=ld["cook_time"],
        total_time=ld["total_time"],
        servings=ld["servings"],
        cuisine=ld["cuisine"],
    )