function SectionCard({ title, children, delayIndex = 0 }) {
  return (
    <div className="card reveal" style={{ animationDelay: `${delayIndex * 70}ms` }}>
      <h3>{title}</h3>
      {children}
    </div>
  );
}

function List({ items }) {
  if (!items || !items.length) return <p className="muted">No data</p>;
  return (
    <ul>
      {items.map((item, index) => (
        <li key={`${typeof item === "string" ? item : JSON.stringify(item)}-${index}`}>
          {typeof item === "string" ? item : JSON.stringify(item)}
        </li>
      ))}
    </ul>
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
          {ingredients.map((ing, idx) => {
            if (typeof ing === "string") {
              return (
                <tr key={`${ing}-${idx}`}>
                  <td>-</td>
                  <td>-</td>
                  <td>{ing}</td>
                </tr>
              );
            }
            return (
              <tr key={`${ing.item || "ingredient"}-${idx}`}>
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

export default function RecipeModal({ open, onClose, recipe }) {
  if (!open || !recipe) return null;
  const data = recipe.data || {};
  const nutrition = data.nutrition || data.nutrition_estimate || {};
  const shoppingList = data.shopping_list || {};

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>{recipe.title}</h2>
          <button className="btn ghost" onClick={onClose}>Close</button>
        </div>

        <div className="grid">
          <SectionCard title="Recipe Summary" delayIndex={0}>
            <p><strong>Cuisine:</strong> {data.cuisine || "Unknown"}</p>
            <p><strong>Prep:</strong> {data.prep_time || "Unknown"}</p>
            <p><strong>Cook:</strong> {data.cook_time || "Unknown"}</p>
            <p><strong>Total:</strong> {data.total_time || "Unknown"}</p>
            <p><strong>Servings:</strong> {data.servings || "Unknown"}</p>
            <p><strong>Difficulty:</strong> {data.difficulty || "Unknown"}</p>
          </SectionCard>

          <SectionCard title="Nutrition" delayIndex={1}>
            <p>Calories: {nutrition.calories || "Unknown"}</p>
            <p>Protein: {nutrition.protein || "Unknown"}</p>
            <p>Carbs: {nutrition.carbs || "Unknown"}</p>
            <p>Fat: {nutrition.fat || "Unknown"}</p>
          </SectionCard>

          <SectionCard title="Ingredients" delayIndex={2}>
            <IngredientList ingredients={data.ingredients} />
          </SectionCard>

          <SectionCard title="Instructions" delayIndex={3}>
            <ol>
              {(data.instructions || []).map((step, idx) => (
                <li key={`${step}-${idx}`}>{step}</li>
              ))}
            </ol>
          </SectionCard>

          <SectionCard title="Substitutions" delayIndex={4}>
            <List items={data.substitutions} />
          </SectionCard>

          <SectionCard title="Related Recipes" delayIndex={5}>
            <List items={data.related_recipes} />
          </SectionCard>
        </div>

        <SectionCard title="Shopping List" delayIndex={6}>
          {Object.keys(shoppingList).length === 0 ? (
            <p className="muted">No shopping list generated.</p>
          ) : (
            Object.entries(shoppingList).map(([category, items]) => (
              <div key={category} className="category-block">
                <h4>{category}</h4>
                <List items={items} />
              </div>
            ))
          )}
        </SectionCard>
      </div>
    </div>
  );
}