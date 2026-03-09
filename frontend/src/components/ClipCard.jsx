import { memo, useMemo, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Link } from "react-router-dom";

import Badge from "./ui/Badge";
import Button from "./ui/Button";
import Card from "./ui/Card";

function formatDuration(durationSeconds) {
  const total = Math.max(0, Math.round(durationSeconds || 0));
  const minutes = Math.floor(total / 60);
  const seconds = total % 60;
  return `${minutes}:${String(seconds).padStart(2, "0")}`;
}

function ClipCard({ clip, index = 0 }) {
  const [isPreviewOpen, setIsPreviewOpen] = useState(false);
  const [downloadProgress, setDownloadProgress] = useState(0);

  const durationLabel = useMemo(() => formatDuration(clip.duration_seconds), [clip.duration_seconds]);

  const handleDownload = () => {
    setDownloadProgress(5);
    const timer = window.setInterval(() => {
      setDownloadProgress((value) => {
        if (value >= 100) {
          clearInterval(timer);
          window.open(clip.file_url, "_blank", "noopener,noreferrer");
          return 0;
        }
        return value + 20;
      });
    }, 120);
  };

  return (
    <Card>
      <div className="clip-thumb" style={{ position: "relative" }}>
        <img
          src={clip.thumbnail_url || "https://placehold.co/800x450/12122a/F8FAFC?text=Clip+Preview"}
          alt={clip.title}
          loading="lazy"
          style={{ width: "100%", borderRadius: 14, aspectRatio: "16 / 9", objectFit: "cover" }}
        />
        <span
          style={{
            position: "absolute",
            top: 10,
            right: 10,
            borderRadius: 8,
            background: "rgba(8,8,18,0.75)",
            padding: "4px 8px",
            fontSize: 12
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
              maxWidth: "85%"
            }}
          >
            {clip.title}
          </h4>
          {index === 0 ? <Badge variant="success">Top Pick</Badge> : null}
        </div>

        <p className="muted" style={{ fontSize: 14 }}>
          {clip.start_time}s - {clip.end_time}s
        </p>

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
