import { useState } from "react";

export default function AdminSettings() {
  const [maintenance, setMaintenance] = useState(false);
  const [allowRegister, setAllowRegister] = useState(true);
  const [force2FA, setForce2FA] = useState(false);

  return (
    <article className="ui-card">
      <h3>Feature Flags</h3>
      <div style={{ display: "grid", gap: 12, marginTop: 10 }}>
        <label><input type="checkbox" checked={maintenance} onChange={(e) => setMaintenance(e.target.checked)} /> Maintenance mode</label>
        <label><input type="checkbox" checked={allowRegister} onChange={(e) => setAllowRegister(e.target.checked)} /> Allow registrations</label>
        <label><input type="checkbox" checked={force2FA} onChange={(e) => setForce2FA(e.target.checked)} /> Force 2FA</label>
      </div>
      <p className="muted" style={{ marginTop: 12 }}>These flags are local UI placeholders and can be connected to /admin settings API.</p>
    </article>
  );
}
