import { useQuery } from "@tanstack/react-query";

import api from "../services/api";
import Card from "../components/ui/Card";

async function fetchCoachReport() {
  const { data } = await api.get("/ai-coach/report");
  return data;
}

function AICoachPage() {
  const coachQuery = useQuery({ queryKey: ["ai-coach-report"], queryFn: fetchCoachReport, refetchInterval: 60000 });
  const report = coachQuery.data?.report;
  const unlocked = coachQuery.data?.unlocked;

  return (
    <section className="page">
      <Card>
        <p className="caption">AI COACH</p>
        <h2 className="section-title" style={{ fontSize: "2rem" }}>Coach personnel</h2>
        <p className="muted">Score hebdo, axes d'amelioration et objectif de la semaine.</p>
      </Card>

      {coachQuery.isLoading ? <Card><div className="skeleton" /></Card> : null}

      {!coachQuery.isLoading && !unlocked ? (
        <Card>
          <p className="muted">
            Genere 5 videos pour debloquer ton AI Coach.
          </p>
        </Card>
      ) : null}

      {!coachQuery.isLoading && unlocked && report ? (
        <>
          <div className="grid grid-3">
            <Card>
              <p className="caption">Score hebdo</p>
              <p style={{ fontSize: 42, fontWeight: 800 }}>{report.weekly_score}/100</p>
              <p className="muted">{report.trend}</p>
            </Card>
            <Card>
              <p className="caption">Style detecte</p>
              <p>{report.creator_style}</p>
            </Card>
            <Card>
              <p className="caption">Objectif</p>
              <p>{report.next_goal}</p>
            </Card>
          </div>

          <Card>
            <h3>Conseil de la semaine</h3>
            <p>{report.this_week_tip}</p>
            <p className="muted" style={{ marginTop: 10 }}>
              Meilleur moment predit: {report.predicted_best_day} • {report.predicted_best_time}
            </p>
          </Card>

          <Card>
            <h3>Analyse par sujet</h3>
            <div className="grid grid-2" style={{ marginTop: 12 }}>
              {(report.topic_analysis || []).map((topic) => (
                <div key={topic.topic} className="ui-card" style={{ padding: 14 }}>
                  <p style={{ fontWeight: 700 }}>{topic.topic}</p>
                  <p className="muted">Score: {topic.score}</p>
                  <p className="muted">{topic.note}</p>
                </div>
              ))}
            </div>
          </Card>
        </>
      ) : null}
    </section>
  );
}

export default AICoachPage;
