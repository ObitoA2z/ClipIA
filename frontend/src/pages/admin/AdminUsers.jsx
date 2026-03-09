import { useState } from "react";
import { useQuery } from "@tanstack/react-query";

import api from "../../services/api";

async function fetchUsers() {
  const { data } = await api.get("/admin/users", { params: { limit: 100 } });
  return data.items || [];
}

export default function AdminUsers() {
  const [search, setSearch] = useState("");
  const usersQuery = useQuery({ queryKey: ["admin-users"], queryFn: fetchUsers, refetchInterval: 30000 });

  const users = (usersQuery.data || []).filter((user) => {
    const term = search.toLowerCase();
    return user.email?.toLowerCase().includes(term) || user.full_name?.toLowerCase().includes(term);
  });

  return (
    <article className="ui-card">
      <div className="inline-actions" style={{ justifyContent: "space-between", alignItems: "center" }}>
        <h3>Utilisateurs</h3>
        <input className="ui-input" style={{ width: 260 }} placeholder="Recherche email/nom" value={search} onChange={(e) => setSearch(e.target.value)} />
      </div>
      <div style={{ overflowX: "auto", marginTop: 12 }}>
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr>
              <th align="left">Email</th>
              <th align="left">Nom</th>
              <th align="left">Plan</th>
              <th align="left">Inscription</th>
              <th align="left">Admin</th>
            </tr>
          </thead>
          <tbody>
            {users.map((user) => (
              <tr key={user.id} style={{ borderTop: "1px solid var(--border)" }}>
                <td style={{ padding: "10px 6px" }}>{user.email}</td>
                <td>{user.full_name}</td>
                <td>{user.plan}</td>
                <td>{user.created_at}</td>
                <td>{user.is_admin ? "Yes" : "No"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </article>
  );
}
