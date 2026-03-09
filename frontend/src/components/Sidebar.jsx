import { NavLink } from "react-router-dom";

import useAuth from "../hooks/useAuth";

const BASE_ITEMS = [
  { to: "/dashboard", icon: "🏠", label: "Dashboard" },
  { to: "/dashboard", icon: "✂️", label: "Mes clips" },
  { to: "/ai-coach", icon: "🤖", label: "AI Coach" },
  { to: "/scheduler", icon: "📅", label: "Planner" },
  { to: "/analytics", icon: "📊", label: "Analytics" },
  { to: "/referral", icon: "🎁", label: "Referral" },
  { to: "/profile", icon: "⚙️", label: "Parametres" },
];

function Sidebar() {
  const { user } = useAuth();
  const plan = user?.plan || "free";
  const videosUsed = Number(user?.videos_used_this_month || 0);
  const usageLabel = plan === "free" ? `${videosUsed}/3 videos` : `${videosUsed} videos`;

  const items = [...BASE_ITEMS];
  if (plan === "business") {
    items.splice(5, 0, { to: "/team", icon: "👥", label: "Team" });
  }
  if (user?.is_admin) {
    items.push({ to: "/admin", icon: "🛡️", label: "Admin" });
  }

  return (
    <aside className="sidebar" aria-label="Navigation principale">
      <NavLink to="/dashboard" style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 10 }}>
        <span style={{ fontSize: 18 }}>✦</span>
        <span className="brand gradient-text">ClipAI</span>
      </NavLink>

      <div style={{ display: "grid", gap: 4 }}>
        {items.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) => `sidebar-link${isActive ? " active" : ""}`}
          >
            <span>{item.icon}</span>
            <span>{item.label}</span>
          </NavLink>
        ))}
      </div>

      <div style={{ marginTop: "auto", display: "grid", gap: 10 }}>
        <div className="ui-card" style={{ padding: 14 }}>
          <p className="caption">Plan actuel</p>
          <p style={{ fontWeight: 700, textTransform: "capitalize" }}>{plan}</p>
          <p className="muted" style={{ fontSize: 13 }}>
            Usage: {usageLabel}
          </p>
        </div>
        <div className="ui-card" style={{ padding: 14 }}>
          <p style={{ fontWeight: 600 }}>{user?.full_name || "Utilisateur"}</p>
          <p className="muted" style={{ fontSize: 13, overflow: "hidden", textOverflow: "ellipsis" }}>
            {user?.email || ""}
          </p>
        </div>
      </div>
    </aside>
  );
}

export default Sidebar;
