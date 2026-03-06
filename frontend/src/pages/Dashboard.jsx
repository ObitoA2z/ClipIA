import { useMemo } from "react";
import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import toast from "react-hot-toast";

import ProcessingStatus from "../components/ProcessingStatus";
import VideoInput from "../components/VideoInput";
import Card from "../components/ui/Card";
import useAuth from "../hooks/useAuth";
import useVideo from "../hooks/useVideo";

function Dashboard() {
  const { user } = useAuth();
  const { videosQuery, processMutation } = useVideo();

  const videos = videosQuery.data || [];
  const currentVideo = videos[0] || null;

  const stats = useMemo(() => {
    const done = videos.filter((video) => video.status === "done").length;
    const processing = videos.filter((video) => video.status !== "done" && video.status !== "error").length;
    const clips = videos.reduce((sum, item) => sum + (item.clips_count || 0), 0);
    return { done, processing, clips };
  }, [videos]);

  const handleSubmit = async (youtubeUrl) => {
    try {
      await processMutation.mutateAsync(youtubeUrl);
      toast.success("Pipeline lancé avec succès");
    } catch (error) {
      toast.error(error?.response?.data?.detail || "Erreur pendant le lancement du traitement");
    }
  };

  return (
    <section className="page">
      <Card>
        <h2 className="section-title" style={{ fontSize: "2rem" }}>
          Bonjour {user?.full_name || "créateur"} 👋
        </h2>
        <p className="muted">Ton studio ClipAI est prêt. Lance un nouveau traitement ci-dessous.</p>

        <div className="grid grid-3" style={{ marginTop: 16 }}>
          {[{ label: "Vidéos traitées", value: stats.done }, { label: "En cours", value: stats.processing }, { label: "Clips générés", value: stats.clips }].map((item) => (
            <motion.div
              key={item.label}
              className="ui-card"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
            >
              <p className="caption">{item.label}</p>
              <p style={{ fontSize: 32, fontWeight: 700 }}>{item.value}</p>
            </motion.div>
          ))}
        </div>
      </Card>

      <VideoInput isLoading={processMutation.isPending} onSubmit={handleSubmit} />

      {currentVideo ? <ProcessingStatus status={currentVideo.status} progress={currentVideo.progress_percent} /> : null}

      <Card>
        <div className="inline-actions" style={{ justifyContent: "space-between", alignItems: "center" }}>
          <h3>Vidéos récentes</h3>
          <p className="muted">{videos.length} élément(s)</p>
        </div>

        {videosQuery.isLoading ? (
          <div className="grid grid-2" style={{ marginTop: 12 }}>
            <div className="skeleton" />
            <div className="skeleton" />
            <div className="skeleton" />
          </div>
        ) : null}

        {!videosQuery.isLoading && videos.length ? (
          <div className="grid grid-2" style={{ marginTop: 12 }}>
            {videos.map((video) => (
              <motion.article key={video.id} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}>
                <Card>
                  <div className="inline-actions" style={{ justifyContent: "space-between", alignItems: "start" }}>
                    <div>
                      <h4>{video.title}</h4>
                      <p className="muted" style={{ fontSize: 14 }}>
                        {video.status} • {video.progress_percent}% • {video.clips_count} clips
                      </p>
                    </div>
                    {video.thumbnail_url ? (
                      <img
                        src={video.thumbnail_url}
                        alt={video.title}
                        loading="lazy"
                        style={{ width: 120, borderRadius: 10, border: "1px solid var(--border)" }}
                      />
                    ) : null}
                  </div>
                  <Link to={`/video/${video.id}`} style={{ marginTop: 10, display: "inline-flex" }}>
                    <button type="button" className="ui-btn ui-btn-secondary">
                      Voir les clips
                    </button>
                  </Link>
                </Card>
              </motion.article>
            ))}
          </div>
        ) : null}

        {!videosQuery.isLoading && videos.length === 0 ? (
          <p className="muted" style={{ marginTop: 10 }}>
            Aucune vidéo pour le moment. Colle ton premier lien YouTube ci-dessus.
          </p>
        ) : null}
      </Card>
    </section>
  );
}

export default Dashboard;
