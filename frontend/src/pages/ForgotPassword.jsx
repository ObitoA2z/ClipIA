import { useState } from "react";
import { Link } from "react-router-dom";
import toast from "react-hot-toast";

import Card from "../components/ui/Card";
import Button from "../components/ui/Button";
import Input from "../components/ui/Input";
import { forgotPassword } from "../services/authService";

function ForgotPassword() {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setLoading(true);
    try {
      const data = await forgotPassword(email);
      toast.success(data?.message || "Email envoye si le compte existe");
    } catch (error) {
      toast.error(error?.response?.data?.detail || "Erreur de demande de reset");
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="auth-shell">
      <Card className="auth-card">
        <h2 className="section-title" style={{ fontSize: "2rem" }}>Mot de passe oublie</h2>
        <p className="muted" style={{ marginBottom: 14 }}>
          Saisis ton email pour recevoir un lien de reinitialisation.
        </p>
        <form className="form-col" onSubmit={handleSubmit}>
          <Input
            id="forgot-email"
            label="Email"
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            placeholder="ton@email.com"
            required
          />
          <Button type="submit" variant="primary" loading={loading}>
            Envoyer le lien
          </Button>
        </form>
        <p className="muted" style={{ marginTop: 12 }}>
          Retour a <Link to="/login" className="gradient-text">Connexion</Link>
        </p>
      </Card>
    </section>
  );
}

export default ForgotPassword;
