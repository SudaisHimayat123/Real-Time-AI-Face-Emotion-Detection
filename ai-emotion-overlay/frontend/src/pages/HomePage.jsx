// ============================================================
// HomePage — Landing page with two main options
// ============================================================

export default function HomePage({ onNavigate }) {
  const features = [
    { icon: "🎯", title: "7 Emotion Classes", desc: "Happy, Sad, Angry, Surprise, Neutral, Fear, Disgust" },
    { icon: "⚡", title: "Real-time 30+ FPS", desc: "Optimized pipeline with MediaPipe + FER" },
    { icon: "📊", title: "HUD Overlay", desc: "Live progress bars for all emotion scores" },
    { icon: "🎭", title: "Persona Filters", desc: "Emotion-based AR filter overlays on your face" },
    { icon: "📁", title: "CSV Export", desc: "Export full session emotion data for analysis" },
    { icon: "🎬", title: "Video Recording", desc: "Save output video with all overlays" },
  ];

  return (
    <div className="max-w-4xl mx-auto">
      {/* Hero */}
      <div className="text-center mb-12 mt-4">
        <div className="text-6xl mb-4">🧠</div>
        <h1 className="text-4xl font-bold mb-3 bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
          AI Face Emotion Overlay
        </h1>
        <p className="text-gray-400 text-lg max-w-xl mx-auto">
          Real-time facial emotion detection with HUD, bounding box, and optional
          AR persona overlays. Powered by MediaPipe + FER.
        </p>
      </div>

      {/* Main CTAs */}
      <div className="grid grid-cols-2 gap-6 mb-12">
        <button
          onClick={() => onNavigate("live")}
          className="group bg-gradient-to-br from-purple-700 to-purple-900 hover:from-purple-600 hover:to-purple-800
            rounded-2xl p-8 text-left transition-all border border-purple-700 hover:border-purple-500"
        >
          <div className="text-5xl mb-4">📹</div>
          <h2 className="text-2xl font-bold mb-2">Use Webcam</h2>
          <p className="text-purple-300 text-sm">
            Start real-time emotion detection from your device camera. Live HUD overlay included.
          </p>
          <div className="mt-4 text-xs text-purple-400 group-hover:text-purple-200 transition-colors">
            Click to start →
          </div>
        </button>

        <button
          onClick={() => onNavigate("sessions")}
          className="group bg-gradient-to-br from-gray-800 to-gray-900 hover:from-gray-700 hover:to-gray-800
            rounded-2xl p-8 text-left transition-all border border-gray-700 hover:border-gray-500"
        >
          <div className="text-5xl mb-4">📊</div>
          <h2 className="text-2xl font-bold mb-2">View Sessions</h2>
          <p className="text-gray-400 text-sm">
            Review past sessions, view emotion history graphs, and export CSV data.
          </p>
          <div className="mt-4 text-xs text-gray-500 group-hover:text-gray-300 transition-colors">
            View history →
          </div>
        </button>
      </div>

      {/* Features Grid */}
      <div>
        <h2 className="text-lg font-semibold text-gray-300 mb-4">Features</h2>
        <div className="grid grid-cols-3 gap-4">
          {features.map((f) => (
            <div
              key={f.title}
              className="bg-gray-900 rounded-xl p-4 border border-gray-800"
            >
              <div className="text-2xl mb-2">{f.icon}</div>
              <div className="font-semibold text-sm mb-1">{f.title}</div>
              <div className="text-gray-500 text-xs">{f.desc}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
