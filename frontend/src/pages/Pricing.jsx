import { useState } from "react";
import toast from "react-hot-toast";

import Card from "../components/ui/Card";
import Button from "../components/ui/Button";
import Badge from "../components/ui/Badge";
import useSubscription from "../hooks/useSubscription";
import { createCheckout } from "../services/paymentService";

function Pricing() {
  const subscription = useSubscription();
  const [yearly, setYearly] = useState(false);

  const handleCheckout = async (plan) => {
    try {
      const result = await createCheckout(plan);
      toast.success(`Checkout créé: ${result.checkout_url}`);
    } catch (error) {
      toast.error(error?.response?.data?.detail || "Impossible de créer le checkout");
    }
  };

  const multiplier = yearly ? 10 : 1;

  return (
    <section className="page">
      <Card>
        <h2 className="section-title" style={{ fontSize: "2.2rem" }}>Tarifs</h2>
        <p className="muted" style={{ marginBottom: 10 }}>
          Statut actuel: {subscription.data?.status || "..."} • plan {subscription.data?.plan || "..."}
        </p>
        <Button variant="secondary" onClick={() => setYearly((value) => !value)}>
          {yearly ? "Affichage Annuel" : "Affichage Mensuel"}
        </Button>
      </Card>

      <div className="grid grid-3">
        <Card>
          <Badge variant="primary">Free</Badge>
          <h3 style={{ marginTop: 8 }}>0€/{yearly ? "an" : "mois"}</h3>
          <p className="muted">3 vidéos par mois pour démarrer.</p>
          <Button variant="secondary" disabled>
            Plan actuel
          </Button>
        </Card>

        <Card style={{ borderColor: "var(--accent)", animation: "glowPulse 2.5s ease infinite" }}>
          <Badge variant="success">Le plus populaire</Badge>
          <h3 style={{ marginTop: 8 }}>{19 * multiplier}€/{yearly ? "an" : "mois"}</h3>
          <p className="muted">Vidéos illimitées, traitement prioritaire.</p>
          <Button variant="accent" onClick={() => handleCheckout("pro")}>
            Choisir Pro
          </Button>
        </Card>

        <Card>
          <Badge variant="primary">Business</Badge>
          <h3 style={{ marginTop: 8 }}>{49 * multiplier}€/{yearly ? "an" : "mois"}</h3>
          <p className="muted">Mode équipe, exports avancés et support dédié.</p>
          <Button variant="primary" onClick={() => handleCheckout("business")}>
            Choisir Business
          </Button>
        </Card>
      </div>
    </section>
  );
}

export default Pricing;
