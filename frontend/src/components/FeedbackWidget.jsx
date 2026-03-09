import { useState } from "react";
import toast from "react-hot-toast";

import { submitFeedback } from "../services/feedbackService";

export default function FeedbackWidget() {
  const [open, setOpen] = useState(false);
  const [rating, setRating] = useState(5);
  const [category, setCategory] = useState("suggestion");
  const [message, setMessage] = useState("");
  const [sending, setSending] = useState(false);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setSending(true);
    try {
      await submitFeedback({
        type: category,
        rating: category === "nps" ? rating : undefined,
        message,
        page_url: window.location.pathname,
      });
      toast.success("Merci pour ton feedback");
      setOpen(false);
      setMessage("");
    } catch (error) {
      toast.error(error?.response?.data?.detail || "Erreur feedback");
    } finally {
      setSending(false);
    }
  };

  return (
    <>
      <button
        type="button"
        className="ui-btn ui-btn-accent"
        style={{ position: "fixed", right: 18, bottom: 18, zIndex: 60 }}
        onClick={() => setOpen((value) => !value)}
      >
        Feedback
      </button>

      {open ? (
        <div
          style={{
            position: "fixed",
            inset: 0,
            background: "rgba(4,4,13,0.7)",
            backdropFilter: "blur(6px)",
            display: "grid",
            placeItems: "center",
            zIndex: 61,
            padding: 16,
          }}
        >
          <form className="ui-card" style={{ width: "min(460px, 92vw)" }} onSubmit={handleSubmit}>
            <h3>Ton avis sur ClipAI</h3>
            <div className="grid" style={{ gap: 10, marginTop: 10 }}>
              <select className="ui-input" value={category} onChange={(e) => setCategory(e.target.value)}>
                <option value="bug">Bug</option>
                <option value="suggestion">Suggestion</option>
                <option value="compliment">Compliment</option>
                <option value="nps">NPS</option>
              </select>
              {category === "nps" ? (
                <input className="ui-input" type="number" min={0} max={10} value={rating} onChange={(e) => setRating(Number(e.target.value))} />
              ) : null}
              <textarea
                className="ui-input"
                rows={4}
                placeholder="Ecris ton message..."
                value={message}
                onChange={(e) => setMessage(e.target.value)}
              />
              <div className="inline-actions">
                <button type="submit" className="ui-btn ui-btn-primary" disabled={sending || message.trim().length < 3}>
                  {sending ? "Envoi..." : "Envoyer"}
                </button>
                <button type="button" className="ui-btn ui-btn-secondary" onClick={() => setOpen(false)}>
                  Fermer
                </button>
              </div>
            </div>
          </form>
        </div>
      ) : null}
    </>
  );
}

