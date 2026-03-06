function PricingCard({ title, price, description, actionLabel, onAction }) {
  return (
    <article className="card">
      <h3>{title}</h3>
      <p style={{ fontSize: 24, margin: "8px 0" }}>{price}</p>
      <p className="muted">{description}</p>
      <button type="button" className="btn btn-primary" onClick={onAction}>
        {actionLabel}
      </button>
    </article>
  );
}

export default PricingCard;
