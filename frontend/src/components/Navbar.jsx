import { useEffect, useState } from "react";
import { Link, NavLink } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";

import useAuth from "../hooks/useAuth";
import Badge from "./ui/Badge";
import Button from "./ui/Button";

function Navbar() {
  const { isAuthenticated, user, logout } = useAuth();
  const [menuOpen, setMenuOpen] = useState(false);
  const [isScrolled, setIsScrolled] = useState(false);

  useEffect(() => {
    const onScroll = () => setIsScrolled(window.scrollY > 8);
    onScroll();
    window.addEventListener("scroll", onScroll);
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  const plan = user?.plan || "free";

  return (
    <header className="navbar" style={{ borderColor: isScrolled ? "var(--border-hover)" : "var(--border)" }}>
      <div className="navbar-inner">
        <Link to="/" style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <motion.span
            animate={{ rotate: [0, 12, -8, 0] }}
            transition={{ duration: 2.2, repeat: Number.POSITIVE_INFINITY, repeatDelay: 4 }}
            style={{ color: "var(--accent)", fontSize: 18 }}
          >
            ✦
          </motion.span>
          <span className="brand gradient-text">ClipAI</span>
        </Link>

        <nav className="nav-links" aria-label="Navigation principale">
          <NavLink to="/" className="nav-link">
            Accueil
          </NavLink>
          <NavLink to="/pricing" className="nav-link">
            Tarifs
          </NavLink>
          {isAuthenticated ? (
            <NavLink to="/dashboard" className="nav-link">
              Dashboard
            </NavLink>
          ) : null}
          {isAuthenticated ? (
            <NavLink to="/profile" className="nav-link">
              Profil
            </NavLink>
          ) : null}
          {isAuthenticated ? (
            <NavLink to="/analytics" className="nav-link">
              Stats
            </NavLink>
          ) : null}
          {isAuthenticated ? (
            <NavLink to="/scheduler" className="nav-link">
              Planner
            </NavLink>
          ) : null}
          {isAuthenticated ? (
            <NavLink to="/team" className="nav-link">
              Team
            </NavLink>
          ) : null}
          {isAuthenticated ? (
            <NavLink to="/referral" className="nav-link">
              Referral
            </NavLink>
          ) : null}
          {isAuthenticated && user?.is_admin ? (
            <NavLink to="/admin" className="nav-link">
              Admin
            </NavLink>
          ) : null}
        </nav>

        <div className="inline-actions" style={{ alignItems: "center" }}>
          <Badge variant="primary">Plan {plan === "free" ? "Free" : "Pro"}</Badge>
          {isAuthenticated ? (
            <>
              <span className="muted" style={{ maxWidth: 170, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                {user?.full_name || "Utilisateur"}
              </span>
              <Button variant="secondary" onClick={logout}>
                Deconnexion
              </Button>
            </>
          ) : (
            <>
              <Link to="/login">
                <Button variant="secondary">Connexion</Button>
              </Link>
              <Link to="/register">
                <Button variant="accent">Essai gratuit</Button>
              </Link>
            </>
          )}
          <button
            type="button"
            className="ui-btn ui-btn-secondary mobile-menu-toggle"
            onClick={() => setMenuOpen((open) => !open)}
            aria-label="Ouvrir le menu"
          >
            ☰
          </button>
        </div>
      </div>

      <AnimatePresence>
        {menuOpen ? (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            className="ui-card"
            style={{ margin: "0 12px 12px", padding: 12 }}
          >
            <div className="grid" style={{ gap: 10 }}>
              <NavLink to="/" onClick={() => setMenuOpen(false)}>
                Accueil
              </NavLink>
              <NavLink to="/pricing" onClick={() => setMenuOpen(false)}>
                Tarifs
              </NavLink>
              {isAuthenticated ? (
                <NavLink to="/dashboard" onClick={() => setMenuOpen(false)}>
                  Dashboard
                </NavLink>
              ) : null}
              {isAuthenticated ? (
                <NavLink to="/profile" onClick={() => setMenuOpen(false)}>
                  Profil
                </NavLink>
              ) : null}
              {isAuthenticated ? (
                <NavLink to="/analytics" onClick={() => setMenuOpen(false)}>
                  Stats
                </NavLink>
              ) : null}
              {isAuthenticated ? (
                <NavLink to="/scheduler" onClick={() => setMenuOpen(false)}>
                  Planner
                </NavLink>
              ) : null}
              {isAuthenticated ? (
                <NavLink to="/team" onClick={() => setMenuOpen(false)}>
                  Team
                </NavLink>
              ) : null}
              {isAuthenticated ? (
                <NavLink to="/referral" onClick={() => setMenuOpen(false)}>
                  Referral
                </NavLink>
              ) : null}
              {isAuthenticated && user?.is_admin ? (
                <NavLink to="/admin" onClick={() => setMenuOpen(false)}>
                  Admin
                </NavLink>
              ) : null}
            </div>
          </motion.div>
        ) : null}
      </AnimatePresence>
    </header>
  );
}

export default Navbar;
