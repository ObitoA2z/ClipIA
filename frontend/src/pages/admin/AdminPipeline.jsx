import { useQuery } from "@tanstack/react-query";

import api from "../../services/api";

async function fetchPipeline() {
  const { data } = await api.get("/admin/pipeline");
  return data;
}

export default function AdminPipeline() {
  const pipelineQuery = useQuery({ queryKey: ["admin-pipeline"], queryFn: fetchPipeline, refetchInterval: 10000 });
  const data = pipelineQuery.data || { in_progress: [], errors: [], queue_size: 0, workers_active: 0 };

  return (
    <div className="grid grid-2">
      <article className="ui-card">
        <h3>Queue</h3>
        <p className="muted">Queue size: {data.queue_size}</p>
        <p className="muted">Workers: {data.workers_active}</p>
        <div style={{ display: "grid", gap: 8, marginTop: 10 }}>
          {(data.in_progress || []).map((video) => (
            <div key={video.id} className="ui-card" style={{ padding: 10 }}>
              <p style={{ fontWeight: 600 }}>{video.title}</p>
              <p className="muted">{video.status} - {video.progress_percent}%</p>
            </div>
          ))}
        </div>
      </article>

      <article className="ui-card">
        <h3>Errors</h3>
        <div style={{ display: "grid", gap: 8, marginTop: 10 }}>
          {(data.errors || []).map((video) => (
            <div key={video.id} className="ui-card" style={{ padding: 10, borderColor: "rgba(239,68,68,0.35)" }}>
              <p style={{ fontWeight: 600 }}>{video.title}</p>
              <p className="muted">{video.error_message || "Pipeline error"}</p>
            </div>
          ))}
        </div>
      </article>
    </div>
  );
}
