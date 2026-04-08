// portal/src/components/LoginView.jsx
import React from "react";

export default function LoginView({
  username,
  setUser,
  password,
  setPass,
  loading,
  login,
}) {
  return (
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
  );
}