import { memo, useEffect, useMemo, useState } from "react";

import Button from "./ui/Button";
import Card from "./ui/Card";
import Input from "./ui/Input";

const placeholders = [
  "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  "https://youtu.be/jNQXAC9IVRw",
  "https://www.youtube.com/watch?v=aqz-KE-bpKQ",
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
    onSubmit(youtubeUrl.trim());
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
      <div className="inline-actions" style={{ justifyContent: "space-between", alignItems: "center" }}>
        <p className="muted">Détection auto des meilleurs moments en <strong>moins de 5 minutes</strong>.</p>
        <Button type="submit" variant="primary" loading={isLoading}>
          {isLoading ? "Traitement en cours" : "Générer mes clips"}
        </Button>
      </div>

      {previewUrl ? (
        <div className="ui-card" style={{ padding: 10 }}>
          <p className="caption" style={{ marginBottom: 8 }}>
            Aperçu miniature détectée
          </p>
          <img
            src={previewUrl}
            alt="Aperçu YouTube"
            loading="lazy"
            style={{ width: "100%", borderRadius: 12, border: "1px solid var(--border)" }}
          />
        </div>
      ) : null}
    </Card>
  );
}

export default memo(VideoInput);
