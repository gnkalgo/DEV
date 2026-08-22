import type { DashboardResponse } from "../types/dashboard";

export function IpModal({
  details,
  open,
  onClose,
}: {
  details: DashboardResponse["ip_details"];
  open: boolean;
  onClose: () => void;
}) {
  if (!open) return null;
  return (
    <div className="modal-backdrop" role="presentation" onClick={onClose}>
      <div
        className="card modal"
        role="dialog"
        aria-labelledby="ip-title"
        onClick={(event) => event.stopPropagation()}
      >
        <h2 id="ip-title">IP details</h2>
        <p className="muted">From backend config — not guessed in the browser.</p>
        <dl className="status-grid">
          <div>
            <dt>Application IP</dt>
            <dd>{details.application_ip}</dd>
          </div>
          <div>
            <dt>Broker API IP</dt>
            <dd>{details.broker_api_ip}</dd>
          </div>
          <div>
            <dt>Connection</dt>
            <dd>{details.connection_status}</dd>
          </div>
          <div>
            <dt>Last verified</dt>
            <dd>{details.last_verified ?? "—"}</dd>
          </div>
          <div>
            <dt>Environment</dt>
            <dd>{details.environment}</dd>
          </div>
        </dl>
        <button type="button" onClick={onClose}>
          Close
        </button>
      </div>
    </div>
  );
}
