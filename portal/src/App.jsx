import React, { useEffect, useMemo, useState } from "react";

/**
 * Mapa estático de "nombre de app" -> ruta en Nginx.
 * Ajusta si cambias los names en la tabla `applications`.
 */
const APP_ROUTE = {
  "Rodel-RealState": "/app1/",
  "Rodel-Garage": "/app2/",
};

const APP_ROUTE_BY_ID = {
  1: "/app1/", // Rodel-RealState
  2: "/app2/", // Rodel-Garage
};


export default function App() {
  const [username, setUser] = useState("admin");
  const [password, setPass] = useState("adminpass");
  const [authed, setAuthed] = useState(false);
  const [msg, setMsg] = useState("");
  const [loading, setLoading] = useState(false);

  // permisos “crudos” que vienen de los microservicios
  const [rawApp1, setRawApp1] = useState([]);
  const [rawApp2, setRawApp2] = useState([]);

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
      // opcional: cargar permisos al instante
      fetchPermissions();
    } catch (e) {
      setMsg(`Error de red: ${String(e)}`);
    } finally {
      setLoading(false);
    }
  };

  const logout = async () => {
    setMsg("");
    try {
      await fetch("/app1/logout", { method: "POST", credentials: "include" });
    } catch {}
    setAuthed(false);
    setRawApp1([]);
    setRawApp2([]);
    setSelectedClientByApp({});
  };

  const fetchPermissions = async () => {
    setMsg("");
    // App1 (FastAPI) devuelve [{app, client}]
    try {
      const r1 = await fetch("/app1/permissions", { credentials: "include" });
      setRawApp1(r1.ok ? await r1.json() : []);
      if (!r1.ok) setMsg(`/app1/permissions falló (${r1.status})`);
    } catch (e) {
      setMsg(`Error /app1/permissions: ${String(e)}`);
      setRawApp1([]);
    }
    // App2 (Express) devuelve [{app_name, client}]
    try {
      const r2 = await fetch("/app2/permissions", { credentials: "include" });
      setRawApp2(r2.ok ? await r2.json() : []);
      if (!r2.ok) setMsg((prev) => prev + ` | /app2/permissions falló (${r2.status})`);
    } catch (e) {
      setMsg((prev) => prev + ` | Error /app2/permissions: ${String(e)}`);
      setRawApp2([]);
    }
  };

  // Normaliza: { [appName]: Set<clientName> }
  const grouped = useMemo(() => {
    const acc = new Map(); // app_id -> { appName, clients: Map<client_id, clientName> }

    const add = (p) => {
      if (!p?.app_id || !p?.client_id) return;
      if (!acc.has(p.app_id)) acc.set(p.app_id, { appName: p.app, clients: new Map() });
      const bucket = acc.get(p.app_id);
      bucket.appName = p.app || bucket.appName;
      bucket.clients.set(p.client_id, p.client);
    };

    rawApp1.forEach(add);
    rawApp2.forEach(add);

    const out = {};
    for (const [app_id, { appName, clients }] of acc.entries()) {
      out[app_id] = { appName, clients: Array.from(clients.entries()).map(([client_id, client]) => ({ client_id, client })) };
    }
    return out;
  }, [rawApp1, rawApp2]);

  // Si ya hay permisos, autoselecciona el 1er cliente por app
  useEffect(() => {
  const next = { ...selectedClientByApp };
    Object.entries(grouped).forEach(([app_id, data]) => {
      if (!data.clients?.length) return;
      if (!next[app_id]) next[app_id] = data.clients[0].client_id;
    });
    setSelectedClientByApp(next);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [JSON.stringify(grouped)]);

  const enterApp = (app_id) => {
    const route = APP_ROUTE_BY_ID[app_id];
    const client_id = selectedClientByApp[app_id];
    if (!route) return setMsg(`No hay ruta para app_id=${app_id}. Ajusta APP_ROUTE_BY_ID.`);
    if (!client_id) return setMsg(`Selecciona un cliente para app_id=${app_id}.`);
    window.location.href = `${route}?app_id=${app_id}&client_id=${client_id}`;
  };

  return (
    <div style={{ maxWidth: 960, margin: "32px auto", fontFamily: "system-ui, sans-serif" }}>
      <h1>Portal Global</h1>

      {msg && (
        <div style={{ padding: "10px 12px", background: "#fff6cc", border: "1px solid #f2d16b", borderRadius: 8, marginBottom: 12 }}>
          {msg}
        </div>
      )}

      {!authed ? (
        <div style={{ display: "grid", gap: 8, maxWidth: 360 }}>
          <label>
            Usuario
            <input value={username} onChange={(e) => setUser(e.target.value)} placeholder="usuario" />
          </label>
          <label>
            Contraseña
            <input value={password} onChange={(e) => setPass(e.target.value)} type="password" placeholder="contraseña" />
          </label>
          <button onClick={login} disabled={loading}>{loading ? "Iniciando..." : "Iniciar sesión"}</button>
        </div>
      ) : (
        <>
          <div style={{ display: "flex", gap: 10, alignItems: "center", marginBottom: 12 }}>
            <button onClick={fetchPermissions}>Refrescar permisos</button>
            <div style={{ marginLeft: "auto" }} />
            <button onClick={logout}>Salir</button>
          </div>

          <h2>Mis aplicaciones</h2>
          {Object.keys(grouped).length === 0 ? (
            <p>No hay aplicaciones asignadas a tu usuario.</p>
          ) : (
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
              {Object.entries(grouped).map(([app_id, data]) => (
                <div key={app_id} className="card">
                  <h3>{data.appName}</h3>
                  <label>
                    Cliente :
                    <select
                      value={selectedClientByApp[app_id] || ""}
                      onChange={(e) =>
                        setSelectedClientByApp((prev) => ({ ...prev, [app_id]: Number(e.target.value) }))
                      }
                    >
                      {data.clients.map(({client_id, client}) => (
                        <option key={client_id} value={client_id}>{client}</option>
                      ))}
                    </select>
                  </label>
                  <div>
                    <button onClick={() => enterApp(Number(app_id))}>Entrar</button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}
