import { useState } from "react";
import { motion } from "framer-motion";
import { Link, useNavigate } from "react-router-dom";
import toast from "react-hot-toast";

import useAuth from "../hooks/useAuth";
import Button from "../components/ui/Button";
import Card from "../components/ui/Card";
import Input from "../components/ui/Input";

function Register() {
  const { register } = useAuth();
  const navigate = useNavigate();

  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError("");
    setIsLoading(true);

    try {
      await register({ full_name: fullName, email, password });
      toast.success("Compte créé avec succès");
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
          Crée ton compte
        </h2>
        <p className="muted" style={{ marginBottom: 16 }}>
          Lance ton premier traitement en moins de 2 minutes.
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
            placeholder="Minimum 6 caractères"
            required
          />

          <Button type="submit" variant="primary" loading={isLoading}>
            {isLoading ? "Création en cours" : "Créer mon compte"}
          </Button>
        </form>

        <p className="muted" style={{ marginTop: 14 }}>
          Déjà inscrit ? <Link to="/login" className="gradient-text">Se connecter</Link>
        </p>
      </Card>
    </section>
  );
}

export default Register;
