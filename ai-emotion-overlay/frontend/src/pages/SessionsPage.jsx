// ============================================================
// SessionsPage — View session history, charts, CSV downloads
// ============================================================

import { useState, useEffect } from "react";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer
} from "recharts";

const EMOTION_COLORS = {
  happy:    "#00ff88",
  sad:      "#5599ff",
  angry:    "#ff4444",
  surprise: "#ffee44",
  neutral:  "#aaaaaa",
  fear:     "#cc44ff",
  disgust:  "#44ffbb",
};

const EMOTIONS = ["angry", "disgust", "fear", "happy", "neutral", "sad", "surprise"];

export default function SessionsPage({ settings }) {
  const API = settings.apiUrl || "http://localhost:8000";

  const [sessions, setSessions] = useState([]);
  const [selectedSession, setSelectedSession] = useState(null);
  const [timeline, setTimeline] = useState([]);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    fetchSessions();
  }, []);

  const fetchSessions = async () => {
    try {
      const res = await fetch(`${API}/api/sessions`);
      const data = await res.json();
      setSessions(data.sessions || []);
    } catch {
      setError("Could not connect to backend API.");
    }
  };

  const loadSession = async (sid) => {
    setLoading(true);
    setSelectedSession(sid);
    try {
      const [timelineRes, summaryRes] = await Promise.all([
        fetch(`${API}/api/session/${sid}/timeline?downsample=3`),
        fetch(`${API}/api/session/${sid}/summary`),
      ]);
      const timelineData = await timelineRes.json();
      const summaryData = await summaryRes.json();

      // Convert timeline to recharts format
      const tl = timelineData.timeline || {};
      const points = (tl.time || []).map((t, i) => {
        const point = { time: t.toFixed(1) };
        EMOTIONS.forEach((e) => { point[e] = (tl[e]?.[i] ?? 0) * 100; });
        return point;
      });
      setTimeline(points);
      setSummary(summaryData.summary || null);
    } catch {
      setError("Failed to load session data.");
    }
    setLoading(false);
  };

  const downloadCSV = async (sid) => {
    window.open(`${API}/api/export-csv?session_id=${sid}`, "_blank");
  };

  const formatTime = (str) => str ? str.replace("T", " ").slice(0, 19) : "—";
  const duration = (s, e) => {
    if (!s || !e) return "—";
    const diff = (new Date(e) - new Date(s)) / 1000;
    return `${Math.floor(diff / 60)}m ${(diff % 60).toFixed(0)}s`;
  };

  return (
    <div className="max-w-6xl mx-auto">
      <h1 className="text-2xl font-bold mb-6 text-purple-300">📊 Session History</h1>

      {error && (
        <div className="bg-red-900/40 border border-red-800 text-red-300 rounded-lg p-3 mb-4 text-sm">
          {error}
        </div>
      )}

      <div className="grid grid-cols-3 gap-6">
        {/* ── Sessions list ────────────────────────────────────────── */}
        <div>
          <div className="bg-gray-900 rounded-xl border border-gray-800">
            <div className="p-4 border-b border-gray-800 flex items-center justify-between">
              <span className="font-semibold text-sm">Sessions</span>
              <button
                onClick={fetchSessions}
                className="text-xs text-gray-500 hover:text-gray-300"
              >
                ↻ Refresh
              </button>
            </div>
            <div className="divide-y divide-gray-800 max-h-[500px] overflow-y-auto">
              {sessions.length === 0 ? (
                <div className="p-6 text-center text-gray-600 text-sm">
                  No sessions recorded yet. <br />Run the app to capture sessions.
                </div>
              ) : (
                sessions.map((s) => (
                  <div
                    key={s.id}
                    onClick={() => loadSession(s.id)}
                    className={`p-3 cursor-pointer hover:bg-gray-800 transition-colors
                      ${selectedSession === s.id ? "bg-purple-900/30 border-l-2 border-purple-500" : ""}`}
                  >
                    <div className="flex justify-between items-center">
                      <span className="text-sm font-medium">Session #{s.id}</span>
                      <span className="text-xs text-gray-500 capitalize">{s.source}</span>
                    </div>
                    <div className="text-xs text-gray-500 mt-0.5">{formatTime(s.start_time)}</div>
                    <div className="text-xs text-gray-600 mt-0.5">
                      {s.total_frames} frames · {duration(s.start_time, s.end_time)}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        {/* ── Session detail ────────────────────────────────────────── */}
        <div className="col-span-2 space-y-4">
          {!selectedSession ? (
            <div className="bg-gray-900 rounded-xl border border-gray-800 p-12 text-center text-gray-600">
              <div className="text-4xl mb-3">📈</div>
              Select a session to view its emotion timeline
            </div>
          ) : loading ? (
            <div className="bg-gray-900 rounded-xl border border-gray-800 p-12 text-center text-gray-500">
              Loading session data...
            </div>
          ) : (
            <>
              {/* Summary row */}
              {summary && (
                <div className="grid grid-cols-4 gap-3">
                  {["happy", "sad", "angry", "neutral"].map((e) => (
                    <div key={e} className="bg-gray-900 rounded-lg border border-gray-800 p-3 text-center">
                      <div className="text-xs text-gray-500 mb-1 capitalize">{e}</div>
                      <div
                        className="text-xl font-bold"
                        style={{ color: EMOTION_COLORS[e] }}
                      >
                        {((summary[`avg_${e}`] ?? 0) * 100).toFixed(0)}%
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Timeline chart */}
              <div className="bg-gray-900 rounded-xl border border-gray-800 p-4">
                <div className="flex justify-between items-center mb-4">
                  <h3 className="font-semibold text-sm text-gray-300">Emotion Timeline</h3>
                  <button
                    onClick={() => downloadCSV(selectedSession)}
                    className="text-xs bg-gray-800 hover:bg-gray-700 px-3 py-1.5 rounded-lg transition-all"
                  >
                    ⬇ Export CSV
                  </button>
                </div>

                {timeline.length > 0 ? (
                  <ResponsiveContainer width="100%" height={280}>
                    <LineChart data={timeline}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#222" />
                      <XAxis
                        dataKey="time"
                        tick={{ fill: "#666", fontSize: 10 }}
                        label={{ value: "Time (s)", position: "insideBottom", fill: "#555", fontSize: 11 }}
                      />
                      <YAxis
                        tick={{ fill: "#666", fontSize: 10 }}
                        domain={[0, 100]}
                        tickFormatter={(v) => `${v}%`}
                      />
                      <Tooltip
                        contentStyle={{ background: "#1a1a1a", border: "1px solid #333", borderRadius: 8 }}
                        labelStyle={{ color: "#aaa" }}
                        formatter={(v, name) => [`${v.toFixed(1)}%`, name]}
                      />
                      <Legend
                        wrapperStyle={{ fontSize: 11, color: "#888" }}
                      />
                      {EMOTIONS.map((e) => (
                        <Line
                          key={e}
                          type="monotone"
                          dataKey={e}
                          stroke={EMOTION_COLORS[e]}
                          strokeWidth={1.5}
                          dot={false}
                          activeDot={{ r: 3 }}
                        />
                      ))}
                    </LineChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="text-center text-gray-600 py-12 text-sm">
                    No timeline data available for this session
                  </div>
                )}
              </div>

              {/* Download buttons */}
              <div className="flex gap-3">
                <button
                  onClick={() => downloadCSV(selectedSession)}
                  className="flex-1 bg-gray-800 hover:bg-gray-700 px-4 py-2.5 rounded-lg text-sm font-medium transition-all"
                >
                  📄 Download CSV
                </button>
                <button
                  onClick={() => window.open(`${API}/api/recordings`, "_blank")}
                  className="flex-1 bg-gray-800 hover:bg-gray-700 px-4 py-2.5 rounded-lg text-sm font-medium transition-all"
                >
                  🎬 View Recordings
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
