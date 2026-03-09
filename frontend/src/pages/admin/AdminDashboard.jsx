import { useQuery } from "@tanstack/react-query";

import api from "../../services/api";

async function fetchOverview() {
  const { data } = await api.get("/admin/overview");
  return data;
}

async function fetchActivity() {
  const { data } = await api.get("/admin/activity", { params: { limit: 15 } });
  return data.items || [];
}

export default function AdminDashboard() {
  const overviewQuery = useQuery({ queryKey: ["admin-overview"], queryFn: fetchOverview, refetchInterval: 30000 });
  const activityQuery = useQuery({ queryKey: ["admin-activity"], queryFn: fetchActivity, refetchInterval: 30000 });

  const kpis = overviewQuery.data?.kpis || {};

  return (
    <div className="grid grid-2">
      <article className="ui-card">
        <p className="caption">KPI</p>
        <div className="grid grid-2" style={{ marginTop: 12 }}>
          <div className="ui-card"><p className="caption">MRR</p><h3>{kpis.mrr || 0} EUR</h3></div>
          <div className="ui-card"><p className="caption">Active users</p><h3>{kpis.users_total || 0}</h3></div>
          <div className="ui-card"><p className="caption">Clips today</p><h3>{kpis.clips_total || 0}</h3></div>
          <div className="ui-card"><p className="caption">Processing</p><h3>{kpis.videos_processing || 0}</h3></div>
        </div>
      </article>

      <article className="ui-card">
        <p className="caption">Activity Feed</p>
        {activityQuery.isLoading ? <p className="muted">Loading...</p> : null}
        <div style={{ display: "grid", gap: 8, marginTop: 12 }}>
          {(activityQuery.data || []).map((item) => (
            <div key={item.id} className="ui-card" style={{ padding: 12 }}>
              <p style={{ fontWeight: 600 }}>{item.action}</p>
              <p className="muted" style={{ fontSize: 13 }}>{item.created_at}</p>
            </div>
          ))}
        </div>
      </article>
    </div>
  );
}
