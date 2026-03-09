import { useState } from "react";
import toast from "react-hot-toast";

import api from "../services/api";

export default function ThumbnailEditor({ clipId }) {
  const [hook, setHook] = useState("");
  const [target, setTarget] = useState("youtube");
  const [variants, setVariants] = useState([]);
  const [loading, setLoading] = useState(false);

  const generate = async () => {
    setLoading(true);
    try {
      const { data } = await api.post(`/clips/${clipId}/thumbnails`, {
        hook: hook.trim() || null,
        target,
        variants: 3,
      });
      setVariants(data?.thumbnails || []);
      toast.success("Thumbnails generees");
    } catch (error) {
      toast.error(error?.response?.data?.detail || "Generation thumbnail impossible");
    } finally {
      setLoading(false);
    }
  };

  return (
    <article className="ui-card" style={{ marginTop: 16, display: "grid", gap: 12 }}>
      <p className="caption">AI THUMBNAILS</p>
      <div className="grid grid-2" style={{ gap: 12 }}>
        <label htmlFor="thumb-hook" style={{ display: "grid", gap: 8 }}>
          <span className="muted">Texte accroche</span>
          <input
            id="thumb-hook"
            className="ui-input"
            placeholder="Ex: Le detail qui change tout"
            value={hook}
            onChange={(event) => setHook(event.target.value)}
          />
        </label>

        <label htmlFor="thumb-target" style={{ display: "grid", gap: 8 }}>
          <span className="muted">Format</span>
          <select id="thumb-target" className="ui-input" value={target} onChange={(event) => setTarget(event.target.value)}>
            <option value="youtube">YouTube 1280x720</option>
            <option value="instagram">Instagram 1080x1080</option>
          </select>
        </label>
      </div>

      <div className="inline-actions" style={{ justifyContent: "space-between", alignItems: "center" }}>
        <p className="muted">3 variantes automatiques avec scoring IA</p>
        <button type="button" className="ui-btn ui-btn-primary" onClick={generate} disabled={loading}>
          {loading ? "Generation..." : "Generer"}
        </button>
      </div>

      {variants.length ? (
        <div className="grid grid-3" style={{ gap: 12 }}>
          {variants.map((item) => (
            <a key={item.rank} href={item.url} target="_blank" rel="noreferrer" className="ui-card" style={{ display: "grid", gap: 8 }}>
              <img src={item.url} alt={item.headline} loading="lazy" style={{ width: "100%", borderRadius: 10 }} />
              <p className="muted" style={{ fontSize: 13 }}>{item.headline}</p>
            </a>
          ))}
        </div>
      ) : null}
    </article>
  );
}
