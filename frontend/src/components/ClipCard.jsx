import { memo, useMemo, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Link } from "react-router-dom";
import toast from "react-hot-toast";

import Badge from "./ui/Badge";
import Button from "./ui/Button";
import Card from "./ui/Card";

function formatDuration(durationSeconds) {
  const total = Math.max(0, Math.round(durationSeconds || 0));
  const minutes = Math.floor(total / 60);
  const seconds = total % 60;
  return `${minutes}:${String(seconds).padStart(2, "0")}`;
}

function scoreClass(score) {
  if (score >= 81) {
    return { className: "score-badge score-viral", label: `🔥 ${score}` };
  }
  if (score >= 61) {
    return { className: "score-badge score-good", label: `✅ ${score}` };
  }
  if (score >= 41) {
    return { className: "score-badge score-ok", label: `⚡ ${score}` };
  }
  return { className: "score-badge score-low", label: `⚠️ ${score}` };
}

function ClipCard({ clip, index = 0 }) {
  const [isPreviewOpen, setIsPreviewOpen] = useState(false);
  const [isHovering, setIsHovering] = useState(false);
  const [downloadProgress, setDownloadProgress] = useState(0);
  const [layout, setLayout] = useState("9:16");

  const durationLabel = useMemo(() => formatDuration(clip.duration_seconds), [clip.duration_seconds]);
  const score = Number(clip.virality_score || 0);

  const handleDownload = () => {
    if (!clip.file_url) {
      toast.error("Aucun fichier disponible");
      return;
    }
    setDownloadProgress(0);

    const xhr = new XMLHttpRequest();
    xhr.open("GET", clip.file_url, true);
    xhr.responseType = "blob";

    xhr.onprogress = (event) => {
      if (!event.lengthComputable) {
        return;
      }
      const progress = Math.round((event.loaded / event.total) * 100);
      setDownloadProgress(progress);
    };

    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 400) {
        const blobUrl = URL.createObjectURL(xhr.response);
        const anchor = document.createElement("a");
        const safeTitle = String(clip.title || "clip").replace(/[^a-zA-Z0-9_-]+/g, "_");
        anchor.href = blobUrl;
        anchor.download = `${safeTitle}.mp4`;
        document.body.appendChild(anchor);
        anchor.click();
        anchor.remove();
        URL.revokeObjectURL(blobUrl);
        setDownloadProgress(100);
        window.setTimeout(() => setDownloadProgress(0), 500);
        toast.success("Telechargement termine");
        return;
      }
      setDownloadProgress(0);
      toast.error("Echec du telechargement");
    };

    xhr.onerror = () => {
      setDownloadProgress(0);
      toast.error("Erreur reseau pendant le telechargement");
    };

    xhr.send();
  };

  const handleShare = async () => {
    const publicLink = clip.file_url || `${window.location.origin}/video/${clip.video_id}`;
    try {
      await navigator.clipboard.writeText(publicLink);
      toast.success("Lien copie !");
    } catch {
      toast.error("Impossible de copier le lien");
    }
  };

  return (
    <Card>
      <div
        className="clip-thumb"
        style={{ position: "relative" }}
        onMouseEnter={() => setIsHovering(true)}
        onMouseLeave={() => setIsHovering(false)}
      >
        {isHovering && clip.file_url ? (
          <video
            src={clip.file_url}
            muted
            loop
            autoPlay
            playsInline
            style={{
              width: "100%",
              borderRadius: 14,
              objectFit: "cover",
              aspectRatio: layout === "9:16" ? "9 / 16" : layout === "1:1" ? "1 / 1" : "16 / 9",
            }}
          />
        ) : (
          <img
            src={clip.thumbnail_url || "https://placehold.co/800x450/12122a/F8FAFC?text=Clip+Preview"}
            alt={clip.title}
            loading="lazy"
            style={{
              width: "100%",
              borderRadius: 14,
              aspectRatio: layout === "9:16" ? "9 / 16" : layout === "1:1" ? "1 / 1" : "16 / 9",
              objectFit: "cover",
            }}
          />
        )}
        {clip.virality_score ? (
          <span style={{ position: "absolute", top: 10, right: 10 }} className={scoreClass(score).className}>
            {scoreClass(score).label}
          </span>
        ) : null}
        <span
          style={{
            position: "absolute",
            bottom: 10,
            right: 10,
            borderRadius: 8,
            background: "rgba(8,8,18,0.75)",
            padding: "4px 8px",
            fontSize: 12,
          }}
        >
          {durationLabel}
        </span>
        <div className="clip-overlay">
          <Button variant="secondary" onClick={() => setIsPreviewOpen((value) => !value)}>
            {isPreviewOpen ? "Fermer" : "Play"}
          </Button>
        </div>
      </div>

      <div style={{ marginTop: 10, display: "grid", gap: 8 }}>
        <div className="inline-actions" style={{ justifyContent: "space-between", alignItems: "center" }}>
          <h4
            style={{
              overflow: "hidden",
              textOverflow: "ellipsis",
              whiteSpace: "nowrap",
              maxWidth: "85%",
            }}
          >
            {clip.title}
          </h4>
          {index === 0 ? <Badge variant="success">Top Pick</Badge> : null}
        </div>

        {clip.hook_text ? (
          <p style={{ fontSize: 13, color: "var(--accent)", fontStyle: "italic" }}>
            🎣 "{clip.hook_text}"
          </p>
        ) : null}

        <p className="muted" style={{ fontSize: 14 }}>
          {clip.start_time}s - {clip.end_time}s
        </p>

        <div className="inline-actions">
          {["9:16", "16:9", "1:1"].map((item) => (
            <button
              key={item}
              type="button"
              className={`ui-btn ${layout === item ? "ui-btn-primary" : "ui-btn-secondary"}`}
              onClick={() => setLayout(item)}
              style={{ padding: "8px 10px", fontSize: 13 }}
            >
              {item === "9:16" ? "📱 9:16" : item === "16:9" ? "💻 16:9" : "⬛ 1:1"}
            </button>
          ))}
        </div>

        <div className="inline-actions">
          <Button variant="secondary" onClick={() => setIsPreviewOpen((value) => !value)}>
            {isPreviewOpen ? "Masquer" : "Preview"}
          </Button>
          <Link to={`/clip-editor/${clip.id}`}>
            <Button variant="secondary">Editer</Button>
          </Link>
          <Button variant="primary" onClick={handleDownload}>
            Telecharger
          </Button>
          <Button variant="secondary" onClick={handleShare}>
            Partager
          </Button>
        </div>

        {downloadProgress > 0 ? (
          <div className="progress-track">
            <div className="progress-bar" style={{ width: `${downloadProgress}%` }} />
          </div>
        ) : null}
      </div>

      <AnimatePresence>
        {isPreviewOpen ? (
          <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: 6 }}>
            <video
              controls
              preload="metadata"
              style={{ marginTop: 12, width: "100%", borderRadius: 12, border: "1px solid var(--border)" }}
            >
              <source src={clip.file_url} type="video/mp4" />
            </video>
          </motion.div>
        ) : null}
      </AnimatePresence>
    </Card>
  );
}

export default memo(ClipCard);
