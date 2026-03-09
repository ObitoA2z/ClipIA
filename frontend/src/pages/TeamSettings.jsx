import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import toast from "react-hot-toast";

import api from "../services/api";

async function fetchTeams() {
  const { data } = await api.get("/teams");
  return data;
}

async function createTeam(name) {
  const { data } = await api.post("/teams", { name });
  return data;
}

export default function TeamSettings() {
  const [teamName, setTeamName] = useState("");
  const queryClient = useQueryClient();

  const teamsQuery = useQuery({ queryKey: ["teams"], queryFn: fetchTeams });
  const createMutation = useMutation({
    mutationFn: createTeam,
    onSuccess: () => {
      toast.success("Workspace cree");
      setTeamName("");
      queryClient.invalidateQueries({ queryKey: ["teams"] });
    },
    onError: (error) => {
      toast.error(error?.response?.data?.detail || "Erreur creation workspace");
    },
  });

  return (
    <section className="page">
      <article className="ui-card">
        <p className="caption">TEAM SETTINGS</p>
        <h2 className="section-title" style={{ fontSize: "2rem" }}>
          Workspace Business
        </h2>
        <div className="inline-actions" style={{ marginTop: 12 }}>
          <input className="ui-input" placeholder="Nom de l'equipe" value={teamName} onChange={(e) => setTeamName(e.target.value)} />
          <button
            type="button"
            className="ui-btn ui-btn-primary"
            onClick={() => createMutation.mutate(teamName)}
            disabled={createMutation.isPending || teamName.trim().length < 2}
          >
            {createMutation.isPending ? "Creation..." : "Creer"}
          </button>
        </div>

        <div style={{ marginTop: 16, display: "grid", gap: 10 }}>
          {(teamsQuery.data?.teams || []).map((team) => (
            <div key={team.id} className="ui-card" style={{ padding: 12 }}>
              <h4>{team.name}</h4>
              <p className="muted">{team.id}</p>
            </div>
          ))}
        </div>
      </article>
    </section>
  );
}

