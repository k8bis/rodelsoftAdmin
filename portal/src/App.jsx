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

  // Fuente maestra de apps + permisos desde App1
  const [rawApps, setRawApps] = useState([]);

  // selección por app -> cliente
  const [selectedClientByApp, setSelectedClientByApp] = useState({});

  // Lee mensajes enviados por launch-service (?msg=...)
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const incomingMsg = params.get("msg");

    if (incomingMsg) {
      setMsg(incomingMsg);
      setMsgType("info");

      // limpia la URL para no dejar el mensaje pegado
      window.history.replaceState({}, document.title, window.location.pathname);
    }
  }, []);

  // 🔥 NUEVO: al cargar el portal, intenta restaurar sesión desde cookie
  useEffect(() => {
    restoreSession();
  }, []);

  const restoreSession = async () => {
    setInitializing(true);

    try {
      const r = await fetch("/app1/my/apps", {
        method: "GET",
        credentials: "include",
        cache: "no-store",
      });

      if (!r.ok) {
        // Si no hay sesión válida, simplemente mostramos login
        setAuthed(false);
        setRawApps([]);
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
          if (meData?.username) {
            setUser(meData.username);
          }
        }
      } catch {
        // Si falla /app1/me, no bloqueamos la UI
      }
    } catch (e) {
      console.error("Error restaurando sesión:", e);
      setAuthed(false);
      setRawApps([]);
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

  // Si ya hay apps, autoselecciona el primer cliente por app
  useEffect(() => {
    const next = { ...selectedClientByApp };

    rawApps.forEach((app) => {
      if (!app?.clients?.length) return;
      if (!next[app.app_id]) next[app.app_id] = app.clients[0].id;
    });

    setSelectedClientByApp(next);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [JSON.stringify(rawApps)]);

  const enterApp = (app) => {
    const app_id = app.app_id;
    const client_id = selectedClientByApp[app_id];

    if (!client_id) {
      setMsg(`Selecciona un cliente para app_id=${app_id}.`);
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
        <header className="app-header">
          <div className="logo-section">
            <picture>
              <source srcSet="/logos/rodelsoft-monogram-hex.svg" type="image/svg+xml" />
              <img src="/logos/rodelsoft-monogram-hex.png" alt="RodelSoft" className="logo" />
            </picture>
            <h1 className="title">Portal RodelSoft</h1>
          </div>
          <div></div>
          <div></div>
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
      <header className="app-header">
        <div className="logo-section">
          <picture>
            <source srcSet="/logos/rodelsoft-monogram-hex.svg" type="image/svg+xml" />
            <img src="/logos/rodelsoft-monogram-hex.png" alt="RodelSoft" className="logo" />
          </picture>
          <h1 className="title">Portal RodelSoft</h1>
        </div>
        <div></div>
        <div className="user-info">
          {authed && (
            <div className="user-info">
              <span>👤 {username}</span>
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
            <div className="toolbar">
              <button className="button button-secondary" onClick={fetchMyApps}>
                🔄 Refrescar aplicaciones
              </button>
              <div className="toolbar-spacer" />
              <button className="button button-danger" onClick={logout}>
                ← Salir
              </button>
            </div>

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
                      <div className="app-header">
                        <h3 className="app-title">{app.app}</h3>
                        <span className="app-badge">
                          {app.clients?.length || 0} cliente{app.clients?.length !== 1 ? "s" : ""}
                        </span>
                      </div>

                      {app.description && (
                        <p className="app-description">{app.description}</p>
                      )}

                      {app.clients && app.clients.length > 0 && (
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
                                {client.name}
                              </option>
                            ))}
                          </select>
                        </div>
                      )}

                      <button
                        className="button button-primary button-fullwidth"
                        onClick={() => enterApp(app)}
                      >
                        ▶ Entrar a {app.app}
                      </button>
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