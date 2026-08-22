import { BrokerForm } from "../components/BrokerForm";

export function BrokerPage() {
  return (
    <section className="card">
      <h1>Broker</h1>
      <p className="muted">
        Save Mock or Dhan credentials (encrypted server-side). Secrets display as ************ when already stored.
      </p>
      <BrokerForm />
    </section>
  );
}
