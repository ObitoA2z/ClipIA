import { useEffect, useMemo, useRef, useState } from "react";
import { motion } from "framer-motion";
import { Link } from "react-router-dom";

import Badge from "../components/ui/Badge";
import Button from "../components/ui/Button";
import Card from "../components/ui/Card";

const features = [
  { title: "Découpe intelligente", text: "Détection automatique des passages viraux avec IA.", accent: "#6366F1", icon: "✂️" },
  { title: "Format 9:16 natif", text: "Export vertical optimisé TikTok, Reels et Shorts.", accent: "#8B5CF6", icon: "📱" },
  { title: "Sous-titres prêts", text: "Sous-titres auto synchronisés avec hook en ouverture.", accent: "#EC4899", icon: "📝" },
  { title: "Batch rapide", text: "10 clips générés en quelques minutes.", accent: "#F59E0B", icon: "⚡" },
  { title: "Qualité studio", text: "Compression propre et rendu HD 1080x1920.", accent: "#10B981", icon: "🎬" },
  { title: "Export cloud", text: "Liens de téléchargement instantanés et partage équipe.", accent: "#3B82F6", icon: "☁️" },
];

const testimonials = [
  { name: "Camille R.", role: "YouTubeuse Tech", quote: "ClipAI m'a fait gagner 6h par semaine.", stars: "★★★★★" },
  { name: "Nassim D.", role: "Coach Business", quote: "Le pipeline est ultra rapide et propre.", stars: "★★★★★" },
  { name: "Lina M.", role: "Créatrice Lifestyle", quote: "Je publie 3x plus sans équipe de montage.", stars: "★★★★★" },
];

const steps = [
  { title: "Colle ton lien", text: "Ajoute l'URL YouTube de ta vidéo longue.", number: "01" },
  { title: "Analyse IA", text: "ClipAI transcrit et sélectionne les meilleurs moments.", number: "02" },
  { title: "Publie", text: "Télécharge des clips verticaux prêts à poster.", number: "03" },
];

