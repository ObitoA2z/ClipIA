import { useState } from "react";
import { motion } from "framer-motion";
import { Link, useLocation, useNavigate } from "react-router-dom";
import toast from "react-hot-toast";

import useAuth from "../hooks/useAuth";
import Button from "../components/ui/Button";
import Card from "../components/ui/Card";
import Input from "../components/ui/Input";

function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const from = location.state?.from || "/dashboard";

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError("");
    setIsLoading(true);

    try {
      await login({ email, password });
      toast.success("Connexion réussie");
      navigate(from, { replace: true });
    } catch (err) {
      const message = err?.response?.data?.detail || "Connexion impossible";
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
          Connexion
        </h2>
        <p className="muted" style={{ marginBottom: 16 }}>
          Reprends ton workflow en moins de 30 secondes.
        </p>

        {error ? (
          <motion.p
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            className="error-text"
            style={{ marginBottom: 10 }}
          >
            {error}
          </motion.p>
        ) : null}

        <form className="form-col" onSubmit={handleSubmit}>
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
            placeholder="••••••••"
            required
          />

          <Button type="submit" variant="primary" loading={isLoading}>
            {isLoading ? "Connexion en cours" : "Se connecter"}
          </Button>
        </form>

        <p className="muted" style={{ marginTop: 14 }}>
          Pas de compte ? <Link to="/register" className="gradient-text">Créer un compte</Link>
        </p>
      </Card>
    </section>
  );
}

export default Login;
