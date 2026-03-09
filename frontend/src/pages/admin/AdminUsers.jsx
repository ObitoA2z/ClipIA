import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import toast from "react-hot-toast";

import api from "../../services/api";

async function fetchUsers({ queryKey }) {
  const [, params] = queryKey;
  const { data } = await api.get("/admin/users", { params });
  return data;
}

function planBadge(plan) {
  const current = String(plan || "free").toLowerCase();
  if (current === "business") {
    return "score-badge score-ok";
  }
  if (current === "pro") {
    return "score-badge score-viral";
  }
  return "score-badge";
}

function formatRelative(dateString) {
  if (!dateString) {
    return "--";
  }
  const date = new Date(dateString);
  const diffMs = Date.now() - date.getTime();
  const diffMinutes = Math.floor(diffMs / 60000);
  if (diffMinutes < 60) {
    return `il y a ${diffMinutes} min`;
  }
  const diffHours = Math.floor(diffMinutes / 60);
  if (diffHours < 24) {
    return `il y a ${diffHours}h`;
  }
  const diffDays = Math.floor(diffHours / 24);
  return `il y a ${diffDays}j`;
}

export default function AdminUsers() {
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [selectedPlan, setSelectedPlan] = useState("all");
  const limit = 50;
  const skip = (page - 1) * limit;

  const queryParams = useMemo(
    () => ({
      limit,
      skip,
      search: search || undefined,
      plan: selectedPlan !== "all" ? selectedPlan : undefined,
    }),
    [limit, search, selectedPlan, skip],
  );

  const usersQuery = useQuery({
    queryKey: ["admin-users", queryParams],
    queryFn: fetchUsers,
    refetchInterval: 30000,
    keepPreviousData: true,
  });

  const users = usersQuery.data?.items || [];
  const total = Number(usersQuery.data?.total || 0);
  const totalPages = Math.max(1, Math.ceil(total / limit));

  const handleAction = async (userId, action, payload = {}) => {
    try {
      if (action === "activity") {
        const { data } = await api.get(`/admin/users/${userId}/activity`, { params: { limit: 20 } });
        toast.success(`Activite chargee (${data.total})`);
        return;
      }
      if (action === "plan") {
        await api.post(`/admin/users/${userId}/plan`, { plan: payload.plan });
      }
      if (action === "suspend") {
        await api.post(`/admin/users/${userId}/suspend`, { reason: "Moderation admin" });
      }
      if (action === "unsuspend") {
        await api.post(`/admin/users/${userId}/unsuspend`);
      }
      if (action === "ban") {
        await api.post(`/admin/users/${userId}/ban`, { reason: "Violation CGU" });
      }
      if (action === "email") {
        await api.post(`/admin/users/${userId}/email`, {
          subject: "Message admin ClipAI",
          message: "Bonjour, ceci est un message admin test.",
        });
      }
      toast.success("Action admin executee");
      await usersQuery.refetch();
    } catch (error) {
      toast.error(error?.response?.data?.detail || "Action admin impossible");
    }
  };

  const exportCsv = () => {
    const headers = ["Email", "Nom", "Plan", "Inscription", "Dernier actif", "Admin"];
    const rows = users.map((user) => [
      user.email,
      user.full_name,
      user.plan,
      user.created_at,
      user.last_active_at || "",
      user.is_admin ? "Yes" : "No",
    ]);
    const csv = [headers, ...rows].map((line) => line.map((value) => `"${String(value || "").replaceAll("\"", "\"\"")}"`).join(",")).join("\n");
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "clipai_users.csv";
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  };

  return (
    <article className="ui-card">
      <div className="inline-actions" style={{ justifyContent: "space-between", alignItems: "center" }}>
        <h3>Utilisateurs</h3>
        <div className="inline-actions">
          <select className="ui-input" value={selectedPlan} onChange={(event) => { setSelectedPlan(event.target.value); setPage(1); }} style={{ width: 160 }}>
            <option value="all">Tous les plans</option>
            <option value="free">Free</option>
            <option value="pro">Pro</option>
            <option value="business">Business</option>
          </select>
          <input
            className="ui-input"
            style={{ width: 260 }}
            placeholder="Recherche email/nom"
            value={search}
            onChange={(event) => { setSearch(event.target.value); setPage(1); }}
          />
          <button type="button" className="ui-btn ui-btn-secondary" onClick={exportCsv}>
            Export CSV
          </button>
        </div>
      </div>

      <div style={{ overflowX: "auto", marginTop: 12 }}>
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr>
              <th align="left">Email</th>
              <th align="left">Nom</th>
              <th align="left">Plan</th>
              <th align="left">Inscription</th>
              <th align="left">Dernier actif</th>
              <th align="left">Admin</th>
              <th align="left">Actions</th>
            </tr>
          </thead>
          <tbody>
            {users.map((user) => (
              <tr key={user.id} style={{ borderTop: "1px solid var(--border)" }}>
                <td style={{ padding: "10px 6px" }}>{user.email}</td>
                <td>{user.full_name}</td>
                <td><span className={planBadge(user.plan)}>{user.plan}</span></td>
                <td>{user.created_at}</td>
                <td>{formatRelative(user.last_active_at)}</td>
                <td>{user.is_admin ? "Yes" : "No"}</td>
                <td>
                  <div className="inline-actions">
                    <select
                      className="ui-input"
                      defaultValue=""
                      onChange={(event) => {
                        const value = event.target.value;
                        if (!value) {
                          return;
                        }
                        if (value.startsWith("plan:")) {
                          void handleAction(user.id, "plan", { plan: value.split(":")[1] });
                        } else {
                          void handleAction(user.id, value);
                        }
                        event.target.value = "";
                      }}
                      style={{ width: 180 }}
                    >
                      <option value="">Choisir...</option>
                      <option value="activity">Voir activite</option>
                      <option value="plan:free">Passer Free</option>
                      <option value="plan:pro">Passer Pro</option>
                      <option value="plan:business">Passer Business</option>
                      <option value="email">Envoyer email</option>
                      <option value="suspend">Suspendre</option>
                      <option value="unsuspend">Unsuspendre</option>
                      <option value="ban">Bannir</option>
                    </select>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="inline-actions" style={{ justifyContent: "space-between", marginTop: 12 }}>
        <p className="muted">{total} utilisateurs</p>
        <div className="inline-actions">
          <button type="button" className="ui-btn ui-btn-secondary" disabled={page <= 1} onClick={() => setPage((value) => Math.max(1, value - 1))}>
            Precedent
          </button>
          <span className="muted">Page {page}/{totalPages}</span>
          <button type="button" className="ui-btn ui-btn-secondary" disabled={page >= totalPages} onClick={() => setPage((value) => Math.min(totalPages, value + 1))}>
            Suivant
          </button>
        </div>
      </div>
    </article>
  );
}
