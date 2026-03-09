import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import toast from "react-hot-toast";

import api from "../services/api";

async function listEvents() {
  const { data } = await api.get("/scheduler/events");
  return data.events || [];
}

async function createEvent(payload) {
  const { data } = await api.post("/scheduler/events", payload);
  return data.event;
}

async function cancelEvent(eventId) {
  await api.post(`/scheduler/events/${eventId}/cancel`);
}

async function retryEvent(eventId) {
  await api.post(`/scheduler/events/${eventId}/retry`);
}

async function deleteEvent(eventId) {
  await api.delete(`/scheduler/events/${eventId}`);
}

function statusBadge(status) {
  const value = String(status || "scheduled").toLowerCase();
  if (value === "published") {
    return "score-badge score-good";
  }
  if (value === "failed" || value === "error") {
    return "score-badge score-low";
  }
  if (value === "cancelled") {
    return "score-badge";
  }
  return "score-badge score-viral";
}

export default function Scheduler() {
  const [clipId, setClipId] = useState("");
  const [platform, setPlatform] = useState("tiktok");
  const [dateValue, setDateValue] = useState("");
  const [title, setTitle] = useState("");
  const queryClient = useQueryClient();

  const eventsQuery = useQuery({ queryKey: ["schedule-events"], queryFn: listEvents, refetchInterval: 15000 });
  const createMutation = useMutation({
    mutationFn: createEvent,
    onSuccess: () => {
      toast.success("Publication planifiee");
      queryClient.invalidateQueries({ queryKey: ["schedule-events"] });
    },
    onError: (error) => {
      toast.error(error?.response?.data?.detail || "Erreur de planification");
    },
  });

  const actionMutation = useMutation({
    mutationFn: async ({ action, eventId }) => {
      if (action === "cancel") return cancelEvent(eventId);
      if (action === "retry") return retryEvent(eventId);
      return deleteEvent(eventId);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["schedule-events"] });
    },
    onError: (error) => {
      toast.error(error?.response?.data?.detail || "Action impossible");
    },
  });

  const grouped = useMemo(() => {
    const entries = eventsQuery.data || [];
    return entries.reduce((acc, item) => {
      const day = (item.scheduled_at || "").slice(0, 10) || "sans-date";
      acc[day] = acc[day] || [];
      acc[day].push(item);
      return acc;
    }, {});
  }, [eventsQuery.data]);

  const onSubmit = (event) => {
    event.preventDefault();
    createMutation.mutate({
      clip_id: clipId.trim(),
      platform,
      scheduled_at: dateValue,
      title: title.trim(),
      description: "",
      hashtags: [],
    });
  };

  return (
    <section className="page">
      <article className="ui-card">
        <p className="caption">SCHEDULER</p>
        <h2 className="section-title" style={{ fontSize: "2rem" }}>
          Calendrier de publication
        </h2>
        <form className="grid grid-3" style={{ marginTop: 14 }} onSubmit={onSubmit}>
          <input className="ui-input" placeholder="Clip ID" value={clipId} onChange={(e) => setClipId(e.target.value)} required />
          <select className="ui-input" value={platform} onChange={(e) => setPlatform(e.target.value)}>
            <option value="tiktok">TikTok</option>
            <option value="reels">Instagram Reels</option>
            <option value="shorts">YouTube Shorts</option>
            <option value="youtube">YouTube</option>
            <option value="instagram">Instagram</option>
            <option value="linkedin">LinkedIn</option>
          </select>
          <input className="ui-input" type="datetime-local" value={dateValue} onChange={(e) => setDateValue(e.target.value)} required />
          <input className="ui-input" placeholder="Titre (optionnel)" value={title} onChange={(e) => setTitle(e.target.value)} />
          <button type="submit" className="ui-btn ui-btn-primary" disabled={createMutation.isPending}>
            {createMutation.isPending ? "Planification..." : "Planifier"}
          </button>
        </form>
      </article>

      <article className="ui-card">
        <h3>Evenements</h3>
        <div style={{ display: "grid", gap: 10, marginTop: 10 }}>
          {Object.keys(grouped).length === 0 ? <p className="muted">Aucune publication planifiee.</p> : null}
          {Object.entries(grouped).map(([day, items]) => (
            <div key={day} className="ui-card" style={{ padding: 12 }}>
              <p className="caption">{day}</p>
              {(items || []).map((item) => (
                <div key={item.id} className="ui-card" style={{ padding: 10, marginTop: 8 }}>
                  <div className="inline-actions" style={{ justifyContent: "space-between", alignItems: "center" }}>
                    <p>
                      <strong>{item.platform}</strong> - clip {item.clip_id}
                    </p>
                    <span className={statusBadge(item.status)}>{item.status || "scheduled"}</span>
                  </div>
                  <p className="muted" style={{ fontSize: 13 }}>
                    {item.scheduled_at}
                    {item.attempts ? ` - tentatives: ${item.attempts}` : ""}
                  </p>
                  {item.last_error ? <p className="muted" style={{ fontSize: 13, color: "#F87171" }}>{item.last_error}</p> : null}
                  <div className="inline-actions" style={{ marginTop: 8 }}>
                    <button
                      type="button"
                      className="ui-btn ui-btn-secondary"
                      onClick={() => actionMutation.mutate({ action: "cancel", eventId: item.id })}
                    >
                      Annuler
                    </button>
                    <button
                      type="button"
                      className="ui-btn ui-btn-primary"
                      onClick={() => actionMutation.mutate({ action: "retry", eventId: item.id })}
                    >
                      Relancer
                    </button>
                    <button
                      type="button"
                      className="ui-btn ui-btn-secondary"
                      onClick={() => actionMutation.mutate({ action: "delete", eventId: item.id })}
                    >
                      Supprimer
                    </button>
                  </div>
                </div>
              ))}
            </div>
          ))}
        </div>
      </article>
    </section>
  );
}
