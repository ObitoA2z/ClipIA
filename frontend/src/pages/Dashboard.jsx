import { useMemo, useState } from "react";
import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import toast from "react-hot-toast";

import ProcessingStatus from "../components/ProcessingStatus";
import VideoInput from "../components/VideoInput";
import Card from "../components/ui/Card";
import useAuth from "../hooks/useAuth";
import useVideo from "../hooks/useVideo";

const FILTERS = [
  { key: "all", label: "Tout" },
  { key: "processing", label: "En cours" },
  { key: "done", label: "Terminees" },
  { key: "error", label: "Erreurs" },
];

function statusBadge(status) {
  const current = String(status || "pending").toLowerCase();
  if (current === "done") {
    return { label: "Done", className: "score-badge score-good" };
  }
  if (current === "error") {
    return { label: "Erreur", className: "score-badge score-low" };
  }
  return { label: "Traitement", className: "score-badge score-viral" };
}

function Dashboard() {
  const { user } = useAuth();
  const { videosQuery, processMutation } = useVideo();
  const [filter, setFilter] = useState("all");
  const [search, setSearch] = useState("");

  const videos = videosQuery.data || [];
  const currentVideo = videos.find((video) => video.status !== "done" && video.status !== "error") || videos[0] || null;

  const stats = useMemo(() => {
    const done = videos.filter((video) => video.status === "done").length;
    const processing = videos.filter((video) => video.status !== "done" && video.status !== "error").length;
    const clips = videos.reduce((sum, item) => sum + Number(item.clips_count || 0), 0);
    const hoursSaved = (clips * 0.25).toFixed(1);
    return { done, processing, clips, hoursSaved };
  }, [videos]);

  const filteredVideos = useMemo(() => {
    const term = search.trim().toLowerCase();
    return videos.filter((video) => {
      const matchesFilter =
        filter === "all" ||
        (filter === "processing" && video.status !== "done" && video.status !== "error") ||
        (filter === "done" && video.status === "done") ||
        (filter === "error" && video.status === "error");
      const matchesSearch =
        !term ||
        String(video.title || "").toLowerCase().includes(term) ||
        String(video.youtube_id || "").toLowerCase().includes(term);
      return matchesFilter && matchesSearch;
    });
  }, [filter, search, videos]);

  const handleSubmit = async (payload) => {
    try {
      await processMutation.mutateAsync(payload);
      toast.success("Pipeline lance avec succes");
    } catch (error) {
      toast.error(error?.response?.data?.detail || "Erreur pendant le lancement du traitement");
    }
  };

  return (
    <section className="page">
      <Card>
        <h2 className="section-title" style={{ fontSize: "2rem" }}>
          Bonjour {user?.full_name || "createur"} 👋
        </h2>
        <p className="muted">Ton studio ClipAI est pret. Lance un nouveau traitement ci-dessous.</p>

        <div className="grid grid-4" style={{ marginTop: 16 }}>
          {[
            { label: "Videos traitees", value: stats.done },
            { label: "En cours", value: stats.processing },
            { label: "Clips generes", value: stats.clips },
            { label: "Heures economisees", value: `${stats.hoursSaved}h` },
          ].map((item, index) => (
            <motion.div
              key={item.label}
              className="ui-card"
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.06 }}
            >
              <p className="caption">{item.label}</p>
              <p style={{ fontSize: 32, fontWeight: 700 }}>{item.value}</p>
            </motion.div>
          ))}
        </div>
      </Card>

      {stats.processing > 0 ? (
        <div className="ui-card" style={{ borderColor: "var(--border-hover)", animation: "glowPulse 2.2s ease infinite" }}>
          🔄 {stats.processing} traitement(s) en cours
        </div>
      ) : null}

      <VideoInput isLoading={processMutation.isPending} onSubmit={handleSubmit} />

      {currentVideo ? <ProcessingStatus status={currentVideo.status} progress={currentVideo.progress_percent} /> : null}

      <Card>
        <div className="inline-actions" style={{ justifyContent: "space-between", alignItems: "center" }}>
          <h3>Videos recentes</h3>
          <p className="muted">{filteredVideos.length} element(s)</p>
        </div>

        <div className="inline-actions" style={{ marginTop: 12, justifyContent: "space-between", alignItems: "center" }}>
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
          <input
            className="ui-input"
            style={{ width: 280 }}
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Rechercher une video..."
          />
        </div>

        {videosQuery.isLoading ? (
          <div className="grid grid-2" style={{ marginTop: 12 }}>
            <div className="skeleton" />
            <div className="skeleton" />
            <div className="skeleton" />
          </div>
        ) : null}

        {!videosQuery.isLoading && filteredVideos.length ? (
          <div className="grid grid-2" style={{ marginTop: 12 }}>
            {filteredVideos.map((video) => {
              const badge = statusBadge(video.status);
              return (
                <motion.article key={video.id} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}>
                  <Card className="video-card">
                    <div className="video-thumb">
                      {video.thumbnail_url ? (
                        <img
                          src={video.thumbnail_url}
                          alt={video.title}
                          loading="lazy"
                          style={{ width: "100%", borderRadius: 12, objectFit: "cover", aspectRatio: "16/9" }}
                        />
                      ) : (
                        <div className="skeleton" style={{ height: 120 }} />
                      )}
                    </div>
                    <div style={{ marginTop: 10, display: "grid", gap: 8 }}>
                      <div className="inline-actions" style={{ justifyContent: "space-between", alignItems: "center" }}>
                        <h4 style={{ maxWidth: "80%", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                          {video.title || "Video sans titre"}
                        </h4>
                        <span className={badge.className}>{badge.label}</span>
                      </div>
                      <p className="muted" style={{ fontSize: 14 }}>
                        {video.progress_percent}% • {video.clips_count || 0} clips
                      </p>
                      <p className="muted" style={{ fontSize: 13 }}>
                        Score moyen: {video.avg_virality_score ? `${video.avg_virality_score}/100` : "--"}
                      </p>
                      <Link to={`/video/${video.id}`} className="video-card-cta">
                        <button type="button" className="ui-btn ui-btn-secondary">
                          Voir les clips
                        </button>
                      </Link>
                    </div>
                  </Card>
                </motion.article>
              );
            })}
          </div>
        ) : null}

        {!videosQuery.isLoading && filteredVideos.length === 0 ? (
          <p className="muted" style={{ marginTop: 10 }}>
            Aucune video pour le filtre actuel.
          </p>
        ) : null}
      </Card>
    </section>
  );
}

export default Dashboard;
