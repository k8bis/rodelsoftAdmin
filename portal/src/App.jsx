import React, { useEffect, useState } from "react";

export default function App() {
  const [username, setUser] = useState("admin");
  const [password, setPass] = useState("adminpass");
  const [authed, setAuthed] = useState(false);
  const [msg, setMsg] = useState("");
  const [loading, setLoading] = useState(false);

  // Fuente maestra de apps + permisos desde App1
  const [rawApps, setRawApps] = useState([]);

  // selección por app -> cliente
  const [selectedClientByApp, setSelectedClientByApp] = useState({});

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
        setAuthed(false);
        return;
      }

      setAuthed(true);
      setMsg("Sesión iniciada ✅");
      fetchMyApps();
    } catch (e) {
      setMsg(`Error de red: ${String(e)}`);
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
  };

  const fetchMyApps = async () => {
    setMsg("");

    try {
      const r = await fetch("/app1/my/apps", {
        credentials: "include",
      });

      if (!r.ok) {
        const t = await r.text();
        setMsg(`/app1/my/apps falló (${r.status}): ${t}`);
        setRawApps([]);
        return;
      }

      const data = await r.json();
      setRawApps(Array.isArray(data) ? data : []);
    } catch (e) {
      setMsg(`Error /app1/my/apps: ${String(e)}`);
      setRawApps([]);
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
      return setMsg(`Selecciona un cliente para app_id=${app_id}.`);
    }

    // FASE 1: usar SIEMPRE el router dinámico central actual
    window.location.href = `/app/?app_id=${app_id}&client_id=${client_id}`;
  };

  return (
    <div style={{ maxWidth: 1100, margin: "32px auto", fontFamily: "system-ui, sans-serif" }}>
      <h1>Portal Global</h1>

      {msg && (
        <div
          style={{
            padding: "10px 12px",
            background: "#fff6cc",
            border: "1px solid #f2d16b",
            borderRadius: 8,
            marginBottom: 12,
          }}
        >
          {msg}
        </div>
      )}

      {!authed ? (
        <div style={{ display: "grid", gap: 8, maxWidth: 360 }}>
          <label>
            Usuario
            <input
              value={username}
              onChange={(e) => setUser(e.target.value)}
              placeholder="usuario"
            />
          </label>

          <label>
            Contraseña
            <input
              value={password}
              onChange={(e) => setPass(e.target.value)}
              type="password"
              placeholder="contraseña"
            />
          </label>

          <button onClick={login} disabled={loading}>
            {loading ? "Iniciando..." : "Iniciar sesión"}
          </button>
        </div>
      ) : (
        <>
          <div style={{ display: "flex", gap: 10, alignItems: "center", marginBottom: 12 }}>
            <button onClick={fetchMyApps}>Refrescar aplicaciones</button>
            <div style={{ marginLeft: "auto" }} />
            <button onClick={logout}>Salir</button>
          </div>

          <h2>Mis aplicaciones</h2>

          {rawApps.length === 0 ? (
            <p>No hay aplicaciones asignadas a tu usuario.</p>
          ) : (
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
              {rawApps.map((app) => (
                <div
                  key={app.app_id}
                  className="card"
                  style={{
                    border: "1px solid #ddd",
                    borderRadius: 10,
                    padding: 16,
                    background: "#fff",
                  }}
                >
                  <h3 style={{ marginTop: 0 }}>{app.app}</h3>

                  {app.description && (
                    <p style={{ color: "#555", marginTop: 0 }}>{app.description}</p>
                  )}

                  <div style={{ fontSize: 12, color: "#666", marginBottom: 10 }}>
                    <div><strong>Slug:</strong> {app.slug || "-"}</div>
                    <div><strong>Entry:</strong> {app.entry_path || "/"}</div>
                    <div><strong>Modo:</strong> {app.launch_mode || "proxy"}</div>
                  </div>

                  <label style={{ display: "block", marginBottom: 12 }}>
                    Cliente:
                    <select
                      style={{ display: "block", marginTop: 6, width: "100%" }}
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
                  </label>

                  <button onClick={() => enterApp(app)}>Entrar</button>
                </div>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}