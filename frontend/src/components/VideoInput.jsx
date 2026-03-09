import { memo, useEffect, useMemo, useState } from "react";

import Button from "./ui/Button";
import Card from "./ui/Card";
import Input from "./ui/Input";

const placeholders = [
  "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  "https://youtu.be/jNQXAC9IVRw",
  "https://www.youtube.com/watch?v=aqz-KE-bpKQ",
];

const clipModes = [
  { id: "talking", label: "🎙 Talking" },
  { id: "visual", label: "📹 Visual" },
  { id: "energy", label: "⚡ Energy" },
  { id: "prompt", label: "🔍 Prompt" },
];

function extractVideoId(url) {
  if (!url) {
    return "";
  }
  const match = url.match(/(?:youtube\.com\/watch\?v=|youtu\.be\/)([\w-]{6,})/i);
  return match?.[1] || "";
}

function VideoInput({ isLoading, onSubmit }) {
  const [youtubeUrl, setYoutubeUrl] = useState("");
  const [placeholderIndex, setPlaceholderIndex] = useState(0);
  const [clipMode, setClipMode] = useState("talking");
  const [prompt, setPrompt] = useState("");
  const [maxClips, setMaxClips] = useState(8);
  const [minDuration, setMinDuration] = useState(30);
  const [maxDuration, setMaxDuration] = useState(90);
  const [targetPlatform, setTargetPlatform] = useState("all");
  const [layout, setLayout] = useState("centered");

  useEffect(() => {
    const timer = window.setInterval(() => {
      setPlaceholderIndex((index) => (index + 1) % placeholders.length);
    }, 2200);
    return () => clearInterval(timer);
  }, []);

  const videoId = useMemo(() => extractVideoId(youtubeUrl.trim()), [youtubeUrl]);
  const previewUrl = videoId ? `https://i.ytimg.com/vi/${videoId}/hqdefault.jpg` : "";

  const handleSubmit = (event) => {
    event.preventDefault();
    if (!youtubeUrl.trim()) {
      return;
    }
    const payload = {
      youtube_url: youtubeUrl.trim(),
      clip_mode: clipMode,
      prompt: clipMode === "prompt" ? prompt.trim() || null : null,
      max_clips: Number(maxClips),
      min_duration: Number(minDuration),
      max_duration: Number(maxDuration),
      target_platform: targetPlatform,
      layout,
    };
    onSubmit(payload);
  };

  return (
    <Card as="form" className="form-col" onSubmit={handleSubmit}>
      <h3>Colle ton lien YouTube</h3>
      <Input
        id="youtube-url"
        label="URL YouTube"
        type="url"
        placeholder={placeholders[placeholderIndex]}
        value={youtubeUrl}
        onChange={(event) => setYoutubeUrl(event.target.value)}
        required
      />

      <div className="inline-actions" style={{ flexWrap: "wrap", gap: 8 }}>
        {clipModes.map((mode) => (
          <button
            key={mode.id}
            type="button"
            className={`ui-btn ${clipMode === mode.id ? "ui-btn-primary" : "ui-btn-secondary"}`}
            onClick={() => setClipMode(mode.id)}
          >
            {mode.label}
          </button>
        ))}
      </div>

      {clipMode === "prompt" ? (
        <Input
          id="clip-prompt"
          label="Recherche IA"
          type="text"
          placeholder="Ex: Trouve les moments les plus droles"
          value={prompt}
          onChange={(event) => setPrompt(event.target.value)}
          required
        />
      ) : null}

      <details className="ui-card" style={{ padding: 12 }}>
        <summary style={{ cursor: "pointer", fontWeight: 600 }}>Options avancees</summary>
        <div className="grid grid-2" style={{ marginTop: 12, gap: 12 }}>
          <Input
            id="max-clips"
            label="Nombre de clips"
            type="number"
            min={1}
            max={12}
            value={maxClips}
            onChange={(event) => setMaxClips(event.target.value)}
          />
          <label htmlFor="target-platform" style={{ display: "grid", gap: 8 }}>
            <span className="muted">Plateforme cible</span>
            <select
              id="target-platform"
              className="ui-input"
              value={targetPlatform}
              onChange={(event) => setTargetPlatform(event.target.value)}
            >
              <option value="all">Toutes</option>
              <option value="tiktok">TikTok</option>
              <option value="reels">Instagram Reels</option>
              <option value="shorts">YouTube Shorts</option>
            </select>
          </label>
          <Input
            id="min-duration"
            label="Duree min (sec)"
            type="number"
            min={10}
            max={180}
            value={minDuration}
            onChange={(event) => setMinDuration(event.target.value)}
          />
          <Input
            id="max-duration"
            label="Duree max (sec)"
            type="number"
            min={15}
            max={240}
            value={maxDuration}
            onChange={(event) => setMaxDuration(event.target.value)}
          />
          <label htmlFor="layout" style={{ display: "grid", gap: 8 }}>
            <span className="muted">Layout video</span>
            <select id="layout" className="ui-input" value={layout} onChange={(event) => setLayout(event.target.value)}>
              <option value="centered">Centered tracking</option>
              <option value="blurred">Blurred background</option>
              <option value="split">Split screen</option>
            </select>
          </label>
        </div>
      </details>

      <div className="inline-actions" style={{ justifyContent: "space-between", alignItems: "center" }}>
        <p className="muted">
          Mode actif: <strong>{clipModes.find((mode) => mode.id === clipMode)?.label}</strong>
        </p>
        <Button type="submit" variant="primary" loading={isLoading}>
          {isLoading ? "Traitement en cours" : "Generer mes clips"}
        </Button>
      </div>

      {previewUrl ? (
        <div className="ui-card" style={{ padding: 10 }}>
          <p className="caption" style={{ marginBottom: 8 }}>Apercu miniature detectee</p>
          <img
            src={previewUrl}
            alt="Apercu YouTube"
            loading="lazy"
            style={{ width: "100%", borderRadius: 12, border: "1px solid var(--border)" }}
          />
        </div>
      ) : null}
    </Card>
  );
}

export default memo(VideoInput);
