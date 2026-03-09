import toast from "react-hot-toast";

export default function AdminTools() {
  const actions = [
    { label: "Relancer pipeline test", message: "Pipeline test relancé" },
    { label: "Purger cache Redis", message: "Cache Redis purgé" },
    { label: "Nettoyer temp files", message: "Fichiers temporaires nettoyés" },
    { label: "Vider queue Celery", message: "Queue Celery vidée" }
  ];

  return (
    <article className="ui-card">
      <h3>Admin Tools</h3>
      <div className="inline-actions" style={{ marginTop: 12 }}>
        {actions.map((action) => (
          <button
            key={action.label}
            type="button"
            className="ui-btn ui-btn-secondary"
            onClick={() => toast.success(action.message)}
          >
            {action.label}
          </button>
        ))}
      </div>
    </article>
  );
}
