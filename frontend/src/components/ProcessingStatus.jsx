import { memo, useEffect, useMemo, useRef, useState } from "react";
import confetti from "canvas-confetti";

import Badge from "./ui/Badge";
import Card from "./ui/Card";
import Spinner from "./ui/Spinner";

const steps = [
  { key: "downloading", label: "Telechargement", icon: "⬇️", desc: "Recuperation de la video source" },
  { key: "extracting", label: "Extraction audio", icon: "🎵", desc: "Preparation audio 16kHz" },
  { key: "transcribing", label: "Transcription", icon: "📝", desc: "Whisper convertit en texte" },
  { key: "detecting", label: "Analyse IA", icon: "🧠", desc: "Gemini detecte les hooks" },
  { key: "cutting", label: "Decoupe", icon: "✂️", desc: "Extraction des meilleurs passages" },
  { key: "formatting", label: "Formatage", icon: "🎬", desc: "Conversion verticale 9:16" },
  { key: "done", label: "Pret", icon: "✅", desc: "Clips livres et telechargeables" },
];

const progressRank = {
  pending: 0,
  downloading: 1,
  extracting: 2,
  transcribing: 3,
  detecting: 4,
  cutting: 5,
  formatting: 6,
  uploading: 6,
  done: 7,
  error: 7,
};

function StepIndicator({ state }) {
  if (state === "done") {
    return <span style={{ fontSize: 16 }}>✅</span>;
  }
  if (state === "active") {
    return <Spinner size={16} />;
  }
  return <span style={{ width: 16, height: 16, borderRadius: "50%", border: "1px solid var(--border)" }} />;
}

function formatElapsed(seconds) {
  const s = Math.max(0, Math.round(seconds || 0));
  const min = Math.floor(s / 60);
  const rest = s % 60;
  if (min <= 0) {
    return `${rest}s`;
  }
  return `${min}m ${String(rest).padStart(2, "0")}s`;
}

function ProcessingStatus({ status, progress }) {
  const rank = progressRank[status] ?? 0;
  const isDone = status === "done";

  const startTimesRef = useRef({});
  const statusRef = useRef(status);
  const [nowTick, setNowTick] = useState(Date.now());

  useEffect(() => {
    if (!startTimesRef.current[status]) {
      startTimesRef.current[status] = Date.now();
    }

    if (statusRef.current !== status) {
      if (!startTimesRef.current[status]) {
        startTimesRef.current[status] = Date.now();
      }
      statusRef.current = status;
    }
  }, [status]);

  useEffect(() => {
    const timer = window.setInterval(() => setNowTick(Date.now()), 1000);
    return () => window.clearInterval(timer);
  }, []);

  useEffect(() => {
    if (!isDone) {
      return;
    }
    confetti({
      particleCount: 100,
      spread: 70,
      colors: ["#6366F1", "#8B5CF6", "#EC4899"],
      origin: { y: 0.6 },
    });
  }, [isDone]);

  const estimatedMinutes = useMemo(() => {
    if (!progress || progress >= 100) {
      return 0;
    }
    return Math.max(1, Math.round(((100 - progress) / 100) * 5));
  }, [progress]);

  const elapsedFor = (key) => {
    const startedAt = startTimesRef.current[key];
    if (!startedAt) {
      return "0s";
    }
    return formatElapsed((nowTick - startedAt) / 1000);
  };

  return (
    <Card>
      <div className="inline-actions" style={{ justifyContent: "space-between", alignItems: "center" }}>
        <h3>Traitement en cours</h3>
        {isDone ? <Badge variant="success">Termine</Badge> : <Badge variant="primary">{status || "pending"}</Badge>}
      </div>

      <div className="progress-track" style={{ marginTop: 10 }}>
        <div className="progress-bar" style={{ width: `${Math.max(0, Math.min(100, progress || 0))}%` }} />
      </div>
      <p className="muted" style={{ marginTop: 8 }}>
        {progress || 0}% • {isDone ? "Livraison finalisee" : `Temps restant estime: ~${estimatedMinutes} min`}
      </p>

      <div className="grid" style={{ marginTop: 16, gap: 10 }}>
        {steps.map((step, index) => {
          const state = index + 1 < rank ? "done" : index + 1 === rank ? "active" : "todo";
          const isActive = state === "active";
          return (
            <div
              key={step.key}
              style={{
                display: "flex",
                gap: 12,
                alignItems: "start",
                padding: "8px 10px",
                borderRadius: 10,
                background: isActive ? "rgba(99,102,241,0.10)" : "transparent",
                border: isActive ? "1px solid rgba(99,102,241,0.35)" : "1px solid transparent",
              }}
            >
              <div style={isActive ? { animation: "glowPulse 1.2s ease-in-out infinite" } : undefined}>
                <StepIndicator state={state} />
              </div>
              <div>
                <p style={{ fontWeight: 600 }}>
                  {step.icon} {step.label}
                </p>
                <p className="muted" style={{ fontSize: 14 }}>
                  {step.desc} • {elapsedFor(step.key)}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </Card>
  );
}

export default memo(ProcessingStatus);
