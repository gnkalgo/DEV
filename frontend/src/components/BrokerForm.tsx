import { useState } from "react";

const BROKERS = ["MOCK", "DHAN", "ZERODHA", "ANGEL_ONE", "GROWW", "ALICE_BLUE"] as const;

export function BrokerForm() {
  const [message, setMessage] = useState<string | null>(null);

  return (
    <form
      className="auth-form"
      onSubmit={(event) => {
        event.preventDefault();
        setMessage("Save/Connect is Phase 5 (Mock) and Phase 6 (Dhan). Secrets are not sent from this screen.");
      }}
    >
      <label>
        Broker
        <select defaultValue="MOCK">
          {BROKERS.map((name) => (
            <option key={name} value={name}>
              {name}
              {name !== "MOCK" && name !== "DHAN" ? " (TODO)" : ""}
            </option>
          ))}
        </select>
      </label>
      <label>
        Client ID
        <input name="client_id" autoComplete="off" />
      </label>
      <label>
        API Key
        <input name="api_key" type="password" autoComplete="off" placeholder="************" />
      </label>
      <label>
        API Secret
        <input name="api_secret" type="password" autoComplete="off" placeholder="************" />
      </label>
      <label>
        TOTP Token
        <input name="totp" type="password" autoComplete="off" placeholder="************" />
      </label>
      {message ? <p className="muted">{message}</p> : null}
      <div className="inline-actions">
        <button type="submit">Save broker</button>
        <button type="button" className="secondary" disabled>
          Test / Connect (Phase 5–6)
        </button>
      </div>
    </form>
  );
}