function Home() {
  const canvasRef = useRef(null);
  const [creatorCount, setCreatorCount] = useState(0);
  const [yearly, setYearly] = useState(false);

  useEffect(() => {
    let animationFrame = 0;
    const canvas = canvasRef.current;
    if (!canvas) {
      return;
    }

    const ctx = canvas.getContext("2d");
    const particles = Array.from({ length: 45 }, () => ({
      x: Math.random(),
      y: Math.random(),
      vx: (Math.random() - 0.5) * 0.0015,
      vy: (Math.random() - 0.5) * 0.0015,
      r: Math.random() * 2 + 0.5,
    }));

    const render = () => {
      const { width, height } = canvas.getBoundingClientRect();
      canvas.width = width;
      canvas.height = height;

      if (!ctx) {
        return;
      }

      ctx.clearRect(0, 0, width, height);
      particles.forEach((p) => {
        p.x += p.vx;
        p.y += p.vy;

        if (p.x <= 0 || p.x >= 1) {
          p.vx *= -1;
        }
        if (p.y <= 0 || p.y >= 1) {
          p.vy *= -1;
        }

        ctx.beginPath();
        ctx.arc(p.x * width, p.y * height, p.r, 0, Math.PI * 2);
        ctx.fillStyle = "rgba(129,140,248,0.6)";
        ctx.fill();
      });

      animationFrame = requestAnimationFrame(render);
    };

    render();
    return () => cancelAnimationFrame(animationFrame);
  }, []);

  useEffect(() => {
    const target = 2847;
    const start = Date.now();
    const duration = 1200;

    const timer = window.setInterval(() => {
      const elapsed = Date.now() - start;
      const progress = Math.min(1, elapsed / duration);
      setCreatorCount(Math.floor(target * progress));
      if (progress >= 1) {
        clearInterval(timer);
      }
    }, 16);

    return () => clearInterval(timer);
  }, []);

  const pricing = useMemo(() => {
    const factor = yearly ? 10 : 1;
    return {
      free: 0,
      pro: 19 * factor,
      business: 49 * factor,
      suffix: yearly ? "/an" : "/mois",
    };
  }, [yearly]);

  return (
    <div className="page">
      <section className="ui-card" style={{ position: "relative", overflow: "hidden", minHeight: 500 }}>
        <canvas ref={canvasRef} style={{ position: "absolute", inset: 0, opacity: 0.75 }} />
        <div style={{ position: "relative", zIndex: 1, display: "grid", gap: 22 }}>
          <Badge variant="primary">✨ Nouveau — Génération en 2 minutes</Badge>
          <h1 className="section-title gradient-text">Transforme tes vidéos en Shorts viraux</h1>
          <p className="muted" style={{ maxWidth: 700 }}>
            L'IA analyse, découpe et formate automatiquement tes contenus YouTube en clips verticaux prêts à publier.
          </p>
          <div className="inline-actions">
            <Link to="/register">
              <Button variant="accent">Essayer gratuitement</Button>
            </Link>
            <Link to="/pricing">
              <Button variant="secondary">Voir la démo ▶</Button>
            </Link>
          </div>
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}>
            <p className="caption">{creatorCount.toLocaleString("fr-FR")} créateurs font confiance à ClipAI</p>
          </motion.div>
          <div className="ui-card" style={{ transform: "perspective(1000px) rotateX(4deg)", background: "rgba(18,18,42,0.9)" }}>
            <div className="grid grid-3">
              <div>
                <p className="caption">Input</p>
                <p>https://youtube.com/watch?v=clipai</p>
              </div>
              <div>
                <p className="caption">Détection IA</p>
                <p>8 extraits identifiés</p>
              </div>
              <div>
                <p className="caption">Export</p>
                <p>MP4 1080x1920 • prêt à poster</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="grid grid-3">
        {steps.map((step, index) => (
          <motion.div
            key={step.title}
            initial={{ opacity: 0, y: 18 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: index * 0.12 }}
          >
            <Card>
              <p className="gradient-text" style={{ fontSize: 40, fontWeight: 800, lineHeight: 1 }}>
                {step.number}
              </p>
              <h3 style={{ marginTop: 10 }}>{step.title}</h3>
              <p className="muted">{step.text}</p>
            </Card>
          </motion.div>
        ))}
      </section>

      <section className="grid grid-3">
        {features.map((feature, index) => (
          <motion.div
            key={feature.title}
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: index * 0.08 }}
          >
            <Card style={{ borderColor: `${feature.accent}66` }}>
              <div style={{ fontSize: 26 }}>{feature.icon}</div>
              <h3 style={{ marginTop: 6 }}>{feature.title}</h3>
              <p className="muted">{feature.text}</p>
            </Card>
          </motion.div>
        ))}
      </section>

      <section className="ui-card">
        <div className="inline-actions" style={{ justifyContent: "space-between", alignItems: "center" }}>
          <h2 className="section-title" style={{ fontSize: "clamp(1.7rem,4vw,2.6rem)" }}>
            Tarifs transparents
          </h2>
          <button
            type="button"
            className="ui-btn ui-btn-secondary"
            onClick={() => setYearly((value) => !value)}
          >
            {yearly ? "Annuel actif" : "Mensuel actif"}
          </button>
        </div>

        <div className="grid grid-3" style={{ marginTop: 16 }}>
          <Card>
            <Badge variant="primary">Free</Badge>
            <h3 style={{ marginTop: 8 }}>{pricing.free}€{pricing.suffix}</h3>
            <p className="muted">3 vidéos/mois</p>
          </Card>

          <Card style={{ borderColor: "var(--accent)", animation: "glowPulse 2.4s ease infinite" }}>
            <Badge variant="success">Le plus populaire</Badge>
            <h3 style={{ marginTop: 8 }}>{pricing.pro}€{pricing.suffix}</h3>
            <p className="muted">Vidéos illimitées + mode équipe</p>
          </Card>

          <Card>
            <Badge variant="primary">Business</Badge>
            <h3 style={{ marginTop: 8 }}>{pricing.business}€{pricing.suffix}</h3>
            <p className="muted">API + branding white-label</p>
          </Card>
        </div>
      </section>

      <section className="ui-card" style={{ overflow: "hidden" }}>
        <h2 style={{ marginBottom: 12 }}>Ce que disent les créateurs</h2>
        <div className="grid grid-3">
          {testimonials.map((item) => (
            <Card key={item.name}>
              <p style={{ color: "#fbbf24" }}>{item.stars}</p>
              <p style={{ marginTop: 8 }}>&ldquo;{item.quote}&rdquo;</p>
              <p className="muted" style={{ marginTop: 10 }}>
                {item.name} • {item.role}
              </p>
            </Card>
          ))}
        </div>
      </section>

      <section className="ui-card" style={{ background: "var(--gradient-primary)", color: "#fff" }}>
        <h2 className="section-title" style={{ fontSize: "clamp(1.8rem,4vw,2.8rem)", marginBottom: 10 }}>
          Lance ta machine à clips maintenant
        </h2>
        <p style={{ marginBottom: 14 }}>Commence gratuitement et publie dès aujourd'hui.</p>
        <Link to="/register">
          <Button variant="secondary">Créer mon compte</Button>
        </Link>
      </section>
    </div>
  );
}

export default Home;
