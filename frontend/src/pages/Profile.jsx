import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import toast from "react-hot-toast";

import api from "../services/api";
import useAuth from "../hooks/useAuth";
import {
  changePassword,
  disableTwoFactor,
  enableTwoFactor,
  getPreferences,
  listSessions,
  revokeSession,
  setupTwoFactor,
  updatePreferences,
  updateProfile,
} from "../services/authService";
import { getBillingPortal } from "../services/paymentService";

function Profile() {
  const navigate = useNavigate();
  const { user, refreshUser, logout } = useAuth();
  const [profileForm, setProfileForm] = useState({
    full_name: "",
    avatar_url: "",
    bio: "",
    youtube_url: "",
  });
  const [preferences, setPreferences] = useState({
    language: "fr",
    timezone: "Europe/Paris",
    preferred_format: "all",
    preferred_quality: "1080p",
    subtitles_default: true,
  });
  const [passwordForm, setPasswordForm] = useState({ current_password: "", new_password: "" });
  const [deletePassword, setDeletePassword] = useState("");
  const [sessions, setSessions] = useState([]);
  const [twoFactorSetup, setTwoFactorSetup] = useState(null);
  const [twoFactorCode, setTwoFactorCode] = useState("");
  const [billingUrl, setBillingUrl] = useState("");
  const [loading, setLoading] = useState({
    profile: false,
    preferences: false,
    password: false,
    setup2fa: false,
    enable2fa: false,
    disable2fa: false,
    sessions: false,
  });

  useEffect(() => {
    setProfileForm({
      full_name: user?.full_name || "",
      avatar_url: user?.avatar_url || "",
      bio: user?.bio || "",
      youtube_url: user?.youtube_url || "",
    });
  }, [user]);

  useEffect(() => {
    async function loadData() {
      try {
        const [prefs, userSessions, billing] = await Promise.all([getPreferences(), listSessions(), getBillingPortal()]);
        setPreferences((prev) => ({ ...prev, ...(prefs.preferences || {}) }));
        setSessions(userSessions || []);
        setBillingUrl(billing?.url || "");
      } catch {
        // non-blocking for profile page
      }
    }
    void loadData();
  }, []);

  const handleProfileUpdate = async (event) => {
    event.preventDefault();
    setLoading((prev) => ({ ...prev, profile: true }));
    try {
      await updateProfile(profileForm);
      await refreshUser();
      toast.success("Profil mis a jour");
    } catch (error) {
      toast.error(error?.response?.data?.detail || "Impossible de mettre a jour le profil");
    } finally {
      setLoading((prev) => ({ ...prev, profile: false }));
    }
  };

  const handlePreferencesUpdate = async (event) => {
    event.preventDefault();
    setLoading((prev) => ({ ...prev, preferences: true }));
    try {
      await updatePreferences(preferences);
      toast.success("Preferences sauvegardees");
    } catch (error) {
      toast.error(error?.response?.data?.detail || "Echec sauvegarde preferences");
    } finally {
      setLoading((prev) => ({ ...prev, preferences: false }));
    }
  };

  const handlePasswordChange = async (event) => {
    event.preventDefault();
    setLoading((prev) => ({ ...prev, password: true }));
    try {
      await changePassword(passwordForm);
      toast.success("Mot de passe modifie. Reconnexion requise.");
      await logout();
      navigate("/login");
    } catch (error) {
      toast.error(error?.response?.data?.detail || "Impossible de changer le mot de passe");
    } finally {
      setLoading((prev) => ({ ...prev, password: false }));
    }
  };

  const handleSetup2fa = async () => {
    setLoading((prev) => ({ ...prev, setup2fa: true }));
    try {
      const data = await setupTwoFactor();
      setTwoFactorSetup(data);
      toast.success("QR Code genere");
    } catch (error) {
      toast.error(error?.response?.data?.detail || "Impossible d'initialiser le 2FA");
    } finally {
      setLoading((prev) => ({ ...prev, setup2fa: false }));
    }
  };

  const handleEnable2fa = async () => {
    setLoading((prev) => ({ ...prev, enable2fa: true }));
    try {
      await enableTwoFactor(twoFactorCode.trim());
      setTwoFactorSetup(null);
      setTwoFactorCode("");
      await refreshUser();
      toast.success("2FA active");
    } catch (error) {
      toast.error(error?.response?.data?.detail || "Code 2FA invalide");
    } finally {
      setLoading((prev) => ({ ...prev, enable2fa: false }));
    }
  };

  const handleDisable2fa = async () => {
    setLoading((prev) => ({ ...prev, disable2fa: true }));
    try {
      await disableTwoFactor(twoFactorCode.trim());
      setTwoFactorCode("");
      await refreshUser();
      toast.success("2FA desactive");
    } catch (error) {
      toast.error(error?.response?.data?.detail || "Code 2FA invalide");
    } finally {
      setLoading((prev) => ({ ...prev, disable2fa: false }));
    }
  };

  const refreshSessions = async () => {
    setLoading((prev) => ({ ...prev, sessions: true }));
    try {
      const data = await listSessions();
      setSessions(data || []);
    } catch {
      // ignore
    } finally {
      setLoading((prev) => ({ ...prev, sessions: false }));
    }
  };

  const handleRevokeSession = async (sessionId) => {
    try {
      await revokeSession(sessionId);
      toast.success("Session revoquee");
      await refreshSessions();
    } catch (error) {
      toast.error(error?.response?.data?.detail || "Impossible de revoquer la session");
    }
  };

  const handleExportGdpr = async () => {
    try {
      const response = await api.get("/gdpr/export", { responseType: "blob" });
      const blobUrl = URL.createObjectURL(response.data);
      const anchor = document.createElement("a");
      anchor.href = blobUrl;
      anchor.download = "clipai_export.zip";
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      URL.revokeObjectURL(blobUrl);
      toast.success("Export RGPD telecharge");
    } catch (error) {
      toast.error(error?.response?.data?.detail || "Echec export RGPD");
    }
  };

  const handleDeleteAccount = async () => {
    if (!deletePassword.trim()) {
      toast.error("Mot de passe requis");
      return;
    }
    try {
      await api.delete("/gdpr/delete-account", { data: { password: deletePassword } });
      toast.success("Compte anonymise");
      await logout();
      navigate("/");
    } catch (error) {
      toast.error(error?.response?.data?.detail || "Suppression impossible");
    }
  };

  return (
    <section className="page">
      <article className="ui-card">
        <p className="caption">PROFILE</p>
        <h2 className="section-title" style={{ fontSize: "2rem" }}>Mon compte</h2>
        <p className="muted">{user?.email}</p>
      </article>

      <article className="ui-card">
        <h3>Informations personnelles</h3>
        <form className="form-col" onSubmit={handleProfileUpdate} style={{ marginTop: 12 }}>
          <label>
            <span className="muted">Nom complet</span>
            <input
              className="ui-input"
              value={profileForm.full_name}
              onChange={(event) => setProfileForm((prev) => ({ ...prev, full_name: event.target.value }))}
            />
          </label>
          <label>
            <span className="muted">Avatar URL</span>
            <input
              className="ui-input"
              value={profileForm.avatar_url}
              onChange={(event) => setProfileForm((prev) => ({ ...prev, avatar_url: event.target.value }))}
            />
          </label>
          <label>
            <span className="muted">Bio</span>
            <textarea
              className="ui-input"
              value={profileForm.bio}
              onChange={(event) => setProfileForm((prev) => ({ ...prev, bio: event.target.value }))}
              rows={3}
            />
          </label>
          <label>
            <span className="muted">Lien YouTube</span>
            <input
              className="ui-input"
              value={profileForm.youtube_url}
              onChange={(event) => setProfileForm((prev) => ({ ...prev, youtube_url: event.target.value }))}
            />
          </label>
          <button type="submit" className="ui-btn ui-btn-primary" disabled={loading.profile}>
            {loading.profile ? "Sauvegarde..." : "Sauvegarder"}
          </button>
        </form>
      </article>

      <article className="ui-card">
        <h3>Securite</h3>
        <form className="form-col" onSubmit={handlePasswordChange} style={{ marginTop: 12 }}>
          <label>
            <span className="muted">Mot de passe actuel</span>
            <input
              className="ui-input"
              type="password"
              value={passwordForm.current_password}
              onChange={(event) => setPasswordForm((prev) => ({ ...prev, current_password: event.target.value }))}
            />
          </label>
          <label>
            <span className="muted">Nouveau mot de passe</span>
            <input
              className="ui-input"
              type="password"
              value={passwordForm.new_password}
              onChange={(event) => setPasswordForm((prev) => ({ ...prev, new_password: event.target.value }))}
            />
          </label>
          <button type="submit" className="ui-btn ui-btn-secondary" disabled={loading.password}>
            {loading.password ? "Mise a jour..." : "Changer le mot de passe"}
          </button>
        </form>

        <div className="ui-card" style={{ marginTop: 12 }}>
          <p className="caption">2FA</p>
          <p className="muted">Etat: {user?.two_factor_enabled ? "Active" : "Inactive"}</p>
          {!user?.two_factor_enabled ? (
            <button type="button" className="ui-btn ui-btn-primary" onClick={handleSetup2fa} disabled={loading.setup2fa}>
              {loading.setup2fa ? "Generation..." : "Activer le 2FA"}
            </button>
          ) : null}
          {user?.two_factor_enabled ? (
            <div className="inline-actions" style={{ marginTop: 10 }}>
              <input
                className="ui-input"
                style={{ maxWidth: 160 }}
                placeholder="Code 2FA"
                value={twoFactorCode}
                onChange={(event) => setTwoFactorCode(event.target.value)}
              />
              <button type="button" className="ui-btn ui-btn-secondary" onClick={handleDisable2fa} disabled={loading.disable2fa}>
                Desactiver
              </button>
            </div>
          ) : null}
          {twoFactorSetup ? (
            <div style={{ marginTop: 12 }}>
              <p className="muted">Scanne ce QR Code puis confirme avec ton code a 6 chiffres.</p>
              <img src={twoFactorSetup.qr_code_base64} alt="QR Code 2FA" style={{ width: 180, borderRadius: 12, marginTop: 8 }} />
              <div className="inline-actions" style={{ marginTop: 10 }}>
                <input
                  className="ui-input"
                  style={{ maxWidth: 160 }}
                  placeholder="Code 2FA"
                  value={twoFactorCode}
                  onChange={(event) => setTwoFactorCode(event.target.value)}
                />
                <button type="button" className="ui-btn ui-btn-primary" onClick={handleEnable2fa} disabled={loading.enable2fa}>
                  Confirmer
                </button>
              </div>
            </div>
          ) : null}
        </div>
      </article>

      <article className="ui-card">
        <h3>Preferences</h3>
        <form className="grid grid-2" style={{ marginTop: 12 }} onSubmit={handlePreferencesUpdate}>
          <label>
            <span className="muted">Langue</span>
            <select className="ui-input" value={preferences.language} onChange={(event) => setPreferences((prev) => ({ ...prev, language: event.target.value }))}>
              <option value="fr">Francais</option>
              <option value="en">English</option>
            </select>
          </label>
          <label>
            <span className="muted">Fuseau</span>
            <input className="ui-input" value={preferences.timezone} onChange={(event) => setPreferences((prev) => ({ ...prev, timezone: event.target.value }))} />
          </label>
          <label>
            <span className="muted">Format prefere</span>
            <select className="ui-input" value={preferences.preferred_format} onChange={(event) => setPreferences((prev) => ({ ...prev, preferred_format: event.target.value }))}>
              <option value="all">Tous</option>
              <option value="tiktok">TikTok</option>
              <option value="reels">Reels</option>
              <option value="shorts">Shorts</option>
            </select>
          </label>
          <label>
            <span className="muted">Qualite</span>
            <select className="ui-input" value={preferences.preferred_quality} onChange={(event) => setPreferences((prev) => ({ ...prev, preferred_quality: event.target.value }))}>
              <option value="720p">720p</option>
              <option value="1080p">1080p</option>
            </select>
          </label>
          <label style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <input
              type="checkbox"
              checked={Boolean(preferences.subtitles_default)}
              onChange={(event) => setPreferences((prev) => ({ ...prev, subtitles_default: event.target.checked }))}
            />
            <span className="muted">Sous-titres auto par defaut</span>
          </label>
          <div>
            <button type="submit" className="ui-btn ui-btn-primary" disabled={loading.preferences}>
              {loading.preferences ? "Sauvegarde..." : "Sauvegarder les preferences"}
            </button>
          </div>
        </form>
      </article>

      <article className="ui-card">
        <h3>Sessions actives</h3>
        <div className="inline-actions" style={{ justifyContent: "space-between", marginTop: 12 }}>
          <p className="muted">{sessions.length} session(s)</p>
          <button type="button" className="ui-btn ui-btn-secondary" onClick={() => void refreshSessions()} disabled={loading.sessions}>
            Rafraichir
          </button>
        </div>
        <div className="grid" style={{ marginTop: 12 }}>
          {sessions.map((session) => (
            <div key={session.id} className="ui-card" style={{ padding: 12 }}>
              <p style={{ fontWeight: 600 }}>{session.country} • {session.ip_address}</p>
              <p className="muted" style={{ fontSize: 13 }}>{session.user_agent}</p>
              <p className="muted" style={{ fontSize: 13 }}>Derniere utilisation: {session.last_used_at}</p>
              <button type="button" className="ui-btn ui-btn-secondary" onClick={() => void handleRevokeSession(session.id)}>
                Revoquer
              </button>
            </div>
          ))}
          {!sessions.length ? <p className="muted">Aucune session active.</p> : null}
        </div>
      </article>

      <article className="ui-card">
        <h3>Abonnement</h3>
        <p className="muted">Plan actuel: {user?.plan || "free"}</p>
        <div className="inline-actions" style={{ marginTop: 10 }}>
          <button type="button" className="ui-btn ui-btn-secondary" onClick={() => navigate("/pricing")}>
            Changer de plan
          </button>
          {billingUrl ? (
            <button type="button" className="ui-btn ui-btn-primary" onClick={() => window.open(billingUrl, "_blank", "noopener,noreferrer")}>
              Ouvrir le portail facturation
            </button>
          ) : null}
        </div>
      </article>

      <article className="ui-card">
        <h3>RGPD</h3>
        <div className="inline-actions" style={{ marginTop: 10 }}>
          <button type="button" className="ui-btn ui-btn-secondary" onClick={handleExportGdpr}>
            Exporter mes donnees
          </button>
        </div>
        <div style={{ marginTop: 12 }}>
          <label>
            <span className="muted">Confirmer mot de passe pour suppression</span>
            <input
              className="ui-input"
              type="password"
              value={deletePassword}
              onChange={(event) => setDeletePassword(event.target.value)}
            />
          </label>
          <button type="button" className="ui-btn ui-btn-secondary" onClick={handleDeleteAccount} style={{ marginTop: 10 }}>
            Supprimer mon compte
          </button>
        </div>
      </article>
    </section>
  );
}

export default Profile;
