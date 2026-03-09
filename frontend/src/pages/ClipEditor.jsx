import { useState } from "react";
import { useParams } from "react-router-dom";
import toast from "react-hot-toast";

import { recutClip } from "../services/videoService";

export default function ClipEditor() {
  const { clipId } = useParams();
  const [start, setStart] = useState(0);
  const [end, setEnd] = useState(30);
  const [loading, setLoading] = useState(false);

  const handleSave = async () => {
    if (end <= start) {
      toast.error("La fin doit etre superieure au debut");
      return;
    }
    setLoading(true);
    try {
      await recutClip(clipId, { start, end });
      toast.success("Clip recoupe avec succes");
    } catch (error) {
      toast.error(error?.response?.data?.detail || "Erreur pendant la recoupe");
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="page">
      <article className="ui-card">
        <p className="caption">CLIP EDITOR</p>
        <h2 className="section-title" style={{ fontSize: "2rem" }}>
          Edition rapide du clip
        </h2>
        <p className="muted">Ajuste les timestamps puis recoupe automatiquement le clip.</p>

        <div className="grid grid-2" style={{ marginTop: 16 }}>
          <label>
            Debut (secondes)
            <input
              className="ui-input"
              type="number"
              min={0}
              value={start}
              onChange={(e) => setStart(Number(e.target.value))}
            />
          </label>
          <label>
            Fin (secondes)
            <input
              className="ui-input"
              type="number"
              min={0}
              value={end}
              onChange={(e) => setEnd(Number(e.target.value))}
            />
          </label>
        </div>

        <div className="inline-actions" style={{ marginTop: 16 }}>
          <button type="button" className="ui-btn ui-btn-primary" onClick={handleSave} disabled={loading}>
            {loading ? "Recoupe..." : "Recouper"}
          </button>
        </div>
      </article>
    </section>
  );
}

