// portal/src/components/Header.jsx
import React from "react";

export default function Header({
  authed,
  username,
  userMenuOpen,
  setUserMenuOpen,
  fetchMyApps,
  hasAdminScope,
  openAdminModal,
  logout,
}) {
  return (
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

                {hasAdminScope && (
                  <button
                    className="rs-user-dropdown-item"
                    onClick={() => {
                      openAdminModal();
                    }}
                  >
                    🛠 Administración
                  </button>
                )}

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
  );
}