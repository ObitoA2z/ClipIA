function Privacy() {
  return (
    <section className="page">
      <article className="ui-card">
        <p className="caption">LEGAL</p>
        <h2 className="section-title" style={{ fontSize: "2rem" }}>
          Politique de confidentialite
        </h2>
        <p className="muted">Derniere mise a jour: 9 mars 2026</p>
      </article>

      <article className="ui-card" style={{ display: "grid", gap: 12 }}>
        <h3>1. Donnees collectees</h3>
        <p className="muted">
          Nous collectons les donnees de compte (email, nom), donnees techniques (IP, user-agent), et donnees de service
          necessaires au traitement des videos.
        </p>

        <h3>2. Finalites</h3>
        <p className="muted">
          Ces donnees sont utilisees pour authentifier l'utilisateur, executer le pipeline video, facturer les abonnements,
          assurer la securite et ameliorer le service.
        </p>

        <h3>3. Partage avec des sous-traitants</h3>
        <p className="muted">
          ClipAI utilise des fournisseurs tiers (ex: Stripe, Supabase, Cloudflare R2) strictement pour operer le service.
          Nous ne revendons pas les donnees personnelles.
        </p>

        <h3>4. Conservation</h3>
        <p className="muted">
          Les donnees sont conservees selon la politique de retention du service. L'utilisateur peut demander l'export ou la
          suppression de ses donnees via les endpoints RGPD.
        </p>

        <h3>5. Droits RGPD</h3>
        <p className="muted">
          Vous disposez d'un droit d'acces, de rectification, d'opposition, d'effacement et de portabilite.
        </p>
      </article>
    </section>
  );
}

export default Privacy;
