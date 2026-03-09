import { Link } from "react-router-dom";

function Footer() {
  return (
    <footer className="footer">
      <div style={{ display: "flex", justifyContent: "space-between", gap: 12, flexWrap: "wrap", alignItems: "center" }}>
        <span>ClipAI - SaaS de generation de shorts IA</span>
        <div className="inline-actions">
          <Link to="/terms" className="muted">
            Conditions
          </Link>
          <Link to="/privacy" className="muted">
            Confidentialite
          </Link>
          <span className="muted">© {new Date().getFullYear()} ClipAI</span>
        </div>
      </div>
    </footer>
  );
}

export default Footer;
