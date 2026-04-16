import { useState } from "react";
import { extractRecipe } from "../api";

function List({ items, ordered = false }) {
  if (!items || !items.length) return <p className="muted">No data</p>;
  const Component = ordered ? "ol" : "ul";
  return (
    <Component>
      {items.map((item, index) => (
        <li key={`${typeof item === "string" ? item : JSON.stringify(item)}-${index}`}>
          {typeof item === "string" ? item : JSON.stringify(item)}
        </li>
      ))}
    </Component>
  );
}

function IngredientList({ ingredients }) {
  if (!ingredients || !ingredients.length) return <p className="muted">No data</p>;

  return (
    <div className="ingredient-table-wrap">
      <table className="ingredient-table">
        <thead>
          <tr>
            <th>Qty</th>
            <th>Unit</th>
            <th>Item</th>
          </tr>
        </thead>
        <tbody>
          {ingredients.map((ing, index) => {
            if (typeof ing === "string") {
              return (
                <tr key={`${ing}-${index}`}>
                  <td>-</td>
                  <td>-</td>
                  <td>{ing}</td>
                </tr>
              );
            }
            return (
              <tr key={`${ing.item || "ingredient"}-${index}`}>
                <td>{ing.quantity || "-"}</td>
                <td>{ing.unit || "-"}</td>
                <td>{ing.item || "-"}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function Card({ title, children, delayIndex = 0 }) {
  return (
    <section className="card reveal" style={{ animationDelay: `${delayIndex * 70}ms` }}>
      <h3>{title}</h3>
      {children}
    </section>
  );
}

export default function ExtractTab({ onRecipeSaved }) {
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);

  async function handleExtract(e) {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const response = await extractRecipe(url);
      setResult(response.data);
      onRecipeSaved();
    } catch (err) {
      setError(err.message || "Could not extract recipe");
    } finally {
      setLoading(false);
    }
  }

  const nutrition = result?.nutrition || result?.nutrition_estimate || {};
  const shoppingList = result?.shopping_list || {};

  return (
    <div>
      <form className="extract-form" onSubmit={handleExtract}>
        <input
          type="url"
          required
          placeholder="Paste recipe blog URL"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
        />
        <button className="btn" type="submit" disabled={loading}>
          {loading ? "Extracting..." : "Extract Recipe"}
        </button>
      </form>

      {error ? <p className="error">{error}</p> : null}

      {result ? (
        <div className="grid">
          <Card title="Recipe Summary" delayIndex={0}>
            <p><strong>Title:</strong> {result.title || "Unknown"}</p>
            <p><strong>Cuisine:</strong> {result.cuisine || "Unknown"}</p>
            <p><strong>Prep:</strong> {result.prep_time || "Unknown"}</p>
            <p><strong>Cook:</strong> {result.cook_time || "Unknown"}</p>
            <p><strong>Total:</strong> {result.total_time || "Unknown"}</p>
            <p><strong>Servings:</strong> {result.servings || "Unknown"}</p>
            <p><strong>Difficulty:</strong> {result.difficulty || "Unknown"}</p>
          </Card>

          <Card title="Ingredients" delayIndex={1}>
            <IngredientList ingredients={result.ingredients} />
          </Card>

          <Card title="Instructions" delayIndex={2}>
            <List items={result.instructions} ordered />
          </Card>

          <Card title="Nutrition" delayIndex={3}>
            <p>Calories: {nutrition.calories || "Unknown"}</p>
            <p>Protein: {nutrition.protein || "Unknown"}</p>
            <p>Carbs: {nutrition.carbs || "Unknown"}</p>
            <p>Fat: {nutrition.fat || "Unknown"}</p>
          </Card>

          <Card title="Substitutions" delayIndex={4}>
            <List items={result.substitutions} />
          </Card>

          <Card title="Related Recipes" delayIndex={5}>
            <List items={result.related_recipes} />
          </Card>

          <Card title="Shopping List" delayIndex={6}>
            {Object.keys(shoppingList).length ? (
              Object.entries(shoppingList).map(([category, items]) => (
                <div className="category-block" key={category}>
                  <h4>{category}</h4>
                  <List items={items} />
                </div>
              ))
            ) : (
              <p className="muted">No shopping list generated.</p>
            )}
          </Card>
        </div>
      ) : null}
    </div>
  );
}