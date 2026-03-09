import { useMemo, useState } from "react";
import toast from "react-hot-toast";

import Card from "../components/ui/Card";
import Button from "../components/ui/Button";
import Badge from "../components/ui/Badge";
import useSubscription from "../hooks/useSubscription";
import { createCheckout } from "../services/paymentService";

const planFeatures = {
  free: ["3 videos/mois", "Clips 720p", "Sans watermark", "Support communaute"],
  pro: ["Illimite", "1080p", "Scheduler", "AI Thumbnails", "AI Coach", "Support chat"],
  business: ["Tout Pro", "API", "Equipe 5 membres", "4K", "Dubbing", "Support prioritaire"],
};

function Pricing() {
  const subscription = useSubscription();
  const [yearly, setYearly] = useState(false);
  const [loadingPlan, setLoadingPlan] = useState("");

  const pricing = useMemo(() => {
    if (!yearly) {
      return { pro: 19, business: 49, suffix: "/mois", savings: 0 };
    }
    return {
      pro: 190,
      business: 490,
      suffix: "/an",
      savings: 38,
    };
  }, [yearly]);

  const handleCheckout = async (plan) => {
    setLoadingPlan(plan);
    try {
      const result = await createCheckout(plan);
      if (result?.checkout_url) {
        window.location.href = result.checkout_url;
        return;
      }
      toast.success("Checkout cree");
    } catch (error) {
      toast.error(error?.response?.data?.detail || "Impossible de creer le checkout");
    } finally {
      setLoadingPlan("");
    }
  };

  return (
    <section className="page">
      <Card>
        <h2 className="section-title" style={{ fontSize: "2.2rem" }}>Tarifs</h2>
        <p className="muted" style={{ marginBottom: 10 }}>
          Statut actuel: {subscription.data?.status || "..."} • plan {subscription.data?.plan || "..."}
        </p>
        <div className="inline-actions">
          <Button variant={yearly ? "secondary" : "primary"} onClick={() => setYearly(false)}>
            Mensuel
          </Button>
          <Button variant={yearly ? "primary" : "secondary"} onClick={() => setYearly(true)}>
            Annuel
          </Button>
          {yearly ? (
            <span className="score-badge score-good">Economisez {pricing.savings}€/an</span>
          ) : null}
        </div>
      </Card>

      <div className="grid grid-3">
        <Card>
          <Badge variant="primary">Free</Badge>
          <h3 style={{ marginTop: 8 }}>0€/{yearly ? "an" : "mois"}</h3>
          <ul className="plan-list">
            {planFeatures.free.map((feature) => (
              <li key={feature}>✅ {feature}</li>
            ))}
          </ul>
          <Button variant="secondary" disabled>
            Plan actuel
          </Button>
        </Card>

        <Card style={{ borderColor: "var(--accent)", animation: "glowPulse 2.5s ease infinite" }}>
          <Badge variant="success">Le plus populaire</Badge>
          <h3 style={{ marginTop: 8 }}>{pricing.pro}€{pricing.suffix}</h3>
          <ul className="plan-list">
            {planFeatures.pro.map((feature) => (
              <li key={feature}>✅ {feature}</li>
            ))}
          </ul>
          <Button variant="accent" onClick={() => void handleCheckout("pro")} loading={loadingPlan === "pro"}>
            Choisir Pro
          </Button>
        </Card>

        <Card>
          <Badge variant="primary">Business</Badge>
          <h3 style={{ marginTop: 8 }}>{pricing.business}€{pricing.suffix}</h3>
          <ul className="plan-list">
            {planFeatures.business.map((feature) => (
              <li key={feature}>✅ {feature}</li>
            ))}
          </ul>
          <Button variant="primary" onClick={() => void handleCheckout("business")} loading={loadingPlan === "business"}>
            Choisir Business
          </Button>
        </Card>
      </div>

      <Card>
        <h3>FAQ rapide</h3>
        <div style={{ display: "grid", gap: 10, marginTop: 10 }}>
          <details className="faq-item">
            <summary>Puis-je annuler a tout moment ?</summary>
            <p className="muted">Oui, annulation instantanee depuis ton profil.</p>
          </details>
          <details className="faq-item">
            <summary>Y a-t-il un engagement ?</summary>
            <p className="muted">Non, abonnement mensuel/annuel sans engagement.</p>
          </details>
          <details className="faq-item">
            <summary>Les plans incluent-ils les mises a jour ?</summary>
            <p className="muted">Oui, toutes les nouvelles features sont incluses.</p>
          </details>
          <details className="faq-item">
            <summary>Le plan Free a-t-il un watermark ?</summary>
            <p className="muted">Non, aucun watermark sur ClipAI.</p>
          </details>
        </div>
      </Card>
    </section>
  );
}

export default Pricing;
