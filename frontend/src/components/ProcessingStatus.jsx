import { memo, useMemo } from "react";

import Badge from "./ui/Badge";
import Card from "./ui/Card";
import Spinner from "./ui/Spinner";

const steps = [
  { key: "downloading", label: "Téléchargement", icon: "⬇️", desc: "Récupération de la vidéo source" },
  { key: "extracting", label: "Extraction audio", icon: "🎵", desc: "Préparation audio 16kHz" },
  { key: "transcribing", label: "Transcription", icon: "📝", desc: "Whisper convertit en texte" },
  { key: "detecting", label: "Analyse IA", icon: "🧠", desc: "Gemini détecte les hooks" },
  { key: "cutting", label: "Découpe", icon: "✂️", desc: "Extraction des meilleurs passages" },
  { key: "formatting", label: "Formatage", icon: "🎬", desc: "Conversion verticale 9:16" },
  { key: "done", label: "Prêt", icon: "✅", desc: "Clips livrés et téléchargeables" },
];

const progressRank = {
  pending: 0,
  downloading: 1,
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

function ProcessingStatus({ status, progress }) {
  const rank = progressRank[status] ?? 0;
  const isDone = status === "done";

  const estimatedMinutes = useMemo(() => {
    if (!progress || progress >= 100) {
      return 0;
    }
    return Math.max(1, Math.round(((100 - progress) / 100) * 5));
  }, [progress]);

  return (
    <Card>
      <div className="inline-actions" style={{ justifyContent: "space-between", alignItems: "center" }}>
        <h3>Traitement en cours</h3>
        {isDone ? <Badge variant="success">Terminé</Badge> : <Badge variant="primary">{status || "pending"}</Badge>}
      </div>

      <div className="progress-track" style={{ marginTop: 10 }}>
        <div className="progress-bar" style={{ width: `${Math.max(0, Math.min(100, progress || 0))}%` }} />
      </div>
      <p className="muted" style={{ marginTop: 8 }}>
        {progress || 0}% • {isDone ? "Livraison finalisée" : `Temps restant estimé: ~${estimatedMinutes} min`}
      </p>

      <div className="grid" style={{ marginTop: 16, gap: 10 }}>
        {steps.map((step, index) => {
          const state = index + 1 < rank ? "done" : index + 1 === rank ? "active" : "todo";
          return (
            <div key={step.key} style={{ display: "flex", gap: 12, alignItems: "start" }}>
              <StepIndicator state={state} />
              <div>
                <p style={{ fontWeight: 600 }}>{step.icon} {step.label}</p>
                <p className="muted" style={{ fontSize: 14 }}>{step.desc}</p>
              </div>
            </div>
          );
        })}
      </div>

      {isDone ? <p style={{ marginTop: 12, fontSize: 22 }}>🎉 🎊 🎉</p> : null}
    </Card>
  );
}

export default memo(ProcessingStatus);
