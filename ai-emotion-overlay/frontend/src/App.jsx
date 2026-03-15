// ============================================================
// AI Face Emotion Overlay — React Web Frontend
// Main App Component
// Stack: React + Tailwind CSS + Recharts
// ============================================================

import { useState, useRef, useEffect, useCallback } from "react";

// ── Page Components (inline for single-file simplicity) ──────────────────────
import HomePage from "./pages/HomePage";
import LivePage from "./pages/LivePage";
import SessionsPage from "./pages/SessionsPage";
import SettingsPage from "./pages/SettingsPage";

const NAV_ITEMS = [
  { id: "home", label: "🏠 Home" },
  { id: "live", label: "🎥 Live" },
  { id: "sessions", label: "📊 Sessions" },
  { id: "settings", label: "⚙️ Settings" },
];

export default function App() {
  const [page, setPage] = useState("home");
  const [settings, setSettings] = useState({
    showHUD: true,
    showBBox: true,
    showPersona: false,
    modelType: "fer",
    smoothingWindow: 5,
    apiUrl: "http://localhost:8000",
  });

  return (
    <div className="min-h-screen bg-gray-950 text-white flex flex-col">
      {/* ── Top Nav ───────────────────────────────────────────────── */}
      <nav className="bg-gray-900 border-b border-gray-800 px-6 py-3 flex items-center gap-8">
        <div className="flex items-center gap-2">
          <span className="text-2xl">🧠</span>
          <span className="font-bold text-purple-400 text-lg tracking-tight">
            AI Emotion Overlay
          </span>
        </div>
        <div className="flex gap-2 ml-auto">
          {NAV_ITEMS.map((item) => (
            <button
              key={item.id}
              onClick={() => setPage(item.id)}
              className={`px-4 py-1.5 rounded-md text-sm font-medium transition-all
                ${page === item.id
                  ? "bg-purple-600 text-white"
                  : "text-gray-400 hover:text-white hover:bg-gray-800"
                }`}
            >
              {item.label}
            </button>
          ))}
        </div>
      </nav>

      {/* ── Page Content ──────────────────────────────────────────── */}
      <main className="flex-1 p-6">
        {page === "home" && <HomePage onNavigate={setPage} />}
        {page === "live" && <LivePage settings={settings} />}
        {page === "sessions" && <SessionsPage settings={settings} />}
        {page === "settings" && (
          <SettingsPage settings={settings} onSave={setSettings} />
        )}
      </main>

      {/* ── Footer ────────────────────────────────────────────────── */}
      <footer className="text-center text-xs text-gray-600 py-3 border-t border-gray-900">
        AI Face Emotion Overlay v1.0.0 — Built with MediaPipe + FER + FastAPI
      </footer>
    </div>
  );
}
