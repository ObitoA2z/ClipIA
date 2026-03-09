import { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";

import useAuth from "../hooks/useAuth";

const BASE_ACTIONS = [
  { id: "dashboard", label: "Aller au Dashboard", to: "/dashboard", icon: "🏠" },
  { id: "video-new", label: "Nouvelle video", to: "/dashboard", icon: "➕" },
  { id: "clips", label: "Mes clips", to: "/dashboard", icon: "✂️" },
  { id: "settings", label: "Parametres", to: "/profile", icon: "⚙️" },
];

function CommandPalette({ open, onClose }) {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [query, setQuery] = useState("");
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef(null);

  const actions = useMemo(() => {
    const result = [...BASE_ACTIONS];
    if (user?.is_admin) {
      result.push({ id: "admin", label: "Panel Admin", to: "/admin", icon: "🛡️" });
    }
    result.push({ id: "logout", label: "Deconnexion", icon: "↩️", destructive: true });
    return result;
  }, [user?.is_admin]);

  const filtered = useMemo(() => {
    const term = query.trim().toLowerCase();
    if (!term) {
      return actions;
    }
    return actions.filter((action) => action.label.toLowerCase().includes(term));
  }, [actions, query]);

  useEffect(() => {
    if (!open) {
      setQuery("");
      setSelectedIndex(0);
      return;
    }
    inputRef.current?.focus();
  }, [open]);

  useEffect(() => {
    if (!open) {
      return;
    }
    const onKeyDown = (event) => {
      if (event.key === "Escape") {
        onClose();
        return;
      }
      if (event.key === "ArrowDown") {
        event.preventDefault();
        setSelectedIndex((index) => Math.min(filtered.length - 1, index + 1));
        return;
      }
      if (event.key === "ArrowUp") {
        event.preventDefault();
        setSelectedIndex((index) => Math.max(0, index - 1));
        return;
      }
      if (event.key === "Enter") {
        event.preventDefault();
        const action = filtered[selectedIndex];
        if (action) {
          void runAction(action);
        }
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [filtered, onClose, open, selectedIndex]);

  const runAction = async (action) => {
    if (!action) {
      return;
    }
    if (action.id === "logout") {
      await logout();
      navigate("/login");
      onClose();
      return;
    }
    if (action.to) {
      navigate(action.to);
    }
    onClose();
  };

  if (!open) {
    return null;
  }

  return (
    <div className="cmd-overlay" role="dialog" aria-modal="true" onClick={onClose}>
      <div className="cmd-box" onClick={(event) => event.stopPropagation()}>
        <input
          ref={inputRef}
          className="cmd-input"
          value={query}
          onChange={(event) => {
            setQuery(event.target.value);
            setSelectedIndex(0);
          }}
          placeholder="Tape une commande..."
        />
        <div style={{ maxHeight: 360, overflowY: "auto" }}>
          {filtered.length ? (
            filtered.map((action, index) => (
              <button
                key={action.id}
                type="button"
                className={`cmd-result${index === selectedIndex ? " selected" : ""}`}
                onMouseEnter={() => setSelectedIndex(index)}
                onClick={() => void runAction(action)}
                style={{
                  width: "100%",
                  textAlign: "left",
                  border: "none",
                  background: "transparent",
                  color: action.destructive ? "#fda4af" : "var(--text-primary)",
                }}
              >
                <span>{action.icon}</span>
                <span>{action.label}</span>
              </button>
            ))
          ) : (
            <p className="muted" style={{ padding: "14px 20px" }}>
              Aucune commande trouvee.
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

export default CommandPalette;
