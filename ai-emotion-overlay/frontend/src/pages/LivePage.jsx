// ============================================================
// LivePage — Real-time webcam emotion detection
// Streams frames to backend via WebSocket, renders processed output
// ============================================================

import { useState, useRef, useEffect, useCallback } from "react";

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

export default function LivePage({ settings }) {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const wsRef = useRef(null);
  const intervalRef = useRef(null);
  const streamRef = useRef(null);

  const [isRunning, setIsRunning] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [faceData, setFaceData] = useState([]);
  const [fps, setFps] = useState(0);
  const [faceCount, setFaceCount] = useState(0);
  const [processedImg, setProcessedImg] = useState(null);
  const [error, setError] = useState("");
  const [isRecording, setIsRecording] = useState(false);

  // ── Start webcam ──────────────────────────────────────────────────────
  const startCamera = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: 1280, height: 720, frameRate: 30 }
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
      setError("");
    } catch (err) {
      setError(`Camera access denied: ${err.message}`);
    }
  }, []);

  // ── Connect WebSocket ─────────────────────────────────────────────────
  const connectWS = useCallback(() => {
    const wsUrl = (settings.apiUrl || "http://localhost:8000")
      .replace("http", "ws") + "/ws/stream";

    wsRef.current = new WebSocket(wsUrl);

    wsRef.current.onopen = () => {
      setIsConnected(true);
      setError("");
    };

    wsRef.current.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setProcessedImg(data.image);
      setFps(data.fps);
      setFaceCount(data.face_count);
      setFaceData(data.faces || []);
    };

    wsRef.current.onerror = () => {
      setError("WebSocket connection failed. Is the backend running?");
      setIsConnected(false);
    };

    wsRef.current.onclose = () => {
      setIsConnected(false);
    };
  }, [settings.apiUrl]);

  // ── Capture and send frames ───────────────────────────────────────────
  const startStreaming = useCallback(() => {
    const canvas = canvasRef.current;
    const video = videoRef.current;

    intervalRef.current = setInterval(() => {
      if (!canvas || !video || !wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;
      const ctx = canvas.getContext("2d");
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      ctx.drawImage(video, 0, 0);
      const dataUrl = canvas.toDataURL("image/jpeg", 0.7);
      wsRef.current.send(dataUrl);
    }, 1000 / 20); // 20 FPS capture rate
  }, []);

  // ── Start session ─────────────────────────────────────────────────────
  const handleStart = useCallback(async () => {
    await startCamera();
    connectWS();

    // Small delay for WS to connect
    setTimeout(() => {
      startStreaming();
      setIsRunning(true);
    }, 800);
  }, [startCamera, connectWS, startStreaming]);

  // ── Stop session ──────────────────────────────────────────────────────
  const handleStop = useCallback(() => {
    clearInterval(intervalRef.current);
    if (wsRef.current) wsRef.current.close();
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop());
    }
    setIsRunning(false);
    setIsConnected(false);
    setProcessedImg(null);
  }, []);

  useEffect(() => {
    return () => handleStop();
  }, [handleStop]);

  // ── Dominant emotion for first face ──────────────────────────────────
  const dominantFace = faceData[0] || null;
  const dominantEmotion = dominantFace?.dominant || null;

  return (
    <div className="max-w-6xl mx-auto">
      <h1 className="text-2xl font-bold mb-6 text-purple-300">🎥 Live Emotion Detection</h1>

      {error && (
        <div className="bg-red-900/50 border border-red-700 text-red-300 rounded-lg p-3 mb-4 text-sm">
          ⚠️ {error}
        </div>
      )}

      <div className="grid grid-cols-3 gap-6">
        {/* ── Video Feed ──────────────────────────────────────────── */}
        <div className="col-span-2">
          <div className="bg-gray-900 rounded-2xl border border-gray-800 overflow-hidden relative">
            {/* Processed output from backend */}
            {processedImg ? (
              <img
                src={processedImg}
                alt="Processed feed"
                className="w-full rounded-2xl"
              />
            ) : (
              <div className="aspect-video flex items-center justify-center bg-gray-950">
                <video
                  ref={videoRef}
                  autoPlay
                  muted
                  playsInline
                  className="w-full rounded-2xl"
                  style={{ display: isRunning ? "block" : "none" }}
                />
                {!isRunning && (
                  <div className="text-center text-gray-600">
                    <div className="text-5xl mb-3">📷</div>
                    <p>Click Start to begin</p>
                  </div>
                )}
              </div>
            )}

            {/* Status badges */}
            <div className="absolute top-3 right-3 flex gap-2">
              <span className={`text-xs px-2 py-1 rounded-full font-mono
                ${isConnected ? "bg-green-900/80 text-green-400" : "bg-gray-800/80 text-gray-500"}`}>
                {isConnected ? "● LIVE" : "○ OFFLINE"}
              </span>
              <span className="text-xs px-2 py-1 rounded-full font-mono bg-gray-800/80 text-gray-400">
                {fps.toFixed(1)} FPS
              </span>
              <span className="text-xs px-2 py-1 rounded-full font-mono bg-gray-800/80 text-gray-400">
                👤 {faceCount}
              </span>
            </div>
          </div>

          {/* Controls */}
          <div className="flex gap-3 mt-4">
            {!isRunning ? (
              <button
                onClick={handleStart}
                className="flex-1 bg-purple-600 hover:bg-purple-500 px-6 py-2.5 rounded-lg font-semibold transition-all"
              >
                ▶ Start Detection
              </button>
            ) : (
              <button
                onClick={handleStop}
                className="flex-1 bg-red-700 hover:bg-red-600 px-6 py-2.5 rounded-lg font-semibold transition-all"
              >
                ■ Stop
              </button>
            )}
            <button
              className="px-4 py-2.5 bg-gray-800 hover:bg-gray-700 rounded-lg text-sm transition-all"
              onClick={() => {
                // Toggle recording via API
                const url = (settings.apiUrl || "http://localhost:8000");
                fetch(`${url}/api/start-session`, { method: "POST" });
              }}
            >
              🎙 New Session
            </button>
          </div>

          {/* Hidden canvas for frame capture */}
          <canvas ref={canvasRef} style={{ display: "none" }} />
        </div>

        {/* ── HUD Panel ───────────────────────────────────────────── */}
        <div className="space-y-4">
          {/* Dominant emotion card */}
          {dominantEmotion && (
            <div className="bg-gray-900 rounded-xl border border-gray-800 p-4">
              <div className="text-xs text-gray-500 mb-1">DOMINANT EMOTION</div>
              <div
                className="text-3xl font-bold capitalize"
                style={{ color: EMOTION_COLORS[dominantEmotion] || "#fff" }}
              >
                {dominantEmotion}
              </div>
              <div className="text-gray-400 text-sm mt-1">
                {((dominantFace?.confidence || 0) * 100).toFixed(0)}% confidence
              </div>
            </div>
          )}

          {/* Emotion scores */}
          <div className="bg-gray-900 rounded-xl border border-gray-800 p-4">
            <div className="text-xs text-gray-500 mb-3 font-semibold tracking-widest">
              FACE EMOTION HUD
            </div>
            {EMOTIONS.map((emotion) => {
              const score = dominantFace?.scores?.[emotion] ?? 0;
              const pct = (score * 100).toFixed(0);
              const color = EMOTION_COLORS[emotion] || "#888";
              return (
                <div key={emotion} className="mb-2.5">
                  <div className="flex justify-between text-xs mb-1">
                    <span className="capitalize text-gray-300">{emotion}</span>
                    <span style={{ color }}>{pct}%</span>
                  </div>
                  <div className="h-2 bg-gray-800 rounded-full overflow-hidden">
                    <div
                      className="h-full rounded-full transition-all duration-200"
                      style={{
                        width: `${pct}%`,
                        backgroundColor: color,
                        boxShadow: score > 0.5 ? `0 0 6px ${color}` : "none",
                      }}
                    />
                  </div>
                </div>
              );
            })}
          </div>

          {/* Multiple faces */}
          {faceData.length > 1 && (
            <div className="bg-gray-900 rounded-xl border border-gray-800 p-4">
              <div className="text-xs text-gray-500 mb-2">ALL FACES</div>
              {faceData.map((face, i) => (
                <div key={i} className="text-sm flex justify-between py-1 border-b border-gray-800 last:border-0">
                  <span className="text-gray-400">Face {i + 1}</span>
                  <span
                    className="capitalize font-medium"
                    style={{ color: EMOTION_COLORS[face.dominant] }}
                  >
                    {face.dominant} ({(face.confidence * 100).toFixed(0)}%)
                  </span>
                </div>
              ))}
            </div>
          )}

          {/* Tips */}
          <div className="bg-gray-900/50 rounded-xl border border-gray-800 p-3 text-xs text-gray-600">
            <div className="font-semibold text-gray-500 mb-1">💡 Tips</div>
            <ul className="space-y-1">
              <li>• Good lighting improves accuracy</li>
              <li>• Face the camera directly</li>
              <li>• Keep face fully in frame</li>
              <li>• Works with multiple faces</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
