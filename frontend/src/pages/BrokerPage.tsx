import { BrokerForm } from "../components/BrokerForm";

export function BrokerPage() {
  return (
    <section className="card">
      <h1>Broker</h1>
      <p className="muted">
        Secrets stay in the form until Phase 5 persist/connect. Existing secrets would display as ************ only.
      </p>
      <BrokerForm />
    </section>
  );
}
