import { useState } from "react";
import toast from "react-hot-toast";

import api from "../services/api";

export default function AICommandBar({ clipId, onApplied }) {
  const [command, setCommand] = useState("");
  const [loading, setLoading] = useState(false);
  const [lastAction, setLastAction] = useState("");

  const submitCommand = async (event) => {
    event.preventDefault();
    if (!command.trim()) {
      return;
    }

    setLoading(true);
    try {
      const { data } = await api.post("/ai-commands/apply", {
        clip_id: clipId,
        command: command.trim(),
      });
      const action = data?.result?.action || "noop";
      setLastAction(action);
      setCommand("");
      toast.success(`Commande appliquee: ${action}`);
      if (onApplied) {
        onApplied(data);
      }
    } catch (error) {
      toast.error(error?.response?.data?.detail || "Commande IA impossible a appliquer");
    } finally {
      setLoading(false);
    }
  };

  return (
    <form className="ui-card" style={{ marginTop: 16, display: "grid", gap: 10 }} onSubmit={submitCommand}>
      <p className="caption">UNDERLORD COMMANDS</p>
      <label htmlFor="ai-command" style={{ display: "grid", gap: 8 }}>
        <span className="muted">Dis a l'IA ce que tu veux faire</span>
        <input
          id="ai-command"
          className="ui-input"
          placeholder="Ex: Raccourcis le debut de 5 secondes"
          value={command}
          onChange={(event) => setCommand(event.target.value)}
        />
      </label>
      <div className="inline-actions" style={{ justifyContent: "space-between", alignItems: "center" }}>
        <p className="muted">Derniere action: {lastAction || "aucune"}</p>
        <button type="submit" className="ui-btn ui-btn-primary" disabled={loading}>
          {loading ? "Execution..." : "Executer"}
        </button>
      </div>
    </form>
  );
}
