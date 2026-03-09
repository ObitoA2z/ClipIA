import { NavLink } from "react-router-dom";

const MOBILE_ITEMS = [
  { to: "/dashboard", icon: "🏠", label: "Home" },
  { to: "/dashboard", icon: "✂️", label: "Clips" },
  { to: "/scheduler", icon: "📅", label: "Plan" },
  { to: "/profile", icon: "👤", label: "Profil" },
];

function BottomNav({ hasNotifications = false }) {
  return (
    <nav className="bottom-nav" aria-label="Navigation mobile">
      {MOBILE_ITEMS.map((item, index) => (
        <NavLink
          key={`${item.to}-${index}`}
          to={item.to}
          className={({ isActive }) => `bottom-nav-item${isActive ? " active" : ""}`}
        >
          <span style={{ position: "relative", display: "inline-flex", alignItems: "center", justifyContent: "center" }}>
            <span>{item.icon}</span>
            {hasNotifications && index === 1 ? (
              <span
                style={{
                  position: "absolute",
                  top: -3,
                  right: -8,
                  width: 8,
                  height: 8,
                  borderRadius: "50%",
                  background: "#ef4444",
                }}
              />
            ) : null}
          </span>
          <span>{item.label}</span>
        </NavLink>
      ))}
    </nav>
  );
}

export default BottomNav;
