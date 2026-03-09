import { Link, Outlet } from "react-router-dom";

const NAV_ITEMS = [
  { to: "/admin", label: "Overview" },
  { to: "/admin/users", label: "Users" },
  { to: "/admin/pipeline", label: "Pipeline" },
  { to: "/admin/analytics", label: "Analytics" },
  { to: "/admin/settings", label: "Settings" },
  { to: "/admin/tools", label: "Tools" }
];

export default function AdminLayout() {
  return (
    <section className="page" style={{ gap: 16 }}>
      <div className="ui-card" style={{ borderColor: "rgba(34, 211, 238, 0.35)" }}>
        <p className="caption">ADMIN PANEL</p>
        <h2 className="section-title" style={{ fontSize: "2rem" }}>ClipAI Control Center</h2>
        <div className="inline-actions" style={{ marginTop: 14 }}>
          {NAV_ITEMS.map((item) => (
            <Link key={item.to} to={item.to}>
              <button type="button" className="ui-btn ui-btn-secondary">{item.label}</button>
            </Link>
          ))}
        </div>
      </div>
      <Outlet />
    </section>
  );
}
