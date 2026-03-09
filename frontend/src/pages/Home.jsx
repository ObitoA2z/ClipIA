import { useEffect, useMemo, useRef, useState } from "react";
import { motion } from "framer-motion";
import { Link } from "react-router-dom";

import api from "../services/api";
import Badge from "../components/ui/Badge";
import Button from "../components/ui/Button";
import Card from "../components/ui/Card";

const features = [
  { title: "Decoupe intelligente", text: "Detection automatique des passages viraux avec IA.", accent: "#6366F1", icon: "✂️" },
  { title: "Format 9:16 natif", text: "Export vertical optimise TikTok, Reels et Shorts.", accent: "#8B5CF6", icon: "📱" },
  { title: "Sous-titres prets", text: "Sous-titres auto synchronises avec hook en ouverture.", accent: "#EC4899", icon: "📝" },
  { title: "Batch rapide", text: "10 clips generes en quelques minutes.", accent: "#F59E0B", icon: "⚡" },
  { title: "Qualite studio", text: "Compression propre et rendu HD 1080x1920.", accent: "#10B981", icon: "🎬" },
  { title: "Export cloud", text: "Liens de telechargement instantanes et partage equipe.", accent: "#3B82F6", icon: "☁️" },
];

const testimonials = [
  { name: "Camille R.", role: "YouTubeuse Tech", quote: "ClipAI m'a fait gagner 6h par semaine.", stars: "★★★★★" },
  { name: "Nassim D.", role: "Coach Business", quote: "Le pipeline est ultra rapide et propre.", stars: "★★★★★" },
  { name: "Lina M.", role: "Creatrice Lifestyle", quote: "Je publie 3x plus sans equipe de montage.", stars: "★★★★★" },
];

const steps = [
  { title: "Colle ton lien", text: "Ajoute l'URL YouTube de ta video longue.", number: "01" },
  { title: "Analyse IA", text: "ClipAI transcrit et selectionne les meilleurs moments.", number: "02" },
  { title: "Publie", text: "Telecharge des clips verticaux prets a poster.", number: "03" },
];

const faqItems = [
  { q: "ClipAI fonctionne avec quelles plateformes ?", a: "TikTok, Instagram Reels, YouTube Shorts et formats 1:1." },
  { q: "Est-ce que je peux tester gratuitement ?", a: "Oui, 3 videos par mois sur le plan Free." },
  { q: "Combien de clips genere l'IA par video ?", a: "Par defaut 5 a 10 clips, ajustable dans les options avancees." },
  { q: "Quelle est la longueur maximale de video ?", a: "Jusqu'a plusieurs heures selon ton plan et la source." },
  { q: "Les clips ont-ils un watermark sur le plan gratuit ?", a: "Non, pas de watermark meme en Free." },
  { q: "Puis-je annuler a tout moment ?", a: "Oui, annulation en un clic depuis ton profil." },
  { q: "Y a-t-il un systeme de credits ?", a: "Non, ClipAI reste simple avec des limites de plan claires." },
  { q: "Comment fonctionne l'IA ?", a: "Transcription + detection des moments forts + rendu vertical automatique." },
];

const logos = ["ProductHunt", "YouTube", "TikTok", "Instagram", "LinkedIn", "Notion", "Zapier"];

