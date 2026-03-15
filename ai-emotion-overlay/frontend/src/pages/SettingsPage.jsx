// ============================================================
// SettingsPage — Configure overlay, model, and API settings
// ============================================================

import { useState } from "react";

export default function SettingsPage({ settings, onSave }) {
  const [form, setForm] = useState({ ...settings });
  const [saved, setSaved] = useState(false);

  const update = (key, value) => setForm((f) => ({ ...f, [key]: value }));

  const handleSave = () => {
    onSave(form);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const Toggle = ({ label, desc, field }) => (
    <div className="flex items-center justify-between py-3 border-b border-gray-800">
      <div>
        <div className="text-sm font-medium">{label}</div>
        {desc && <div className="text-xs text-gray-500 mt-0.5">{desc}</div>}
      </div>
      <button
        onClick={() => update(field, !form[field])}
        className={`relative w-10 h-5 rounded-full transition-colors
          ${form[field] ? "bg-purple-600" : "bg-gray-700"}`}
      >
        <div className={`absolute top-0.5 w-4 h-4 rounded-full bg-white transition-all
          ${form[field] ? "left-5" : "left-0.5"}`} />
      </button>
    </div>
  );

  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold mb-6 text-purple-300">⚙️ Settings</h1>

      <div className="space-y-6">
        {/* Overlay settings */}
        <div className="bg-gray-900 rounded-xl border border-gray-800 p-5">
          <h2 className="font-semibold mb-4 text-purple-400">Overlay Options</h2>
          <Toggle label="Show HUD Panel" desc="Display emotion progress bars on left side" field="showHUD" />
          <Toggle label="Show Bounding Box" desc="Draw box around detected faces" field="showBBox" />
          <Toggle label="Persona AR Overlays" desc="Show emotion-based filter on face" field="showPersona" />
        </div>

        {/* Model settings */}
        <div className="bg-gray-900 rounded-xl border border-gray-800 p-5">
          <h2 className="font-semibold mb-4 text-purple-400">AI Model</h2>

          <div className="mb-4">
            <label className="text-sm text-gray-400 mb-2 block">Emotion Detection Backend</label>
            <select
              value={form.modelType}
              onChange={(e) => update("modelType", e.target.value)}
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-purple-500"
            >
              <option value="fer">FER (Fast, recommended)</option>
              <option value="deepface">DeepFace (More accurate, slower)</option>
              <option value="custom">Custom CNN (requires training)</option>
            </select>
          </div>

          <div>
            <label className="text-sm text-gray-400 mb-2 block">
              Smoothing Window: {form.smoothingWindow} frames
            </label>
            <input
              type="range"
              min={1} max={15}
              value={form.smoothingWindow}
              onChange={(e) => update("smoothingWindow", parseInt(e.target.value))}
              className="w-full accent-purple-500"
            />
            <div className="flex justify-between text-xs text-gray-600 mt-1">
              <span>1 (jittery)</span>
              <span>15 (very smooth)</span>
            </div>
          </div>
        </div>

        {/* API settings */}
        <div className="bg-gray-900 rounded-xl border border-gray-800 p-5">
          <h2 className="font-semibold mb-4 text-purple-400">Backend API</h2>
          <div>
            <label className="text-sm text-gray-400 mb-2 block">API Base URL</label>
            <input
              type="text"
              value={form.apiUrl}
              onChange={(e) => update("apiUrl", e.target.value)}
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm font-mono focus:outline-none focus:border-purple-500"
              placeholder="http://localhost:8000"
            />
          </div>
        </div>

        {/* Save button */}
        <button
          onClick={handleSave}
          className={`w-full py-3 rounded-xl font-semibold transition-all
            ${saved ? "bg-green-700 text-green-200" : "bg-purple-600 hover:bg-purple-500"}`}
        >
          {saved ? "✓ Settings Saved!" : "Save Settings"}
        </button>
      </div>
    </div>
  );
}
