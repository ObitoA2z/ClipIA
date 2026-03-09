import { useState } from "react";
import toast from "react-hot-toast";

import useAuth from "../hooks/useAuth";

export default function Profile() {
  const { user } = useAuth();
  const [language, setLanguage] = useState("fr");
  const [timezone, setTimezone] = useState("Europe/Paris");
  const [format, setFormat] = useState("all");
  const [quality, setQuality] = useState("1080p");

  return (
    <section className="page">
      <article className="ui-card">
        <p className="caption">PROFILE</p>
        <h2 className="section-title" style={{ fontSize: "2rem" }}>
          Mon compte
        </h2>
        <p className="muted">{user?.email}</p>

        <div className="grid grid-2" style={{ marginTop: 16 }}>
          <div className="ui-card">
            <h3>Informations</h3>
            <p className="muted">Nom: {user?.full_name || "-"}</p>
            <p className="muted">Plan: {user?.plan || "free"}</p>
            <p className="muted">2FA: {user?.two_factor_enabled ? "Active" : "Inactive"}</p>
          </div>

          <div className="ui-card">
            <h3>Preferences</h3>
            <div className="grid" style={{ gap: 8, marginTop: 10 }}>
              <label>
                Langue
                <select className="ui-input" value={language} onChange={(e) => setLanguage(e.target.value)}>
                  <option value="fr">Francais</option>
                  <option value="en">English</option>
                </select>
              </label>
              <label>
                Fuseau
                <input className="ui-input" value={timezone} onChange={(e) => setTimezone(e.target.value)} />
              </label>
              <label>
                Format prefere
                <select className="ui-input" value={format} onChange={(e) => setFormat(e.target.value)}>
                  <option value="all">Tous</option>
                  <option value="tiktok">TikTok</option>
                  <option value="reels">Reels</option>
                  <option value="shorts">Shorts</option>
                </select>
              </label>
              <label>
                Qualite
                <select className="ui-input" value={quality} onChange={(e) => setQuality(e.target.value)}>
                  <option value="720p">720p</option>
                  <option value="1080p">1080p</option>
                </select>
              </label>
            </div>
          </div>
        </div>

        <div className="inline-actions" style={{ marginTop: 16 }}>
          <button type="button" className="ui-btn ui-btn-secondary" onClick={() => toast.success("Export RGPD lancé")}>
            Exporter mes donnees
          </button>
          <button type="button" className="ui-btn ui-btn-secondary" onClick={() => toast.error("Suppression compte: confirmation requise")}>
            Supprimer mon compte
          </button>
        </div>
      </article>
    </section>
  );
}

