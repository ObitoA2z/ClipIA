function Footer() {
  return (
    <footer className="footer">
      <div style={{ display: "flex", justifyContent: "space-between", gap: 12, flexWrap: "wrap" }}>
        <span>ClipAI • SaaS de génération de shorts IA</span>
        <span className="muted">© {new Date().getFullYear()} ClipAI</span>
      </div>
    </footer>
  );
}

export default Footer;
