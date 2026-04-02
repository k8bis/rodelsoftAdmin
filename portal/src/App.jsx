import React, { useEffect, useState } from "react";
import "./App.css";

export default function App() {
  const [username, setUser] = useState("admin");
  const [password, setPass] = useState("adminpass");
  const [authed, setAuthed] = useState(false);
  const [msg, setMsg] = useState("");
  const [loading, setLoading] = useState(false);
  const [initializing, setInitializing] = useState(true);
  const [msgType, setMsgType] = useState("info"); // info, success, error, warning
  const [userMenuOpen, setUserMenuOpen] = useState(false);

  // Fuente maestra de apps + permisos desde App1
  const [rawApps, setRawApps] = useState([]);

  // selección por app -> cliente
  const [selectedClientByApp, setSelectedClientByApp] = useState({});

  // Lee mensajes enviados por launch-service (?msg=...)
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const incomingMsg = params.get("msg");
    const incomingMsgType = params.get("msg_type");

    if (incomingMsg) {
      const allowedMsgTypes = ["info", "success", "warning", "error"];
      const safeMsgType = allowedMsgTypes.includes(incomingMsgType) ? incomingMsgType : "info";

      setMsg(incomingMsg);
      setMsgType(safeMsgType);
      window.history.replaceState({}, document.title, window.location.pathname);
    }
  }, []);

  // 🔥 NUEVO: al cargar el portal, intenta restaurar sesión desde cookie
  useEffect(() => {
    restoreSession();
  }, []);

  useEffect(() => {
    const handlePageShow = () => {
      restoreSession();
    };

    window.addEventListener("pageshow", handlePageShow);

    return () => {
      window.removeEventListener("pageshow", handlePageShow);
    };
  }, []);

  useEffect(() => {
    const handleClickOutside = () => {
      setUserMenuOpen(false);
    };

    if (userMenuOpen) {
      document.addEventListener("click", handleClickOutside);
    }

    return () => {
      document.removeEventListener("click", handleClickOutside);
    };
  }, [userMenuOpen]);

  const restoreSession = async () => {
    setInitializing(true);

    try {
      const r = await fetch("/app1/my/apps", {
        method: "GET",
        credentials: "include",
        cache: "no-store",
      });

      if (!r.ok) {
        setAuthed(false);
        setRawApps([]);
        setSelectedClientByApp({});
        setMsg("");
        setMsgType("info");
        return;
      }

      const data = await r.json();

      setRawApps(Array.isArray(data) ? data : []);
      setAuthed(true);

      // Opcional: intentar obtener usuario real
      try {
        const me = await fetch("/app1/me", {
          method: "GET",
          credentials: "include",
          cache: "no-store",
        });

        if (me.ok) {
          const meData = await me.json();
          if (meData?.user) {
            setUser(meData.user);
          }
        }
      } catch {
        // Si falla /app1/me, no bloqueamos la UI
      }
    } catch (e) {
      console.error("Error restaurando sesión:", e);
      setAuthed(false);
      setRawApps([]);
      setSelectedClientByApp({});
      setMsg("");
      setMsgType("info");
    } finally {
      setInitializing(false);
    }
  };

  const login = async () => {
    setMsg("");
    setLoading(true);

    try {
      const r = await fetch("/app1/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ username, password }),
      });

      if (!r.ok) {
        const t = await r.text();
        setMsg(`Login falló (${r.status}): ${t}`);
        setMsgType("error");
        setAuthed(false);
        return;
      }

      setMsg("Sesión iniciada ✅");
      setMsgType("success");

      // 🔥 IMPORTANTE: después del login, restaurar sesión completa
      await restoreSession();
    } catch (e) {
      setMsg(`Error de red: ${String(e)}`);
      setMsgType("error");
    } finally {
      setLoading(false);
    }
  };

  const logout = async () => {
    setMsg("");
    try {
      await fetch("/app1/logout", {
        method: "POST",
        credentials: "include",
      });
    } catch {}

    setAuthed(false);
    setRawApps([]);
    setSelectedClientByApp({});
    setMsg("");
    setMsgType("info");
    setUserMenuOpen(false);
  };

  const fetchMyApps = async () => {
    setMsg("");

    try {
      const r = await fetch("/app1/my/apps", {
        method: "GET",
        credentials: "include",
        cache: "no-store",
      });

      if (!r.ok) {
        const t = await r.text();
        setMsg(`/app1/my/apps falló (${r.status}): ${t}`);
        setMsgType("error");
        setRawApps([]);
        setAuthed(false);
        return;
      }

      const data = await r.json();
      setRawApps(Array.isArray(data) ? data : []);
      setAuthed(true);
    } catch (e) {
      setMsg(`Error /app1/my/apps: ${String(e)}`);
      setMsgType("error");
      setRawApps([]);
      setAuthed(false);
    }
  };

  // Si ya hay apps, autoselecciona el primer cliente accesible por app;
  // si no hay ninguno accesible, toma el primero.
  useEffect(() => {
    const next = { ...selectedClientByApp };

    rawApps.forEach((app) => {
      if (!app?.clients?.length) return;
      if (!next[app.app_id]) {
        const firstAccessible = app.clients.find((c) => c.is_accessible);
        next[app.app_id] = (firstAccessible || app.clients[0]).id;
      }
    });

    setSelectedClientByApp(next);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [JSON.stringify(rawApps)]);

  const getSelectedClient = (app) => {
    const selectedId = selectedClientByApp[app.app_id];
    return app.clients?.find((c) => c.id === Number(selectedId)) || app.clients?.[0] || null;
  };

  const getClientStatusLabel = (client) => {
    if (!client) return "";

    if (client.is_expiring_soon) return "VENCE PRONTO";

    switch (client.subscription_status) {
      case "active":
        return "ACTIVA";
      case "trial":
        return "TRIAL";
      case "expired":
        return "VENCIDA";
      case "suspended":
        return "SUSPENDIDA";
      case "missing":
        return "SIN SUSCRIPCIÓN";
      default:
        return (client.subscription_status || "SIN ESTADO").toUpperCase();
    }
  };

  const getClientStatusText = (client) => {
    if (!client) return "";

    if (client.is_accessible && client.is_expiring_soon) {
      return `⚠️ Suscripción por vencer${client.subscription_end_date ? ` (${client.subscription_end_date})` : ""}`;
    }

    if (client.is_accessible && client.subscription_status === "active") {
      return "✅ Suscripción activa";
    }

    if (client.is_accessible && client.subscription_status === "trial") {
      return "🟡 Cliente en trial";
    }

    if (!client.is_accessible && client.subscription_status === "expired") {
      return `⛔ Suscripción vencida${client.subscription_end_date ? ` (${client.subscription_end_date})` : ""}`;
    }

    if (!client.is_accessible && client.subscription_status === "suspended") {
      return "⛔ Suscripción suspendida";
    }

    if (!client.is_accessible && client.subscription_status === "missing") {
      return "⛔ Cliente sin suscripción configurada";
    }

    return `ℹ️ Estado: ${client.subscription_status || "desconocido"}`;
  };

  const enterApp = (app) => {
    const app_id = app.app_id;
    const client = getSelectedClient(app);
    const client_id = client?.id;

    if (!client_id) {
      setMsg(`Selecciona un cliente para app_id=${app_id}.`);
      setMsgType("warning");
      return;
    }

    if (!client.is_accessible) {
      setMsg(`No puedes ingresar a ${app.app} con el cliente "${client.name}" porque su suscripción no está activa.`);
      setMsgType("warning");
      return;
    }

    // FASE 2: usar launch-service
    window.location.href = `/launch?app_id=${app_id}&client_id=${client_id}`;
  };

  // 🔥 NUEVO: mientras valida sesión, no mostrar login prematuramente
  if (initializing) {
    return (
      <div className="app-container">
        <header className="rs-shell-header">
          <div className="rs-shell-left">
            <picture>
              <source srcSet="/logos/rodelsoft-monogram-hex.svg" type="image/svg+xml" />
              <img src="/logos/rodelsoft-monogram-hex.png" alt="RodelSoft" className="rs-shell-logo" />
            </picture>
            <div className="rs-shell-brand">
              <h1 className="rs-shell-title">Portal RodelSoft</h1>
              <p className="rs-shell-subtitle">Acceso central a tus aplicaciones</p>
            </div>
          </div>
          <div className="rs-shell-right"></div>
        </header>

        <main className="main-content">
          <div className="login-container">
            <div className="login-card">
              <div className="login-header">
                <h2 className="login-title">Cargando sesión...</h2>
                <p className="login-subtitle">Validando acceso a tus aplicaciones</p>
              </div>
            </div>
          </div>
        </main>

        <footer className="app-footer">
          <p className="app-footer-text">© 2026 RodelSoft. Todos los derechos reservados.</p>
        </footer>
      </div>
    );
  }

  return (
    <div className="app-container">
      {/* Header */}
      <header className="rs-shell-header">
        <div className="rs-shell-left">
          <picture>
            <source srcSet="/logos/rodelsoft-monogram-hex.svg" type="image/svg+xml" />
            <img src="/logos/rodelsoft-monogram-hex.png" alt="RodelSoft" className="rs-shell-logo" />
          </picture>
          <div className="rs-shell-brand">
            <h1 className="rs-shell-title">Portal RodelSoft</h1>
            <p className="rs-shell-subtitle">Acceso central a tus aplicaciones</p>
          </div>
        </div>

        <div className="rs-shell-right">
          {authed && (
            <div className="rs-user-menu">
              <button
                className="rs-user-trigger"
                onClick={(e) => {
                  e.stopPropagation();
                  setUserMenuOpen((prev) => !prev);
                }}
                type="button"
              >
                👤 {username}
              </button>

              {userMenuOpen && (
                <div
                  className="rs-user-dropdown"
                  onClick={(e) => e.stopPropagation()}
                >
                  <button
                    className="rs-user-dropdown-item"
                    onClick={() => {
                      setUserMenuOpen(false);
                      fetchMyApps();
                    }}
                  >
                    🔄 Refrescar aplicaciones
                  </button>
                  <button
                    className="rs-user-dropdown-item rs-user-dropdown-item-danger"
                    onClick={() => {
                      setUserMenuOpen(false);
                      logout();
                    }}
                  >
                    Cerrar sesión
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      </header>

      {/* Main Content */}
      <main className="main-content">
        {msg && (
          <div className={`alert ${msgType}`}>
            {msg}
          </div>
        )}

        {!authed ? (
          /* Login Panel */
          <div className="login-container">
            <div className="login-card">
              <div className="login-header">
                <h2 className="login-title">Iniciar sesión</h2>
                <p className="login-subtitle">Accede a tus aplicaciones</p>
              </div>

              <div className="form-group">
                <label className="label">Usuario</label>
                <input
                  className="input"
                  type="text"
                  value={username}
                  onChange={(e) => setUser(e.target.value)}
                  placeholder="Ingresa tu usuario"
                  disabled={loading}
                />
              </div>

              <div className="form-group">
                <label className="label">Contraseña</label>
                <input
                  className="input"
                  type="password"
                  value={password}
                  onChange={(e) => setPass(e.target.value)}
                  placeholder="Ingresa tu contraseña"
                  disabled={loading}
                />
              </div>

              <button
                className={`button button-primary${loading ? " button-loading" : ""}`}
                onClick={login}
                disabled={loading}
              >
                {loading ? "Iniciando..." : "Iniciar sesión"}
              </button>
            </div>
          </div>
        ) : (
          /* Apps Panel */
          <>
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
                        const selectedClient = getSelectedClient(app);
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
          </>
        )}
      </main>

      {/* Footer */}
      <footer className="app-footer">
        <p className="app-footer-text">© 2026 RodelSoft. Todos los derechos reservados.</p>
      </footer>
    </div>
  );
}