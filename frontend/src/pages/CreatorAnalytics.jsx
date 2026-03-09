import { useMemo } from "react";

import useVideo from "../hooks/useVideo";

export default function CreatorAnalytics() {
  const { videosQuery } = useVideo();
  const videos = videosQuery.data || [];

  const stats = useMemo(() => {
    const clips = videos.reduce((sum, item) => sum + (item.clips_count || 0), 0);
    const savedHours = Math.round((clips * 15) / 60);
    const avgClipDuration = clips ? 45 : 0;
    return {
      videos: videos.length,
      clips,
      savedHours,
      avgClipDuration,
    };
  }, [videos]);

  return (
    <section className="page">
      <article className="ui-card">
        <p className="caption">CREATOR ANALYTICS</p>
        <h2 className="section-title" style={{ fontSize: "2rem" }}>
          Performance personnelle
        </h2>
        <div className="grid grid-3" style={{ marginTop: 16 }}>
          <div className="ui-card"><p className="caption">Videos traitees</p><h3>{stats.videos}</h3></div>
          <div className="ui-card"><p className="caption">Clips generes</p><h3>{stats.clips}</h3></div>
          <div className="ui-card"><p className="caption">Heures economisees</p><h3>{stats.savedHours}h</h3></div>
          <div className="ui-card"><p className="caption">Duree moyenne</p><h3>{stats.avgClipDuration}s</h3></div>
        </div>
      </article>
    </section>
  );
}

