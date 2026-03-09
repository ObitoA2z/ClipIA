import { useQuery } from "@tanstack/react-query";

import api from "../services/api";

async function fetchReferralDashboard() {
  const { data } = await api.get("/referral/me");
  return data;
}

export default function ReferralPage() {
  const referralQuery = useQuery({ queryKey: ["referral-me"], queryFn: fetchReferralDashboard });
  const data = referralQuery.data;

  return (
    <section className="page">
      <article className="ui-card">
        <p className="caption">REFERRAL</p>
        <h2 className="section-title" style={{ fontSize: "2rem" }}>
          Programme de parrainage
        </h2>
        <p className="muted" style={{ marginTop: 6 }}>
          Invite des créateurs: 1 mois offert pour chaque filleul qui passe Pro.
        </p>

        {referralQuery.isLoading ? <p className="muted" style={{ marginTop: 12 }}>Chargement...</p> : null}

        {data ? (
          <div className="grid grid-3" style={{ marginTop: 16 }}>
            <div className="ui-card">
              <p className="caption">Code</p>
              <h3>{data.code}</h3>
            </div>
            <div className="ui-card">
              <p className="caption">Invites</p>
              <h3>{data.invited}</h3>
            </div>
            <div className="ui-card">
              <p className="caption">Recompenses</p>
              <h3>{data.rewards}</h3>
            </div>
          </div>
        ) : null}
      </article>
    </section>
  );
}

