import { Link } from "react-router-dom";

function Hero() {
  return (
    <section className="hero">
      <h1>Transforme une video YouTube longue en clips courts automatiquement.</h1>
      <p className="muted">
        Colle ton lien, laisse le pipeline tourner et recupere des clips verticaux prets a poster.
      </p>
      <div className="inline-actions">
        <Link to="/register" className="btn btn-primary">
          Commencer gratuitement
        </Link>
        <Link to="/dashboard" className="btn btn-secondary">
          Ouvrir le dashboard
        </Link>
      </div>
    </section>
  );
}

export default Hero;
