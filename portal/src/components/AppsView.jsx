// portal/src/components/AppsView.jsx
import React from "react";
import {
  getClientStatusLabel,
  getClientStatusText,
  getSelectedClient,
} from "../utils/adminHelpers";

export default function AppsView({
  rawApps,
  selectedClientByApp,
  setSelectedClientByApp,
  enterApp,
}) {
  return (
    <section className="section">
      <h2 className="section-title">Mis aplicaciones</h2>

      {rawApps.length === 0 ? (
        <div className="empty-state">
          <p className="empty-state-text">📭 No hay aplicaciones asignadas a tu usuario.</p>
        </div>
      ) : (
        <div className="apps-grid">
          {rawApps.map((app) => (
            <div key={app.app_id} className="app-card">
              <div className="app-card-header">
                <h3 className="app-title">{app.app}</h3>
                <span className="app-badge">
                  {app.clients?.length || 0} cliente{app.clients?.length !== 1 ? "s" : ""}
                </span>
              </div>

              {app.description && (
                <p className="app-description">{app.description}</p>
              )}

              {app.clients && app.clients.length > 0 && (() => {
                const selectedClient = getSelectedClient(app, selectedClientByApp);
                const canLaunch = !!selectedClient?.is_accessible;

                return (
                  <>
                    <div className="form-group">
                      <label className="label">Seleccionar cliente:</label>
                      <select
                        className="select"
                        value={selectedClientByApp[app.app_id] || ""}
                        onChange={(e) =>
                          setSelectedClientByApp((prev) => ({
                            ...prev,
                            [app.app_id]: Number(e.target.value),
                          }))
                        }
                      >
                        {app.clients?.map((client) => (
                          <option key={client.id} value={client.id}>
                            {client.name} ({getClientStatusLabel(client)})
                          </option>
                        ))}
                      </select>

                      {selectedClient && (
                        <div
                          className={`rs-client-status rs-status-${selectedClient.subscription_status}${
                            selectedClient.is_expiring_soon ? " rs-status-expiring" : ""
                          }`}
                        >
                          {getClientStatusText(selectedClient)}
                        </div>
                      )}
                    </div>

                    <button
                      className={`button button-primary button-fullwidth${!canLaunch ? " rs-button-disabled" : ""}`}
                      onClick={() => enterApp(app)}
                      disabled={!canLaunch}
                    >
                      {canLaunch ? `▶ Entrar a ${app.app}` : "No disponible"}
                    </button>
                  </>
                );
              })()}
            </div>
          ))}
        </div>
      )}
    </section>
  );
}