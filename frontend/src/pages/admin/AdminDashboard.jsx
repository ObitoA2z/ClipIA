import { useQuery } from "@tanstack/react-query";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import api from "../../services/api";

async function fetchOverview() {
  const { data } = await api.get("/admin/overview");
  return data;
}

async function fetchActivity() {
  const { data } = await api.get("/admin/activity", { params: { limit: 15 } });
  return data.items || [];
}

function activityIcon(action) {
  const normalized = String(action || "").toLowerCase();
  if (normalized.includes("payment")) {
    return "💳";
  }
  if (normalized.includes("video") || normalized.includes("clip")) {
    return "🎬";
  }
  if (normalized.includes("error") || normalized.includes("failed")) {
    return "❌";
  }
  if (normalized.includes("register")) {
    return "👋";
  }
  return "ℹ️";
}

function activityColor(action) {
  const normalized = String(action || "").toLowerCase();
  if (normalized.includes("payment")) {
    return "#34D399";
  }
  if (normalized.includes("video") || normalized.includes("clip")) {
    return "#818CF8";
  }
  if (normalized.includes("error") || normalized.includes("failed")) {
    return "#F87171";
  }
  if (normalized.includes("register")) {
    return "#38BDF8";
  }
  return "#94A3B8";
}

export default function AdminDashboard() {
  const overviewQuery = useQuery({ queryKey: ["admin-overview"], queryFn: fetchOverview, refetchInterval: 30000 });
  const activityQuery = useQuery({ queryKey: ["admin-activity"], queryFn: fetchActivity, refetchInterval: 30000 });

  const kpis = overviewQuery.data?.kpis || {};
  const mrrHistory = overviewQuery.data?.mrr_history || [];
  const usersDaily = overviewQuery.data?.users_daily || [];
  const planDistribution = overviewQuery.data?.plan_distribution || [];
  const colors = ["#94A3B8", "#818CF8", "#F59E0B"];

  return (
    <div className="page">
      <div className="grid grid-4">
        <article className="ui-card">
          <p className="caption">MRR</p>
          <h3>{kpis.mrr || 0} EUR</h3>
          <p className="muted" style={{ color: Number(kpis.mrr_change_percent || 0) >= 0 ? "#34D399" : "#F87171" }}>
            {Number(kpis.mrr_change_percent || 0) >= 0 ? "+" : ""}{kpis.mrr_change_percent || 0}% vs mois precedent
          </p>
        </article>
        <article className="ui-card">
          <p className="caption">Utilisateurs</p>
          <h3>{kpis.users_total || 0}</h3>
          <p className="muted">Total actifs</p>
        </article>
        <article className="ui-card">
          <p className="caption">Clips</p>
          <h3>{kpis.clips_total || 0}</h3>
          <p className="muted">Generes</p>
        </article>
        <article className="ui-card">
          <p className="caption">Pipeline</p>
          <h3>{kpis.videos_processing || 0}</h3>
          <p className="muted">Videos en cours</p>
        </article>
      </div>

      <div className="grid grid-2">
        <article className="ui-card">
          <p className="caption">MRR - 12 mois</p>
          <div style={{ width: "100%", height: 260 }}>
            <ResponsiveContainer>
              <LineChart data={mrrHistory}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.2)" />
                <XAxis dataKey="month" stroke="#94A3B8" />
                <YAxis stroke="#94A3B8" />
                <Tooltip />
                <Line type="monotone" dataKey="mrr" stroke="#818CF8" strokeWidth={3} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </article>

        <article className="ui-card">
          <p className="caption">Nouveaux users / jour</p>
          <div style={{ width: "100%", height: 260 }}>
            <ResponsiveContainer>
              <BarChart data={usersDaily}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.2)" />
                <XAxis dataKey="day" hide />
                <YAxis stroke="#94A3B8" />
                <Tooltip />
                <Bar dataKey="users" fill="#6366F1" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </article>
      </div>

      <div className="grid grid-2">
        <article className="ui-card">
          <p className="caption">Repartition des plans</p>
          <div style={{ width: "100%", height: 240 }}>
            <ResponsiveContainer>
              <PieChart>
                <Pie data={planDistribution} dataKey="value" nameKey="name" outerRadius={88}>
                  {planDistribution.map((entry, index) => (
                    <Cell key={entry.name} fill={colors[index % colors.length]} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </article>

        <article className="ui-card">
          <p className="caption">Feed activite</p>
          {activityQuery.isLoading ? <p className="muted">Loading...</p> : null}
          <div style={{ display: "grid", gap: 8, marginTop: 12 }}>
            {(activityQuery.data || []).map((item) => (
              <div key={item.id} className="ui-card" style={{ padding: 12, borderColor: `${activityColor(item.action)}55` }}>
                <p style={{ fontWeight: 600, color: activityColor(item.action) }}>
                  {activityIcon(item.action)} {item.action}
                </p>
                <p className="muted" style={{ fontSize: 13 }}>{item.created_at}</p>
              </div>
            ))}
          </div>
        </article>
      </div>
    </div>
  );
}