function Home() {
  const canvasRef = useRef(null);
  const [creatorCount, setCreatorCount] = useState(0);
  const [yearly, setYearly] = useState(false);
  const [stats, setStats] = useState({
    clips_today: 847,
    total_creators: 2847,
    clips_total: 124000,
  });

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
      particles.forEach((particle) => {
        particle.x += particle.vx;
        particle.y += particle.vy;
        if (particle.x <= 0 || particle.x >= 1) {
          particle.vx *= -1;
        }
        if (particle.y <= 0 || particle.y >= 1) {
          particle.vy *= -1;
        }
        ctx.beginPath();
        ctx.arc(particle.x * width, particle.y * height, particle.r, 0, Math.PI * 2);
        ctx.fillStyle = "rgba(129,140,248,0.6)";
        ctx.fill();
      });
      animationFrame = requestAnimationFrame(render);
    };

    render();
    return () => cancelAnimationFrame(animationFrame);
  }, []);

  useEffect(() => {
    let cancelled = false;
    async function loadStats() {
      try {
        const { data } = await api.get("/stats/public");
        if (!cancelled && data) {
          setStats((current) => ({ ...current, ...data }));
        }
      } catch {
        // silent fallback with default values
      }
    }

    void loadStats();
    const timer = window.setInterval(() => {
      void loadStats();
    }, 60000);
    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, []);

  useEffect(() => {
    const target = Number(stats.total_creators || 0);
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
  }, [stats.total_creators]);

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
          <Badge variant="primary">✨ Nouveau - Generation en 2 minutes</Badge>
          <h1 className="section-title gradient-text">Transforme tes videos en Shorts viraux</h1>
          <p className="muted" style={{ maxWidth: 700 }}>
            L'IA analyse, decoupe et formate automatiquement tes contenus YouTube en clips verticaux prets a publier.
          </p>
          <div className="inline-actions">
            <Link to="/register">
              <Button variant="accent">Essayer gratuitement</Button>
            </Link>
            <Link to="/pricing">
              <Button variant="secondary">Voir la demo ▶</Button>
            </Link>
          </div>
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}>
            <p className="caption">{creatorCount.toLocaleString("fr-FR")} createurs font confiance a ClipAI</p>
          </motion.div>
          <div className="ui-card" style={{ transform: "perspective(1000px) rotateX(4deg)", background: "rgba(18,18,42,0.9)" }}>
            <div className="grid grid-3">
              <div>
                <p className="caption">Input</p>
                <p>https://youtube.com/watch?v=clipai</p>
              </div>
              <div>
                <p className="caption">Detection IA</p>
                <p>8 extraits identifies</p>
              </div>
              <div>
                <p className="caption">Export</p>
                <p>MP4 1080x1920 - pret a poster</p>
              </div>
            </div>
          </div>
          <p className="muted" style={{ fontSize: 14 }}>
            🟢 {Number(stats.clips_today || 0).toLocaleString("fr-FR")} clips generes aujourd'hui
          </p>
        </div>
      </section>

      <section className="ui-card" style={{ overflow: "hidden" }}>
        <p className="caption">Qui utilise ClipAI</p>
        <div className="marquee" style={{ marginTop: 12 }}>
          <div className="marquee-track">
            {[...logos, ...logos].map((logo, index) => (
              <span key={`${logo}-${index}`} className="logo-chip">
                {logo}
              </span>
            ))}
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
            <p className="muted">3 videos/mois</p>
          </Card>

          <Card style={{ borderColor: "var(--accent)", animation: "glowPulse 2.4s ease infinite" }}>
            <Badge variant="success">Le plus populaire</Badge>
            <h3 style={{ marginTop: 8 }}>{pricing.pro}€{pricing.suffix}</h3>
            <p className="muted">Videos illimitees + mode equipe</p>
          </Card>

          <Card>
            <Badge variant="primary">Business</Badge>
            <h3 style={{ marginTop: 8 }}>{pricing.business}€{pricing.suffix}</h3>
            <p className="muted">API + branding white-label</p>
          </Card>
        </div>
      </section>

      <section className="ui-card" style={{ overflow: "hidden" }}>
        <h2 style={{ marginBottom: 12 }}>Ce que disent les createurs</h2>
        <div className="testimonials-strip">
          {[...testimonials, ...testimonials].map((item, index) => (
            <Card key={`${item.name}-${index}`} style={{ minWidth: 280 }}>
              <p style={{ color: "#fbbf24" }}>{item.stars}</p>
              <p style={{ marginTop: 8 }}>"{item.quote}"</p>
              <p className="muted" style={{ marginTop: 10 }}>
                {item.name} - {item.role}
              </p>
            </Card>
          ))}
        </div>
      </section>

      <section className="ui-card">
        <h2>Pourquoi ClipAI plutot qu'OpusClip ?</h2>
        <p className="muted" style={{ marginBottom: 12 }}>Meme resultat. 2x moins cher. Sans les bugs.</p>
        <div style={{ overflowX: "auto" }}>
          <table className="compare-table">
            <thead>
              <tr>
                <th>Feature</th>
                <th>ClipAI ✅</th>
                <th>OpusClip ❌</th>
                <th>Klap ❌</th>
                <th>Submagic ❌</th>
              </tr>
            </thead>
            <tbody>
              <tr><td>Gratuit sans watermark</td><td>✅</td><td>❌</td><td>❌</td><td>❌</td></tr>
              <tr><td>Pas de credits confus</td><td>✅</td><td>❌</td><td>❌</td><td>❌</td></tr>
              <tr><td>Scheduler fiable</td><td>✅</td><td>❌ buggy</td><td>❌</td><td>N/A</td></tr>
              <tr><td>AI Thumbnails integrees</td><td>✅</td><td>❌</td><td>❌</td><td>❌</td></tr>
              <tr><td>AI Coach personnel</td><td>✅</td><td>❌</td><td>❌</td><td>❌</td></tr>
              <tr><td>Support chat temps reel</td><td>✅</td><td>❌ 2.4/5</td><td>❌</td><td>❌</td></tr>
              <tr><td>Prix mensuel</td><td>19€</td><td>29€</td><td>29€</td><td>12€+</td></tr>
            </tbody>
          </table>
        </div>
      </section>

      <section className="ui-card">
        <h2>FAQ</h2>
        <div style={{ display: "grid", gap: 10, marginTop: 12 }}>
          {faqItems.map((item) => (
            <details key={item.q} className="faq-item">
              <summary>{item.q}</summary>
              <p className="muted">{item.a}</p>
            </details>
          ))}
        </div>
      </section>

      <section className="ui-card" style={{ background: "var(--gradient-primary)", color: "#fff" }}>
        <h2 className="section-title" style={{ fontSize: "clamp(1.8rem,4vw,2.8rem)", marginBottom: 10 }}>
          Lance ta machine a clips maintenant
        </h2>
        <p style={{ marginBottom: 14 }}>
          {Number(stats.clips_total || 0).toLocaleString("fr-FR")} clips deja generes sur ClipAI.
        </p>
        <Link to="/register">
          <Button variant="secondary">Creer mon compte</Button>
        </Link>
      </section>
    </div>
  );
}

export default Home;
