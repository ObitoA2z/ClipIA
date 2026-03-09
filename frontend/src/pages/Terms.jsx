function Terms() {
  return (
    <section className="page">
      <article className="ui-card">
        <p className="caption">LEGAL</p>
        <h2 className="section-title" style={{ fontSize: "2rem" }}>
          Conditions d'utilisation
        </h2>
        <p className="muted">Derniere mise a jour: 9 mars 2026</p>
      </article>

      <article className="ui-card" style={{ display: "grid", gap: 12 }}>
        <h3>1. Objet du service</h3>
        <p className="muted">
          ClipAI fournit un service SaaS de transformation de videos longues en clips courts. L'utilisateur reste responsable
          des droits sur les contenus soumis.
        </p>

        <h3>2. Compte utilisateur</h3>
        <p className="muted">
          L'utilisateur doit fournir des informations exactes et proteger ses identifiants. Toute activite effectuee via le
          compte est presumee etre autorisee par son titulaire.
        </p>

        <h3>3. Paiement et abonnement</h3>
        <p className="muted">
          Les abonnements sont geres via Stripe. Les prix et limites par plan sont affiches dans la page Pricing. La
          resiliation est possible a tout moment depuis l'espace compte.
        </p>

        <h3>4. Usage acceptable</h3>
        <p className="muted">
          Sont interdits: contenus illicites, atteinte aux droits d'auteur, tentative d'intrusion, abus de l'API, ou
          contournement des limitations de securite.
        </p>

        <h3>5. Limitation de responsabilite</h3>
        <p className="muted">
          Le service est fourni "en l'etat". ClipAI ne garantit pas une disponibilite ininterrompue ni l'absence totale
          d'erreurs. En cas d'incident, la responsabilite est limitee dans les conditions prevues par la loi applicable.
        </p>
      </article>
    </section>
  );
}

export default Terms;
