import { useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import toast from "react-hot-toast";

import ClipCard from "../components/ClipCard";
import ProcessingStatus from "../components/ProcessingStatus";
import Card from "../components/ui/Card";
import useVideo from "../hooks/useVideo";
import { downloadAllClips } from "../services/videoService";

const FILTERS = [
  { key: "all", label: "Tous" },
  { key: "tiktok", label: "TikTok" },
  { key: "reels", label: "Reels" },
  { key: "shorts", label: "Shorts" },
  { key: "best", label: "Meilleur score" },
];

function VideoDetail() {
  const { videoId } = useParams();
  const { detailsQuery, statusQuery, liveStatus, clipsQuery } = useVideo(videoId);
  const [filter, setFilter] = useState("all");
  const [isDownloadingZip, setIsDownloadingZip] = useState(false);

  const video = detailsQuery.data;
  const status = liveStatus || statusQuery.data;
  const clips = clipsQuery.data || [];

  const headerMeta = useMemo(() => {
    if (!video) {
      return { duration: "--", createdAt: "--" };
    }
    const duration = video.duration_seconds ? `${video.duration_seconds}s` : "--";
    const createdAt = video.created_at ? new Date(video.created_at).toLocaleString("fr-FR") : "--";
    return { duration, createdAt };
  }, [video]);

  const filteredClips = useMemo(() => {
    const sorted = [...clips].sort((a, b) => Number(b.virality_score || 0) - Number(a.virality_score || 0));
    if (filter === "all") {
      return sorted;
    }
    if (filter === "best") {
      return sorted.slice(0, 5);
    }
    return sorted.filter((clip) => String(clip.best_platform || "").toLowerCase() === filter);
  }, [clips, filter]);

  const averageScore = useMemo(() => {
    if (!clips.length) {
      return "--";
    }
    const values = clips.map((clip) => Number(clip.virality_score || 0)).filter((score) => score > 0);
    if (!values.length) {
      return "--";
    }
    const avg = values.reduce((sum, value) => sum + value, 0) / values.length;
    return `${avg.toFixed(1)}/100`;
  }, [clips]);

  const handleDownloadAll = async () => {
    if (!videoId) {
      return;
    }
    setIsDownloadingZip(true);
    try {
      const blob = await downloadAllClips(videoId);
      const blobUrl = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      const safeTitle = String(video?.title || "clips").replace(/[^a-zA-Z0-9_-]+/g, "_");
      anchor.href = blobUrl;
      anchor.download = `${safeTitle}_clips.zip`;
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      URL.revokeObjectURL(blobUrl);
      toast.success("ZIP telecharge");
    } catch (error) {
      toast.error(error?.response?.data?.detail || "Echec du telechargement ZIP");
    } finally {
      setIsDownloadingZip(false);
    }
  };

  return (
    <section className="page">
      <Card className="video-detail-hero" style={{ padding: 0, overflow: "hidden" }}>
        <div
          style={{
            padding: 24,
            backgroundImage: `linear-gradient(180deg, rgba(8,8,18,0.4), rgba(8,8,18,0.95)), url(${video?.thumbnail_url || ""})`,
            backgroundSize: "cover",
            backgroundPosition: "center",
          }}
        >
          <div className="inline-actions" style={{ justifyContent: "space-between", alignItems: "start" }}>
            <div>
              <p className="caption">Detail video</p>
              <h2>{video?.title || "Chargement..."}</h2>
              <p className="muted">
                Duree source: {headerMeta.duration} • Creee: {headerMeta.createdAt}
              </p>
              <p className="muted">
                Clips: {clips.length} • Score moyen: {averageScore}
              </p>
            </div>
            <button type="button" className="ui-btn ui-btn-primary" onClick={handleDownloadAll} disabled={isDownloadingZip}>
              {isDownloadingZip ? "ZIP en cours..." : "⬇️ Telecharger tous les clips (.zip)"}
            </button>
          </div>
        </div>
      </Card>

      <ProcessingStatus
        status={status?.status || video?.status || "pending"}
        progress={status?.progress_percent || video?.progress_percent || 0}
      />

      <Card>
        <div className="inline-actions" style={{ justifyContent: "space-between", alignItems: "center" }}>
          <h3>Clips generes</h3>
          <div className="inline-actions">
            {FILTERS.map((item) => (
              <button
                key={item.key}
                type="button"
                className={`ui-btn ${filter === item.key ? "ui-btn-primary" : "ui-btn-secondary"}`}
                onClick={() => setFilter(item.key)}
              >
                {item.label}
              </button>
            ))}
          </div>
        </div>

        {clipsQuery.isLoading ? (
          <div className="grid grid-3" style={{ marginTop: 14 }}>
            <div className="skeleton" />
            <div className="skeleton" />
            <div className="skeleton" />
          </div>
        ) : null}

        {filteredClips.length ? (
          <div className="grid grid-3" style={{ marginTop: 14 }}>
            {filteredClips.map((clip, index) => (
              <ClipCard key={clip.id} clip={clip} index={index} />
            ))}
          </div>
        ) : null}

        {!clipsQuery.isLoading && !filteredClips.length ? (
          <p className="muted" style={{ marginTop: 10 }}>
            Aucun clip pour ce filtre. Le traitement est peut-etre toujours en cours.
          </p>
        ) : null}
      </Card>
    </section>
  );
}

export default VideoDetail;
