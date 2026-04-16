const API_BASE = (import.meta.env.VITE_API_BASE || "http://localhost:8000").replace(/\/$/, "");

async function safeFetch(url, options) {
  try {
    return await fetch(url, options);
  } catch {
    throw new Error("Cannot reach backend. Ensure FastAPI is running on http://localhost:8000.");
  }
}

export async function extractRecipe(url) {
  const response = await safeFetch(`${API_BASE}/extract`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Unknown error" }));
    throw new Error(error.detail || "Failed to extract recipe");
  }

  return response.json();
}

export async function fetchRecipes() {
  const response = await safeFetch(`${API_BASE}/recipes`);
  if (!response.ok) throw new Error("Failed to fetch recipes");
  return response.json();
}

export async function fetchRecipeById(id) {
  const response = await safeFetch(`${API_BASE}/recipes/${id}`);
  if (!response.ok) throw new Error("Failed to fetch recipe details");
  return response.json();
}

export async function buildMealPlan(recipeIds) {
  const response = await safeFetch(`${API_BASE}/meal-planner`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ recipe_ids: recipeIds }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Unknown error" }));
    throw new Error(error.detail || "Failed to create meal plan");
  }

  return response.json();
}