import { useEffect, useState } from "react";
import {
  BrokerPublic,
  connectBroker,
  disconnectBroker,
  listBrokers,
  saveBroker,
  testBroker,
} from "../services/api";

const BROKERS = ["MOCK", "DHAN", "ZERODHA", "ANGEL_ONE", "GROWW", "ALICE_BLUE"] as const;

export function BrokerForm() {
  const [brokers, setBrokers] = useState<BrokerPublic[]>([]);
  const [selectedId, setSelectedId] = useState<string>("");
  const [broker, setBroker] = useState<(typeof BROKERS)[number]>("MOCK");
  const [clientId, setClientId] = useState("MOCK-1");
  const [apiKey, setApiKey] = useState("");
  const [apiSecret, setApiSecret] = useState("");
  const [totp, setTotp] = useState("");
  const [accessToken, setAccessToken] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const refresh = async () => {
    const data = await listBrokers();
    setBrokers(data);
    if (data.length > 0 && !selectedId) {
      setSelectedId(data[0].id);
    }
  };

  useEffect(() => {
    void refresh().catch((err: Error) => setError(err.message));
  }, []);

  const active = brokers.find((row) => row.id === selectedId) ?? brokers[0];

  return (
    <form
      className="auth-form"
      onSubmit={(event) => {
        event.preventDefault();
        setError(null);
        setMessage(null);
        void saveBroker({
          broker,
          client_id: clientId,
          api_key: apiKey || undefined,
          api_secret: apiSecret || undefined,
          totp: totp || undefined,
        })
          .then(async (saved) => {
            setMessage(`Saved ${saved.broker} (${saved.client_id})`);
            setApiKey("");
            setApiSecret("");
            setTotp("");
            await refresh();
            setSelectedId(saved.id);
          })
          .catch((err: Error) => setError(err.message));
      }}
    >
      <label>
        Broker
        <select value={broker} onChange={(event) => setBroker(event.target.value as (typeof BROKERS)[number])}>
          {BROKERS.map((name) => (
            <option key={name} value={name} disabled={name !== "MOCK" && name !== "DHAN"}>
              {name}
              {name !== "MOCK" && name !== "DHAN" ? " (TODO)" : ""}
            </option>
          ))}
        </select>
      </label>
      <label>
        Client ID
        <input name="client_id" autoComplete="off" value={clientId} onChange={(e) => setClientId(e.target.value)} />
      </label>
      <label>
        API Key / Trading PIN
        <input
          name="api_key"
          type="password"
          autoComplete="off"
          placeholder={active?.has_api_key ? "************" : ""}
          value={apiKey}
          onChange={(e) => setApiKey(e.target.value)}
        />
      </label>
      <label>
        API Secret
        <input
          name="api_secret"
          type="password"
          autoComplete="off"
          placeholder={active?.has_api_secret ? "************" : ""}
          value={apiSecret}
          onChange={(e) => setApiSecret(e.target.value)}
        />
      </label>
      <label>
        TOTP Token
        <input
          name="totp"
          type="password"
          autoComplete="off"
          placeholder={active?.has_totp ? "************" : ""}
          value={totp}
          onChange={(e) => setTotp(e.target.value)}
        />
      </label>
      {broker === "DHAN" ? (
        <label>
          Access token (connect only, from web.dhan.co)
          <input
            name="access_token"
            type="password"
            autoComplete="off"
            value={accessToken}
            onChange={(e) => setAccessToken(e.target.value)}
          />
        </label>
      ) : null}
      {brokers.length > 0 ? (
        <label>
          Saved account
          <select value={selectedId} onChange={(event) => setSelectedId(event.target.value)}>
            {brokers.map((row) => (
              <option key={row.id} value={row.id}>
                {row.broker} — {row.client_id} ({row.status})
              </option>
            ))}
          </select>
        </label>
      ) : null}
      {message ? <p className="muted">{message}</p> : null}
      {error ? <p className="error">{error}</p> : null}
      <div className="inline-actions">
        <button type="submit">Save broker</button>
        <button
          type="button"
          className="secondary"
          disabled={!selectedId}
          onClick={() => {
            if (!selectedId) return;
            setError(null);
            void testBroker(selectedId)
              .then((result) => setMessage(result.message ?? "Connection OK"))
              .catch((err: Error) => setError(err.message));
          }}
        >
          Test connection
        </button>
        <button
          type="button"
          disabled={!selectedId}
          onClick={() => {
            if (!selectedId) return;
            setError(null);
            void connectBroker(selectedId, accessToken ? { access_token: accessToken } : undefined)
              .then(async (result) => {
                setMessage(result.message ?? "Connected");
                setAccessToken("");
                await refresh();
              })
              .catch((err: Error) => setError(err.message));
          }}
        >
          Connect
        </button>
        <button
          type="button"
          className="secondary"
          disabled={!selectedId}
          onClick={() => {
            if (!selectedId) return;
            void disconnectBroker(selectedId)
              .then(async (result) => {
                setMessage(result.message ?? "Disconnected");
                await refresh();
              })
              .catch((err: Error) => setError(err.message));
          }}
        >
          Disconnect
        </button>
      </div>
    </form>
  );
}
