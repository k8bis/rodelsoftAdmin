// portal/src/components/AdminEditorModal.jsx
import React from "react";

export default function AdminEditorModal({
  adminEditorOpen,
  closeAdminEditor,
  adminEditorType,
  adminEditorMode,
  adminActionMsg,
  adminActionMsgType,
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
  adminClients,
  adminAppsCatalog,
  adminPermissionUsers = [],
  adminPermissionApps = [],
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
}) {
  if (!adminEditorOpen) return null;

  const isPermissionCreate =
    adminEditorType === "permission" && adminEditorMode === "create";

  return (
    <div className="rs-admin-editor-overlay" onClick={closeAdminEditor}>
      <div
        className="rs-admin-editor-modal"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="rs-admin-editor-header">
          <div>
            <h3 className="rs-admin-editor-title">
              {adminEditorType === "global-user" &&
                (adminEditorMode === "edit"
                  ? "Modificar usuario global"
                  : "Nuevo usuario global")}
              {adminEditorType === "global-client" &&
                (adminEditorMode === "edit"
                  ? "Modificar cliente"
                  : "Nuevo cliente")}
              {adminEditorType === "global-application" &&
                (adminEditorMode === "edit"
                  ? "Modificar aplicación"
                  : "Nueva aplicación")}
              {adminEditorType === "subscription" &&
                (adminEditorMode === "edit"
                  ? "Modificar suscripción"
                  : "Nueva suscripción")}
              {adminEditorType === "permission" &&
                (adminEditorMode === "edit"
                  ? "Modificar permiso"
                  : "Nuevo permiso")}
            </h3>
            <p className="rs-admin-editor-subtitle">
              {adminEditorType === "global-user" &&
                (adminEditorMode === "edit"
                  ? "Actualizar datos del usuario global"
                  : "Registrar usuario del catálogo global")}
              {adminEditorType === "global-client" &&
                (adminEditorMode === "edit"
                  ? "Actualizar nombre del cliente global"
                  : "Registrar nuevo cliente en el sistema")}
              {adminEditorType === "global-application" &&
                (adminEditorMode === "edit"
                  ? "Actualizar datos de la aplicación"
                  : "Registrar nueva aplicación en el catálogo")}
              {adminEditorType === "subscription" &&
                (adminEditorMode === "edit"
                  ? "Actualizar contratación de app para cliente"
                  : "Registrar suscripción para cliente")}
              {adminEditorType === "permission" &&
                (adminEditorMode === "edit"
                  ? "Actualizar rol del permiso existente"
                  : "Asignar permiso por cliente y aplicación")}
            </p>
          </div>

          <button
            type="button"
            className="rs-admin-close"
            onClick={closeAdminEditor}
          >
            ✕
          </button>
        </div>

        <div className="rs-admin-editor-body">
          {adminActionMsg && (
            <div className={`alert ${adminActionMsgType}`}>
              {adminActionMsg}
            </div>
          )}

          {/* GLOBAL USER */}
          {adminEditorType === "global-user" && (
            <div className="rs-admin-editor-form">
              {adminEditorMode === "edit" && (
                <div className="form-group">
                  <label className="label">User ID</label>
                  <input
                    className="input"
                    type="text"
                    value={adminCreateUserForm.user_id || ""}
                    disabled
                  />
                </div>
              )}

              <div className="form-group">
                <label className="label">Usuario</label>
                <input
                  className="input"
                  type="text"
                  value={adminCreateUserForm.username || ""}
                  onChange={(e) =>
                    setAdminCreateUserForm((prev) => ({
                      ...prev,
                      username: e.target.value,
                    }))
                  }
                />
              </div>

              {adminEditorMode === "create" && (
                <div className="form-group">
                  <label className="label">Password inicial</label>
                  <input
                    className="input"
                    type="password"
                    value={adminCreateUserForm.password || ""}
                    onChange={(e) =>
                      setAdminCreateUserForm((prev) => ({
                        ...prev,
                        password: e.target.value,
                      }))
                    }
                  />
                </div>
              )}

              <div className="form-group">
                <label className="label">Email</label>
                <input
                  className="input"
                  type="email"
                  value={adminCreateUserForm.email || ""}
                  onChange={(e) =>
                    setAdminCreateUserForm((prev) => ({
                      ...prev,
                      email: e.target.value,
                    }))
                  }
                />
              </div>

              <div className="form-group">
                <label className="label">System Admin</label>
                <select
                  className="select"
                  value={adminCreateUserForm.is_system_admin ? "1" : "0"}
                  onChange={(e) =>
                    setAdminCreateUserForm((prev) => ({
                      ...prev,
                      is_system_admin: e.target.value === "1",
                    }))
                  }
                >
                  <option value="0">No</option>
                  <option value="1">Sí</option>
                </select>
              </div>
            </div>
          )}

          {/* GLOBAL CLIENT */}
          {adminEditorType === "global-client" && (
            <div className="rs-admin-editor-form">
              {adminEditorMode === "edit" && (
                <div className="form-group">
                  <label className="label">Client ID</label>
                  <input
                    className="input"
                    type="text"
                    value={adminCreateClientForm.client_id || ""}
                    disabled
                  />
                </div>
              )}

              <div className="form-group">
                <label className="label">Cliente</label>
                <input
                  className="input"
                  type="text"
                  value={adminCreateClientForm.client_name || ""}
                  onChange={(e) =>
                    setAdminCreateClientForm((prev) => ({
                      ...prev,
                      client_name: e.target.value,
                    }))
                  }
                />
              </div>
            </div>
          )}

          {/* GLOBAL APPLICATION */}
          {adminEditorType === "global-application" && (
            <div className="rs-admin-editor-form">
              {adminEditorMode === "edit" && (
                <div className="form-group">
                  <label className="label">App ID</label>
                  <input
                    className="input"
                    type="text"
                    value={adminApplicationForm.app_id || ""}
                    disabled
                  />
                </div>
              )}

              <div className="form-group">
                <label className="label">Aplicación</label>
                <input
                  className="input"
                  type="text"
                  value={adminApplicationForm.app_name || ""}
                  onChange={(e) =>
                    setAdminApplicationForm((prev) => ({
                      ...prev,
                      app_name: e.target.value,
                    }))
                  }
                />
              </div>

              <div className="form-group">
                <label className="label">Slug</label>
                <input
                  className="input"
                  type="text"
                  value={adminApplicationForm.slug || ""}
                  onChange={(e) =>
                    setAdminApplicationForm((prev) => ({
                      ...prev,
                      slug: e.target.value,
                    }))
                  }
                />
              </div>

              <div className="form-group">
                <label className="label">Internal URL</label>
                <input
                  className="input"
                  type="text"
                  value={adminApplicationForm.internal_url || ""}
                  onChange={(e) =>
                    setAdminApplicationForm((prev) => ({
                      ...prev,
                      internal_url: e.target.value,
                    }))
                  }
                />
              </div>

              <div className="form-group">
                <label className="label">Public URL</label>
                <input
                  className="input"
                  type="text"
                  value={adminApplicationForm.public_url || ""}
                  onChange={(e) =>
                    setAdminApplicationForm((prev) => ({
                      ...prev,
                      public_url: e.target.value,
                    }))
                  }
                />
              </div>

              <div className="form-group">
                <label className="label">Entry path</label>
                <input
                  className="input"
                  type="text"
                  value={adminApplicationForm.entry_path || ""}
                  onChange={(e) =>
                    setAdminApplicationForm((prev) => ({
                      ...prev,
                      entry_path: e.target.value,
                    }))
                  }
                />
              </div>

              <div className="form-group">
                <label className="label">Health path</label>
                <input
                  className="input"
                  type="text"
                  value={adminApplicationForm.health_path || ""}
                  onChange={(e) =>
                    setAdminApplicationForm((prev) => ({
                      ...prev,
                      health_path: e.target.value,
                    }))
                  }
                />
              </div>

              <div className="form-group">
                <label className="label">Launch mode</label>
                <select
                  className="select"
                  value={adminApplicationForm.launch_mode || "dynamic_proxy"}
                  onChange={(e) =>
                    setAdminApplicationForm((prev) => ({
                      ...prev,
                      launch_mode: e.target.value,
                    }))
                  }
                >
                  <option value="dynamic_proxy">dynamic_proxy</option>
                  <option value="internal_redirect">internal_redirect</option>
                  <option value="external_link">external_link</option>
                </select>
              </div>

              <div className="form-group">
                <label className="label">Descripción</label>
                <textarea
                  className="input"
                  rows="3"
                  value={adminApplicationForm.description || ""}
                  onChange={(e) =>
                    setAdminApplicationForm((prev) => ({
                      ...prev,
                      description: e.target.value,
                    }))
                  }
                />
              </div>

              <div className="form-group">
                <label className="label">Habilitada</label>
                <select
                  className="select"
                  value={adminApplicationForm.is_enabled ? "1" : "0"}
                  onChange={(e) =>
                    setAdminApplicationForm((prev) => ({
                      ...prev,
                      is_enabled: e.target.value === "1",
                    }))
                  }
                >
                  <option value="1">Sí</option>
                  <option value="0">No</option>
                </select>
              </div>
            </div>
          )}

          {/* SUBSCRIPTION */}
          {adminEditorType === "subscription" && (
            <div className="rs-admin-editor-form">
              <div className="form-group">
                <label className="label">Cliente</label>
                <select
                  className="select"
                  value={adminSubscriptionForm.client_id || ""}
                  onChange={(e) =>
                    setAdminSubscriptionForm((prev) => ({
                      ...prev,
                      client_id: e.target.value,
                    }))
                  }
                  disabled={adminEditorMode === "edit"}
                >
                  <option value="">Selecciona un cliente</option>
                  {adminClients.map((client) => (
                    <option key={client.client_id} value={client.client_id}>
                      {client.client_name}
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label className="label">Aplicación</label>
                <select
                  className="select"
                  value={adminSubscriptionForm.app_id || ""}
                  onChange={(e) =>
                    setAdminSubscriptionForm((prev) => ({
                      ...prev,
                      app_id: e.target.value,
                    }))
                  }
                  disabled={adminEditorMode === "edit"}
                >
                  <option value="">Selecciona una aplicación</option>
                  {adminAppsCatalog.map((app) => {
                    const appId = app.app_id ?? app.id ?? "";
                    const appName = app.app_name ?? app.name ?? `App ${appId}`;

                    return (
                      <option key={String(appId)} value={String(appId)}>
                        {appName}
                      </option>
                    );
                  })}
                </select>
              </div>

              <div className="form-group">
                <label className="label">Status</label>
                <select
                  className="select"
                  value={adminSubscriptionForm.status || "active"}
                  onChange={(e) =>
                    setAdminSubscriptionForm((prev) => ({
                      ...prev,
                      status: e.target.value,
                    }))
                  }
                >
                  <option value="active">active</option>
                  <option value="trial">trial</option>
                  <option value="suspended">suspended</option>
                  <option value="expired">expired</option>
                </select>
              </div>

              <div className="form-group">
                <label className="label">Habilitada</label>
                <select
                  className="select"
                  value={adminSubscriptionForm.is_enabled ? "1" : "0"}
                  onChange={(e) =>
                    setAdminSubscriptionForm((prev) => ({
                      ...prev,
                      is_enabled: e.target.value === "1",
                    }))
                  }
                >
                  <option value="1">Sí</option>
                  <option value="0">No</option>
                </select>
              </div>

              <div className="form-group">
                <label className="label">Inicio</label>
                <input
                  className="input"
                  type="date"
                  value={adminSubscriptionForm.start_date || ""}
                  onChange={(e) =>
                    setAdminSubscriptionForm((prev) => ({
                      ...prev,
                      start_date: e.target.value,
                    }))
                  }
                />
              </div>

              <div className="form-group">
                <label className="label">Fin</label>
                <input
                  className="input"
                  type="date"
                  value={adminSubscriptionForm.end_date || ""}
                  onChange={(e) =>
                    setAdminSubscriptionForm((prev) => ({
                      ...prev,
                      end_date: e.target.value,
                    }))
                  }
                />
              </div>
            </div>
          )}

          {/* PERMISSION */}
          {adminEditorType === "permission" && (
            <div className="rs-admin-editor-form">
              {adminEditorMode === "edit" && (
                <>
                  <div className="form-group">
                    <label className="label">Usuario</label>
                    <input
                      className="input"
                      type="text"
                      value={adminPermissionForm.username || ""}
                      disabled
                    />
                  </div>

                  <div className="form-group">
                    <label className="label">Cliente</label>
                    <select
                      className="select"
                      value={adminPermissionForm.client_id || ""}
                      disabled
                    >
                      {adminClients.map((client) => (
                        <option key={client.client_id} value={client.client_id}>
                          {client.client_name}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="form-group">
                    <label className="label">Aplicación</label>
                    <input
                      className="input"
                      type="text"
                      value={
                        adminPermissionForm.app_name ||
                        adminAppsCatalog.find(
                          (app) =>
                            String(app.app_id ?? app.id ?? "") ===
                            String(adminPermissionForm.app_id || "")
                        )?.app_name ||
                        adminAppsCatalog.find(
                          (app) =>
                            String(app.app_id ?? app.id ?? "") ===
                            String(adminPermissionForm.app_id || "")
                        )?.name ||
                        ""
                      }
                      disabled
                    />
                  </div>
                </>
              )}

              {isPermissionCreate && (
                <>
                  <div className="form-group">
                    <label className="label">Usuario</label>
                    <select
                      className="select"
                      value={adminPermissionForm.user_id || ""}
                      onChange={(e) => {
                        const selectedId = e.target.value;
                        const selectedUser =
                          adminPermissionUsers.find(
                            (row) => String(row.user_id || row.id) === String(selectedId)
                          ) || null;

                        setAdminPermissionForm((prev) => ({
                          ...prev,
                          user_id: selectedId,
                          username: selectedUser?.username || "",
                        }));
                      }}
                    >
                      <option value="">
                        {adminPermissionUsers.length
                          ? "Selecciona un usuario"
                          : "No hay usuarios disponibles"}
                      </option>
                      {adminPermissionUsers.map((user) => (
                        <option
                          key={user.user_id || user.id}
                          value={String(user.user_id || user.id)}
                        >
                          {user.username}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="form-group">
                    <label className="label">Cliente</label>
                    <select
                      className="select"
                      value={adminPermissionForm.client_id || ""}
                      disabled
                    >
                      {adminClients.map((client) => (
                        <option key={client.client_id} value={client.client_id}>
                          {client.client_name}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="form-group">
                    <label className="label">Aplicación</label>
                    <select
                      className="select"
                      value={adminPermissionForm.app_id || ""}
                      onChange={(e) => {
                        const selectedId = e.target.value;
                        const selectedApp =
                          adminPermissionApps.find(
                            (app) => String(app.app_id ?? app.id ?? "") === String(selectedId)
                          ) || null;

                        setAdminPermissionForm((prev) => ({
                          ...prev,
                          app_id: selectedId,
                          app_name:
                            selectedApp?.app_name ||
                            selectedApp?.name ||
                            "",
                        }));
                      }}
                    >
                      <option value="">
                        {adminPermissionApps.length
                          ? "Selecciona una aplicación"
                          : "No hay aplicaciones disponibles"}
                      </option>
                      {adminPermissionApps.map((app) => {
                        const appId = app.app_id ?? app.id ?? "";
                        const appName = app.app_name ?? app.name ?? `App ${appId}`;

                        return (
                          <option key={String(appId)} value={String(appId)}>
                            {appName}
                          </option>
                        );
                      })}
                    </select>
                  </div>
                </>
              )}

              <div className="form-group">
                <label className="label">Rol</label>
                <select
                  className="select"
                  value={adminPermissionForm.role || "member"}
                  onChange={(e) =>
                    setAdminPermissionForm((prev) => ({
                      ...prev,
                      role: e.target.value,
                    }))
                  }
                >
                  <option value="member">member</option>
                  <option value="app_client_admin">app_client_admin</option>
                </select>
              </div>
            </div>
          )}
        </div>

        <div className="rs-admin-editor-footer">
          <button
            type="button"
            className="button button-secondary"
            onClick={closeAdminEditor}
            disabled={adminActionLoading}
          >
            Cancelar
          </button>

          {adminEditorType === "global-user" && (
            <button
              type="button"
              className="button button-primary"
              onClick={
                adminEditorMode === "edit"
                  ? handleUpdateGlobalUser
                  : handleCreateGlobalUser
              }
              disabled={adminActionLoading}
            >
              {adminActionLoading ? "Guardando..." : "Guardar"}
            </button>
          )}

          {adminEditorType === "global-client" && (
            <button
              type="button"
              className="button button-primary"
              onClick={
                adminEditorMode === "edit"
                  ? handleUpdateGlobalClient
                  : handleCreateGlobalClient
              }
              disabled={adminActionLoading}
            >
              {adminActionLoading ? "Guardando..." : "Guardar"}
            </button>
          )}

          {adminEditorType === "global-application" && (
            <button
              type="button"
              className="button button-primary"
              onClick={
                adminEditorMode === "edit"
                  ? handleUpdateGlobalApplication
                  : handleCreateGlobalApplication
              }
              disabled={adminActionLoading}
            >
              {adminActionLoading ? "Guardando..." : "Guardar"}
            </button>
          )}

          {adminEditorType === "subscription" && (
            <button
              type="button"
              className="button button-primary"
              onClick={
                adminEditorMode === "edit"
                  ? handleUpdateSubscription
                  : handleCreateSubscription
              }
              disabled={adminActionLoading}
            >
              {adminActionLoading ? "Guardando..." : "Guardar"}
            </button>
          )}

          {adminEditorType === "permission" && (
            <button
              type="button"
              className="button button-primary"
              onClick={
                adminEditorMode === "edit"
                  ? handleUpdatePermissionRole
                  : handleCreatePermission
              }
              disabled={adminActionLoading}
            >
              {adminActionLoading ? "Guardando..." : "Guardar"}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}