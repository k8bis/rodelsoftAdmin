// portal/src/components/AdminModal.jsx
import React from "react";
import { isGlobalAdminTab } from "../utils/adminHelpers";
import AdminEditorModal from "./AdminEditorModal";

export default function AdminModal({
  adminModalOpen,
  closeAdminModal,
  adminLoadingClients,
  adminClients,
  adminSelectedClientId,
  setAdminSelectedClientId,
  fetchAdminClients,
  adminSelectedClientName,
  isSystemAdmin,
  adminTab,
  setAdminTab,
  adminActionMsg,
  adminActionMsgType,
  adminLoadingData,
  adminGlobalUsers,
  adminGlobalApplications,
  adminGlobalClients,
  adminUsers,
  adminSubscriptions,
  adminPermissions,
  openAdminEditor,
  adminEditorOpen,
  closeAdminEditor,
  adminEditorType,
  adminEditorMode,
  adminActionLoading,
  adminCreateUserForm,
  setAdminCreateUserForm,
  adminCreateClientForm,
  setAdminCreateClientForm,
  adminApplicationForm,
  setAdminApplicationForm,
  adminSubscriptionForm,
  setAdminSubscriptionForm,
  adminPermissionForm,
  setAdminPermissionForm,
  adminAppsCatalog,
  adminPermissionUsers,
  adminPermissionApps,
  handleCreateGlobalUser,
  handleUpdateGlobalUser,
  handleCreateGlobalClient,
  handleUpdateGlobalClient,
  handleCreateGlobalApplication,
  handleUpdateGlobalApplication,
  handleCreateSubscription,
  handleUpdateSubscription,
  handleCreatePermission,
  handleUpdatePermissionRole,
  reloadCurrentAdminTab,
}) {
  if (!adminModalOpen) return null;

  return (
    <div
      className="rs-admin-modal-overlay"
      onClick={() => closeAdminModal()}
    >
      <div
        className="rs-admin-modal"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="rs-admin-modal-header">
          <div>
            <h2 className="rs-admin-modal-title">Administración</h2>
            <p className="rs-admin-modal-subtitle">
              Consulta interna de clientes, usuarios, suscripciones y permisos
            </p>
          </div>

          <button
            type="button"
            className="rs-admin-close"
            onClick={() => closeAdminModal()}
          >
            ✕
          </button>
        </div>

        <div className="rs-admin-toolbar">
          {!isGlobalAdminTab(adminTab) ? (
            <>
              <div className="rs-admin-field">
                <label className="label">Cliente</label>
                <select
                  className="select"
                  value={adminSelectedClientId}
                  onChange={(e) => setAdminSelectedClientId(e.target.value)}
                  disabled={adminLoadingClients || adminClients.length === 0}
                >
                  {adminLoadingClients ? (
                    <option value="">Cargando clientes...</option>
                  ) : adminClients.length === 0 ? (
                    <option value="">Sin clientes disponibles</option>
                  ) : (
                    adminClients.map((client) => (
                      <option key={client.client_id} value={client.client_id}>
                        {client.client_name}
                      </option>
                    ))
                  )}
                </select>
              </div>

              <button
                type="button"
                className="button button-secondary"
                onClick={() => fetchAdminClients()}
                disabled={adminLoadingClients}
              >
                {adminLoadingClients ? "Cargando..." : "↻ Recargar clientes"}
              </button>
            </>
          ) : (
            <div className="rs-admin-global-hint">
              Vista global del sistema. Esta consulta no depende del cliente seleccionado.
            </div>
          )}
        </div>

        {!isGlobalAdminTab(adminTab) && adminSelectedClientName && (
          <div className="rs-admin-selected-client">
            Cliente actual: <strong>{adminSelectedClientName}</strong>
          </div>
        )}

        <div className="rs-admin-tab-groups">
          {isSystemAdmin && (
            <div className="rs-admin-tab-group">
              <div className="rs-admin-tab-group-label">Catálogo global</div>
              <div className="rs-admin-tabs">
                <button
                  type="button"
                  className={`rs-admin-tab ${adminTab === "global-users" ? "active" : ""}`}
                  onClick={() => setAdminTab("global-users")}
                >
                  Usuarios (global)
                </button>

                <button
                  type="button"
                  className={`rs-admin-tab ${adminTab === "global-applications" ? "active" : ""}`}
                  onClick={() => setAdminTab("global-applications")}
                >
                  Aplicaciones
                </button>

                <button
                  type="button"
                  className={`rs-admin-tab ${adminTab === "global-clients" ? "active" : ""}`}
                  onClick={() => setAdminTab("global-clients")}
                >
                  Clientes
                </button>
              </div>
            </div>
          )}

          <div className="rs-admin-tab-group">
            <div className="rs-admin-tab-group-label">Operación por cliente</div>
            <div className="rs-admin-tabs">
              <button
                type="button"
                className={`rs-admin-tab ${adminTab === "users" ? "active" : ""}`}
                onClick={() => setAdminTab("users")}
              >
                Usuarios
              </button>

              <button
                type="button"
                className={`rs-admin-tab ${adminTab === "subscriptions" ? "active" : ""}`}
                onClick={() => setAdminTab("subscriptions")}
              >
                Suscripciones
              </button>

              <button
                type="button"
                className={`rs-admin-tab ${adminTab === "permissions" ? "active" : ""}`}
                onClick={() => setAdminTab("permissions")}
              >
                Permisos
              </button>
            </div>
          </div>
        </div>

        <div className="rs-admin-actions-toolbar">
          {adminTab === "global-users" && isSystemAdmin && (
            <button
              type="button"
              className="button button-primary"
              onClick={() => openAdminEditor("global-user", "create")}
            >
              + Nuevo usuario global
            </button>
          )}

          {adminTab === "global-applications" && isSystemAdmin && (
            <button
              type="button"
              className="button button-primary"
              onClick={() => openAdminEditor("global-application", "create")}
            >
              + Nueva aplicación
            </button>
          )}

          {adminTab === "global-clients" && isSystemAdmin && (
            <button
              type="button"
              className="button button-primary"
              onClick={() => openAdminEditor("global-client", "create")}
            >
              + Nuevo cliente
            </button>
          )}

          {adminTab === "subscriptions" && isSystemAdmin && (
            <button
              type="button"
              className="button button-primary"
              onClick={() => openAdminEditor("subscription", "create")}
              disabled={!adminSelectedClientId}
            >
              + Nueva suscripción
            </button>
          )}

          {adminTab === "permissions" && (
            <button
              type="button"
              className="button button-primary"
              onClick={() => openAdminEditor("permission", "create")}
              disabled={!adminSelectedClientId}
            >
              + Nuevo permiso
            </button>
          )}
        </div>

        <div className="rs-admin-content">
          {adminActionMsg && !adminEditorOpen && (
            <div className={`alert ${adminActionMsgType}`}>
              {adminActionMsg}
            </div>
          )}

          {adminLoadingData ? (
            <div className="rs-admin-loading">
              Cargando datos administrativos...
            </div>
          ) : (
            <>
              {adminTab === "global-users" && (
                <div className="rs-admin-table-wrap">
                  {adminGlobalUsers.length === 0 ? (
                    <div className="empty-state rs-admin-empty">
                      <p className="empty-state-text">No hay usuarios en el catálogo global.</p>
                    </div>
                  ) : (
                    <table className="rs-admin-table">
                      <thead>
                        <tr>
                          <th>ID</th>
                          <th>Usuario</th>
                          <th>Email</th>
                          <th>System Admin</th>
                          <th>Clientes</th>
                          <th>Permisos</th>
                          <th>Acciones</th>
                        </tr>
                      </thead>
                      <tbody>
                        {adminGlobalUsers.map((row) => (
                          <tr key={`global-user-${row.user_id}`}>
                            <td>{row.user_id}</td>
                            <td>{row.username}</td>
                            <td>{row.email || "—"}</td>
                            <td>{row.is_system_admin ? "Sí" : "No"}</td>
                            <td>{row.clients_count ?? 0}</td>
                            <td>{row.permissions_count ?? 0}</td>
                            <td>
                              {isSystemAdmin ? (
                                <button
                                  type="button"
                                  className="rs-admin-row-action"
                                  onClick={() => openAdminEditor("global-user", "edit", row)}
                                >
                                  Modificar
                                </button>
                              ) : (
                                "—"
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  )}
                </div>
              )}

              {adminTab === "global-applications" && (
                <div className="rs-admin-table-wrap">
                  {adminGlobalApplications.length === 0 ? (
                    <div className="empty-state rs-admin-empty">
                      <p className="empty-state-text">No hay aplicaciones en el catálogo global.</p>
                    </div>
                  ) : (
                    <table className="rs-admin-table">
                      <thead>
                        <tr>
                          <th>ID</th>
                          <th>Aplicación</th>
                          <th>Slug</th>
                          <th>Launch mode</th>
                          <th>Descripción</th>
                          <th>Acciones</th>
                        </tr>
                      </thead>
                      <tbody>
                        {adminGlobalApplications.map((row) => (
                          <tr key={`global-app-${row.app_id || row.id}`}>
                            <td>{row.app_id || row.id}</td>
                            <td>{row.app_name || row.name}</td>
                            <td>{row.slug || "—"}</td>
                            <td>{row.launch_mode || "—"}</td>
                            <td>{row.description || "—"}</td>
                            <td>
                              {isSystemAdmin ? (
                                <button
                                  type="button"
                                  className="rs-admin-row-action"
                                  onClick={() =>
                                    openAdminEditor("global-application", "edit", {
                                      app_id: row.app_id || row.id,
                                      app_name: row.app_name || row.name,
                                      slug: row.slug || "",
                                      internal_url: row.internal_url || "",
                                      public_url: row.public_url || "",
                                      entry_path: row.entry_path || "/",
                                      health_path: row.health_path || "/health",
                                      launch_mode: row.launch_mode || "dynamic_proxy",
                                      description: row.description || "",
                                      is_enabled:
                                        row.is_enabled !== undefined
                                          ? Boolean(row.is_enabled)
                                          : true,
                                    })
                                  }
                                >
                                  Modificar
                                </button>
                              ) : (
                                "—"
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  )}
                </div>
              )}

              {adminTab === "global-clients" && (
                <div className="rs-admin-table-wrap">
                  {adminGlobalClients.length === 0 ? (
                    <div className="empty-state rs-admin-empty">
                      <p className="empty-state-text">No hay clientes en el catálogo global.</p>
                    </div>
                  ) : (
                    <table className="rs-admin-table">
                      <thead>
                        <tr>
                          <th>ID</th>
                          <th>Cliente</th>
                          <th>Membresías activas</th>
                          <th>Suscripciones</th>
                          <th>Suscripciones activas</th>
                          <th>Acciones</th>
                        </tr>
                      </thead>
                      <tbody>
                        {adminGlobalClients.map((row) => (
                          <tr key={`global-client-${row.client_id}`}>
                            <td>{row.client_id}</td>
                            <td>{row.client_name}</td>
                            <td>{row.active_memberships ?? 0}</td>
                            <td>{row.subscriptions_count ?? 0}</td>
                            <td>{row.active_subscriptions_count ?? 0}</td>
                            <td>
                              {isSystemAdmin ? (
                                <button
                                  type="button"
                                  className="rs-admin-row-action"
                                  onClick={() => openAdminEditor("global-client", "edit", row)}
                                >
                                  Modificar
                                </button>
                              ) : (
                                "—"
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  )}
                </div>
              )}

              {adminTab === "users" && (
                <div className="rs-admin-table-wrap">
                  {adminUsers.length === 0 ? (
                    <div className="empty-state rs-admin-empty">
                      <p className="empty-state-text">No hay usuarios para este cliente.</p>
                    </div>
                  ) : (
                    <table className="rs-admin-table">
                      <thead>
                        <tr>
                          <th>ID</th>
                          <th>Usuario</th>
                          <th>Email</th>
                          <th>Membresía</th>
                        </tr>
                      </thead>
                      <tbody>
                        {adminUsers.map((row) => (
                          <tr key={`${row.user_id}-${row.username}`}>
                            <td>{row.user_id}</td>
                            <td>{row.username}</td>
                            <td>{row.email || "—"}</td>
                            <td>{row.membership_status || "—"}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  )}
                </div>
              )}

              {adminTab === "subscriptions" && (
                <div className="rs-admin-table-wrap">
                  {adminSubscriptions.length === 0 ? (
                    <div className="empty-state rs-admin-empty">
                      <p className="empty-state-text">No hay suscripciones para este cliente.</p>
                    </div>
                  ) : (
                    <table className="rs-admin-table">
                      <thead>
                        <tr>
                          <th>ID</th>
                          <th>App ID</th>
                          <th>Aplicación</th>
                          <th>Status</th>
                          <th>Habilitada</th>
                          <th>Inicio</th>
                          <th>Fin</th>
                          <th>Acciones</th>
                        </tr>
                      </thead>
                      <tbody>
                        {adminSubscriptions.map((row) => (
                          <tr key={`${row.subscription_id}-${row.app_id}`}>
                            <td>{row.subscription_id}</td>
                            <td>{row.app_id}</td>
                            <td>{row.app_name}</td>
                            <td>{row.status || "—"}</td>
                            <td>{row.is_enabled ? "Sí" : "No"}</td>
                            <td>{row.start_date || "—"}</td>
                            <td>{row.end_date || "—"}</td>
                            <td>
                              {isSystemAdmin ? (
                                <button
                                  type="button"
                                  className="rs-admin-row-action"
                                  onClick={() => openAdminEditor("subscription", "edit", row)}
                                >
                                  Modificar
                                </button>
                              ) : (
                                "—"
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  )}
                </div>
              )}

              {adminTab === "permissions" && (
                <div className="rs-admin-table-wrap">
                  {adminPermissions.length === 0 ? (
                    <div className="empty-state rs-admin-empty">
                      <p className="empty-state-text">No hay permisos para este cliente.</p>
                    </div>
                  ) : (
                    <table className="rs-admin-table">
                      <thead>
                        <tr>
                          <th>ID</th>
                          <th>User ID</th>
                          <th>Usuario</th>
                          <th>App ID</th>
                          <th>Aplicación</th>
                          <th>Rol</th>
                          <th>Cliente</th>
                          <th>Acciones</th>
                        </tr>
                      </thead>
                      <tbody>
                        {adminPermissions.map((row) => (
                          <tr key={`permission-${row.permission_id || row.id}`}>
                            <td>{row.permission_id || row.id}</td>
                            <td>{row.user_id || "—"}</td>
                            <td>{row.username || "—"}</td>
                            <td>{row.app_id || "—"}</td>
                            <td>{row.app_name || "—"}</td>
                            <td>{row.role || "—"}</td>
                            <td>{row.client_name || "—"}</td>
                            <td>
                              <button
                                type="button"
                                className="rs-admin-row-action"
                                onClick={() =>
                                  openAdminEditor("permission", "edit", {
                                    permission_id: row.permission_id || row.id,
                                    user_id: row.user_id || "",
                                    username: row.username || "",
                                    client_id: row.client_id || "",
                                    client_name: row.client_name || "",
                                    app_id: row.app_id || "",
                                    app_name: row.app_name || "",
                                    role: row.role || "member",
                                  })
                                }
                              >
                                Modificar
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  )}
                </div>
              )}
            </>
          )}
        </div>

        <AdminEditorModal
          adminEditorOpen={adminEditorOpen}
          closeAdminEditor={closeAdminEditor}
          adminEditorType={adminEditorType}
          adminEditorMode={adminEditorMode}
          adminActionMsg={adminActionMsg}
          adminActionMsgType={adminActionMsgType}
          adminActionLoading={adminActionLoading}
          adminCreateUserForm={adminCreateUserForm}
          setAdminCreateUserForm={setAdminCreateUserForm}
          adminCreateClientForm={adminCreateClientForm}
          setAdminCreateClientForm={setAdminCreateClientForm}
          adminApplicationForm={adminApplicationForm}
          setAdminApplicationForm={setAdminApplicationForm}
          adminSubscriptionForm={adminSubscriptionForm}
          setAdminSubscriptionForm={setAdminSubscriptionForm}
          adminPermissionForm={adminPermissionForm}
          setAdminPermissionForm={setAdminPermissionForm}
          adminClients={adminClients}
          adminAppsCatalog={adminAppsCatalog}
          adminPermissionUsers={adminPermissionUsers}
          adminPermissionApps={adminPermissionApps}
          handleCreateGlobalUser={handleCreateGlobalUser}
          handleUpdateGlobalUser={handleUpdateGlobalUser}
          handleCreateGlobalClient={handleCreateGlobalClient}
          handleUpdateGlobalClient={handleUpdateGlobalClient}
          handleCreateGlobalApplication={handleCreateGlobalApplication}
          handleUpdateGlobalApplication={handleUpdateGlobalApplication}
          handleCreateSubscription={handleCreateSubscription}
          handleUpdateSubscription={handleUpdateSubscription}
          handleCreatePermission={handleCreatePermission}
          handleUpdatePermissionRole={handleUpdatePermissionRole}
        />

        <div className="rs-admin-footer">
          <button
            type="button"
            className="button button-secondary"
            onClick={reloadCurrentAdminTab}
            disabled={(!isGlobalAdminTab(adminTab) && !adminSelectedClientId) || adminLoadingData}
          >
            {adminLoadingData ? "Cargando..." : "↻ Recargar pestaña"}
          </button>

          <button
            type="button"
            className="button button-primary"
            onClick={() => closeAdminModal()}
          >
            Cerrar
          </button>
        </div>
      </div>
    </div>
  );
}