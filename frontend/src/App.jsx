import { useState } from "react";
import ExtractTab from "./components/ExtractTab";
import SavedTab from "./components/SavedTab";

const TABS = {
  extract: "Extract Recipe",
  saved: "Saved Recipes",
};

export default function App() {
  const [activeTab, setActiveTab] = useState("extract");
  const [refreshKey, setRefreshKey] = useState(0);

  return (
    <div className="app-shell">
      <header>
        <h1>Recipe Extractor & Meal Planner</h1>
        <p>Paste any recipe blog URL, extract structured data, and save it to your recipe history.</p>
      </header>

      <div className="tabs">
        {Object.entries(TABS).map(([key, label]) => (
          <button
            key={key}
            className={`tab ${activeTab === key ? "active" : ""}`}
            onClick={() => setActiveTab(key)}
          >
            {label}
          </button>
        ))}
      </div>

      <main>
        {activeTab === "extract" ? (
          <ExtractTab onRecipeSaved={() => setRefreshKey((k) => k + 1)} />
        ) : (
          <SavedTab refreshKey={refreshKey} />
        )}
      </main>
    </div>
  );
}
