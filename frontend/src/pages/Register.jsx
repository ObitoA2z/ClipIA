import { useMemo, useState } from "react";
import { motion } from "framer-motion";
import { Link, useNavigate } from "react-router-dom";
import toast from "react-hot-toast";

import useAuth from "../hooks/useAuth";
import Button from "../components/ui/Button";
import Card from "../components/ui/Card";
import Input from "../components/ui/Input";

const API_BASE = import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

function getPasswordChecks(password) {
  return {
    length: password.length >= 8,
    uppercase: /[A-Z]/.test(password),
    digit: /\d/.test(password),
    special: /[^A-Za-z0-9]/.test(password),
  };
}

function Register() {
  const { register } = useAuth();
  const navigate = useNavigate();

  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const checks = useMemo(() => getPasswordChecks(password), [password]);
  const strength = Object.values(checks).filter(Boolean).length;
  const strengthPercent = (strength / 4) * 100;

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError("");
    setIsLoading(true);
    try {
      await register({ full_name: fullName, email, password });
      toast.success("Compte cree avec succes");
      navigate("/dashboard", { replace: true });
    } catch (err) {
      const message = err?.response?.data?.detail || "Inscription impossible";
      setError(message);
      toast.error(message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <section className="auth-shell">
      <Card className="auth-card">
        <h2 className="section-title" style={{ fontSize: "2rem" }}>
          Cree ton compte
        </h2>
        <p className="muted" style={{ marginBottom: 16 }}>
          Lance ton premier traitement en moins de 2 minutes.
        </p>

        {error ? (
          <motion.p initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }} className="error-text" style={{ marginBottom: 10 }}>
            {error}
          </motion.p>
        ) : null}

        <div className="grid grid-2" style={{ marginBottom: 12 }}>
          <button type="button" className="ui-btn ui-btn-secondary" onClick={() => { window.location.href = `${API_BASE}/auth/google`; }}>
            Continuer avec Google
          </button>
          <button type="button" className="ui-btn ui-btn-secondary" onClick={() => { window.location.href = `${API_BASE}/auth/github`; }}>
            Continuer avec GitHub
          </button>
        </div>

        <form className="form-col" onSubmit={handleSubmit}>
          <Input
            id="full_name"
            label="Nom complet"
            value={fullName}
            onChange={(event) => setFullName(event.target.value)}
            placeholder="Rayane Example"
            required
          />

          <Input
            id="email"
            label="Email"
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            placeholder="ton@email.com"
            required
          />

          <Input
            id="password"
            label="Mot de passe"
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            placeholder="Minimum 8 caracteres"
            required
          />

          <div>
            <div className="progress-track">
              <div className="progress-bar" style={{ width: `${strengthPercent}%` }} />
            </div>
            <p className="muted" style={{ marginTop: 8, fontSize: 13 }}>
              Force: {strength}/4 • 8+ caracteres, 1 majuscule, 1 chiffre, 1 special.
            </p>
          </div>

          <Button type="submit" variant="primary" loading={isLoading}>
            {isLoading ? "Creation en cours" : "Creer mon compte"}
          </Button>
        </form>

        <p className="muted" style={{ marginTop: 14 }}>
          Deja inscrit ? <Link to="/login" className="gradient-text">Se connecter</Link>
        </p>
      </Card>
    </section>
  );
}

export default Register;
