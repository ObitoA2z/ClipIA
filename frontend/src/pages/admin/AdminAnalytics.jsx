import { useQuery } from "@tanstack/react-query";

import api from "../../services/api";

async function fetchAnalytics() {
  const { data } = await api.get("/admin/analytics");
  return data;
}

export default function AdminAnalytics() {
  const analyticsQuery = useQuery({ queryKey: ["admin-analytics"], queryFn: fetchAnalytics, refetchInterval: 30000 });
  const data = analyticsQuery.data || {};

  return (
    <article className="ui-card">
      <h3>Analytics</h3>
      <div className="grid grid-3" style={{ marginTop: 12 }}>
        <div className="ui-card"><p className="caption">Users</p><h4>{data.users_total || 0}</h4></div>
        <div className="ui-card"><p className="caption">Videos</p><h4>{data.videos_total || 0}</h4></div>
        <div className="ui-card"><p className="caption">Clips</p><h4>{data.clips_total || 0}</h4></div>
        <div className="ui-card"><p className="caption">Activation</p><h4>{data.activation_rate_percent || 0}%</h4></div>
        <div className="ui-card"><p className="caption">Conversion</p><h4>{data.free_to_pro_conversion_percent || 0}%</h4></div>
      </div>
    </article>
  );
}
