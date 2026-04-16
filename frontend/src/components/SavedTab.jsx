import { useEffect, useMemo, useState } from "react";
import { buildMealPlan, fetchRecipeById, fetchRecipes } from "../api";
import RecipeModal from "./RecipeModal";

export default function SavedTab({ refreshKey }) {
  const [recipes, setRecipes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selected, setSelected] = useState(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [checkedIds, setCheckedIds] = useState([]);
  const [mealPlan, setMealPlan] = useState(null);

  async function loadRecipes() {
    setLoading(true);
    setError("");
    try {
      const data = await fetchRecipes();
      setRecipes(data);
    } catch (err) {
      setError(err.message || "Failed to load recipes");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadRecipes();
  }, [refreshKey]);

  async function openDetails(id) {
    try {
      const detail = await fetchRecipeById(id);
      setSelected(detail);
      setModalOpen(true);
    } catch (err) {
      setError(err.message || "Could not load details");
    }
  }

  function toggleRecipe(id) {
    setCheckedIds((prev) =>
      prev.includes(id) ? prev.filter((v) => v !== id) : [...prev, id]
    );
  }

  async function handleMealPlan() {
    setError("");
    setMealPlan(null);
    try {
      const response = await buildMealPlan(checkedIds);
      setMealPlan(response);
    } catch (err) {
      setError(err.message || "Could not build meal plan");
    }
  }

  const canCreatePlan = useMemo(
    () => checkedIds.length >= 3 && checkedIds.length <= 5,
    [checkedIds]
  );

  return (
    <div>
      <div className="meal-box">
        <h3>Meal Planner (Bonus)</h3>
        <p className="muted">Select 3 to 5 recipes from history and generate one combined shopping list.</p>
        <button className="btn" disabled={!canCreatePlan} onClick={handleMealPlan}>Generate Meal Plan</button>
        {!canCreatePlan ? <p className="muted">Pick between 3 and 5 recipes to continue.</p> : null}
      </div>

      {mealPlan ? (
        <div className="card">
          <h3>Combined Shopping List</h3>
          {Object.entries(mealPlan.combined_shopping_list || {}).map(([category, items]) => (
            <div className="category-block" key={category}>
              <h4>{category}</h4>
              <ul>
                {items.map((item) => (
                  <li key={`${category}-${item}`}>{item}</li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      ) : null}

      {error ? <p className="error">{error}</p> : null}
      {loading ? <p className="muted">Loading saved recipes...</p> : null}

      {!loading && recipes.length === 0 ? <p className="muted">No recipes saved yet.</p> : null}

      {!loading && recipes.length > 0 ? (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Select</th>
                <th>Title</th>
                <th>Cuisine</th>
                <th>Difficulty</th>
                <th>Date</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {recipes.map((recipe) => (
                <tr key={recipe.id}>
                  <td>
                    <input
                      type="checkbox"
                      checked={checkedIds.includes(recipe.id)}
                      onChange={() => toggleRecipe(recipe.id)}
                    />
                  </td>
                  <td>{recipe.title}</td>
                  <td>{recipe.cuisine || "Unknown"}</td>
                  <td>{recipe.difficulty || "Unknown"}</td>
                  <td>{new Date(recipe.created_at).toLocaleDateString()}</td>
                  <td>
                    <button className="btn ghost" onClick={() => openDetails(recipe.id)}>
                      Details
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}

      <RecipeModal open={modalOpen} onClose={() => setModalOpen(false)} recipe={selected} />
    </div>
  );
}
