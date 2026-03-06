function Features() {
  const items = [
    "Detection automatique des moments forts",
    "Suivi d'avancement en temps reel",
    "Clips 9:16 prets pour TikTok, Reels et Shorts",
  ];

  return (
    <section className="grid grid-2" style={{ marginTop: 16 }}>
      {items.map((item) => (
        <article key={item} className="card">
          <h3>{item}</h3>
          <p className="muted">
            Fonctionnalite active dans ce MVP local pour valider ton flux de travail rapidement.
          </p>
        </article>
      ))}
    </section>
  );
}

export default Features;
