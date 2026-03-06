import { useMemo } from "react";
import { useParams } from "react-router-dom";

import ClipCard from "../components/ClipCard";
import ProcessingStatus from "../components/ProcessingStatus";
import Card from "../components/ui/Card";
import useVideo from "../hooks/useVideo";

function VideoDetail() {
  const { videoId } = useParams();
  const { detailsQuery, statusQuery, clipsQuery } = useVideo(videoId);

  const video = detailsQuery.data;
  const status = statusQuery.data;

  const headerMeta = useMemo(() => {
    if (!video) {
      return { duration: "--", createdAt: "--" };
    }
    const duration = video.duration_seconds ? `${video.duration_seconds}s` : "--";
    const createdAt = video.created_at ? new Date(video.created_at).toLocaleString("fr-FR") : "--";
    return { duration, createdAt };
  }, [video]);

  return (
    <section className="page">
      <Card>
        <div className="inline-actions" style={{ justifyContent: "space-between", alignItems: "start" }}>
          <div>
            <p className="caption">Détail vidéo</p>
            <h2>{video?.title || "Chargement..."}</h2>
            <p className="muted">Durée: {headerMeta.duration} • Créée: {headerMeta.createdAt}</p>
          </div>
          {video?.thumbnail_url ? (
            <img
              src={video.thumbnail_url}
              alt={video?.title}
              loading="lazy"
              style={{ width: 260, borderRadius: 14, border: "1px solid var(--border)" }}
            />
          ) : null}
        </div>
      </Card>

      <ProcessingStatus
        status={status?.status || video?.status || "pending"}
        progress={status?.progress_percent || video?.progress_percent || 0}
      />

      <Card>
        <h3>Clips générés</h3>
        {clipsQuery.isLoading ? (
          <div className="grid grid-3" style={{ marginTop: 14 }}>
            <div className="skeleton" />
            <div className="skeleton" />
            <div className="skeleton" />
          </div>
        ) : null}

        {clipsQuery.data?.length ? (
          <div className="grid grid-3" style={{ marginTop: 14 }}>
            {clipsQuery.data.map((clip, index) => (
              <ClipCard key={clip.id} clip={clip} index={index} />
            ))}
          </div>
        ) : null}

        {!clipsQuery.isLoading && !clipsQuery.data?.length ? (
          <p className="muted" style={{ marginTop: 10 }}>
            Aucun clip pour le moment. Le traitement est peut-être toujours en cours.
          </p>
        ) : null}
      </Card>
    </section>
  );
}

export default VideoDetail;
