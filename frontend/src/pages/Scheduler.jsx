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

export default function Scheduler() {
  const [clipId, setClipId] = useState("");
  const [platform, setPlatform] = useState("tiktok");
  const [dateValue, setDateValue] = useState("");
  const queryClient = useQueryClient();

  const eventsQuery = useQuery({ queryKey: ["schedule-events"], queryFn: listEvents });
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

  const grouped = useMemo(() => {
    const entries = eventsQuery.data || [];
    return entries.reduce((acc, item) => {
      const day = (item.scheduled_at || "").slice(0, 10);
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
          <input className="ui-input" placeholder="Clip ID" value={clipId} onChange={(e) => setClipId(e.target.value)} />
          <select className="ui-input" value={platform} onChange={(e) => setPlatform(e.target.value)}>
            <option value="tiktok">TikTok</option>
            <option value="reels">Instagram Reels</option>
            <option value="shorts">YouTube Shorts</option>
            <option value="youtube">YouTube</option>
          </select>
          <input className="ui-input" type="datetime-local" value={dateValue} onChange={(e) => setDateValue(e.target.value)} />
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
                <p key={item.id} style={{ marginTop: 6 }}>
                  {item.platform} - clip {item.clip_id} - {item.scheduled_at}
                </p>
              ))}
            </div>
          ))}
        </div>
      </article>
    </section>
  );
}

