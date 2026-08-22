import { useEffect, useState } from "react";
import { useAuth } from "../hooks/useAuth";
import { getDashboard } from "../services/api";
import { isSoundsMuted, setSoundsMuted } from "../utils/sounds";

export function SettingsPage() {
  const { user } = useAuth();
  const [muted, setMuted] = useState(isSoundsMuted);
  const [env, setEnv] = useState<string>("");
  const [mode, setMode] = useState<string>("");

  useEffect(() => {
    void getDashboard().then((data) => {
      setEnv(data.environment);
      setMode(data.trading_mode);
    });
  }, []);

  return (
    <section className="card">
      <h1>Settings</h1>
      <dl className="status-grid">
        <div>
          <dt>User</dt>
          <dd>{user?.email}</dd>
        </div>
        <div>
          <dt>Environment</dt>
          <dd>{env || "…"}</dd>
        </div>
        <div>
          <dt>Trading mode</dt>
          <dd>{mode || "…"}</dd>
        </div>
      </dl>
      <label className="check-row">
        <input
          type="checkbox"
          checked={muted}
          onChange={(event) => {
            setSoundsMuted(event.target.checked);
            setMuted(event.target.checked);
          }}
        />
        Mute order-book and cancel ticks
      </label>
    </section>
  );
}
