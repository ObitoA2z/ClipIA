import { useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import toast from "react-hot-toast";

import Card from "../components/ui/Card";
import Button from "../components/ui/Button";
import Input from "../components/ui/Input";
import { resetPassword } from "../services/authService";

function ResetPassword() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token") || "";
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!token) {
      toast.error("Token manquant dans l'URL");
      return;
    }
    if (password !== confirmPassword) {
      toast.error("Les mots de passe ne correspondent pas");
      return;
    }

    setLoading(true);
    try {
      const data = await resetPassword(token, password);
      toast.success(data?.message || "Mot de passe mis a jour");
    } catch (error) {
      toast.error(error?.response?.data?.detail || "Reset impossible");
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="auth-shell">
      <Card className="auth-card">
        <h2 className="section-title" style={{ fontSize: "2rem" }}>Reinitialiser le mot de passe</h2>
        <p className="muted" style={{ marginBottom: 14 }}>
          Choisis un nouveau mot de passe securise.
        </p>
        <form className="form-col" onSubmit={handleSubmit}>
          <Input
            id="reset-password"
            label="Nouveau mot de passe"
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            required
          />
          <Input
            id="reset-password-confirm"
            label="Confirmer le mot de passe"
            type="password"
            value={confirmPassword}
            onChange={(event) => setConfirmPassword(event.target.value)}
            required
          />
          <Button type="submit" variant="primary" loading={loading}>
            Mettre a jour
          </Button>
        </form>
        <p className="muted" style={{ marginTop: 12 }}>
          Retour a <Link to="/login" className="gradient-text">Connexion</Link>
        </p>
      </Card>
    </section>
  );
}

export default ResetPassword;
