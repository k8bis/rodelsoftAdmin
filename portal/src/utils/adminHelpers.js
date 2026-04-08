// portal/src/utils/adminHelpers.js
export const ADMIN_TABS = [
  { key: "users", label: "Usuarios por cliente" },
  { key: "subscriptions", label: "Suscripciones por cliente" },
  { key: "permissions", label: "Permisos por cliente" },
  { key: "global-users", label: "Usuarios globales" },
  { key: "global-applications", label: "Aplicaciones globales" },
  { key: "global-clients", label: "Clientes globales" },
];

export const GLOBAL_ADMIN_TABS = new Set([
  "global-users",
  "global-applications",
  "global-clients",
]);

export function isGlobalAdminTab(tab) {
  return GLOBAL_ADMIN_TABS.has(tab);
}

function isClientAppEnabled(client) {
  if (!client) return false;
  return client.app_enabled !== undefined ? Boolean(client.app_enabled) : true;
}

function isClientSubscriptionEnabled(client) {
  if (!client) return false;
  return client.subscription_enabled !== undefined
    ? Boolean(client.subscription_enabled)
    : false;
}

export function getClientStatusLabel(client) {
  if (!client) return "sin estado";

  if (!isClientAppEnabled(client)) return "app deshabilitada";
  if (!isClientSubscriptionEnabled(client)) return "suscripción deshabilitada";
  if (client.subscription_status === "suspended") return "suspendida";
  if (client.subscription_status === "expired") return "expirada";
  if (client.subscription_status === "trial") return "trial";
  if (client.subscription_status === "active") return "activa";

  return client.subscription_status || "sin estado";
}

export function getClientStatusText(client) {
  if (!client) return "Sin información de suscripción";

  if (!isClientAppEnabled(client)) {
    return "Aplicación deshabilitada temporalmente";
  }

  if (!isClientSubscriptionEnabled(client)) {
    return "Suscripción deshabilitada para este cliente";
  }

  if (client.subscription_status === "suspended") {
    return "Suscripción suspendida";
  }

  if (client.subscription_status === "expired") {
    return "Suscripción expirada";
  }

  if (client.subscription_status === "trial") {
    return client.is_expiring_soon
      ? "Suscripción trial próxima a vencer"
      : "Suscripción trial activa";
  }

  if (client.subscription_status === "active") {
    return client.is_expiring_soon
      ? "Suscripción activa próxima a vencer"
      : "Suscripción activa";
  }

  return "Estado de suscripción no disponible";
}

export function getSelectedClient(app, selectedClientByApp) {
  if (!app?.clients?.length) return null;

  const selectedId = selectedClientByApp?.[app.app_id];
  return (
    app.clients.find((c) => String(c.id) === String(selectedId)) ||
    app.clients.find((c) => c.is_accessible) ||
    app.clients[0] ||
    null
  );
}

export function buildDefaultSelectedClients(rawApps = [], current = {}) {
  const next = { ...current };

  rawApps.forEach((app) => {
    if (!app?.clients?.length) return;

    const exists = app.clients.some((c) => String(c.id) === String(next[app.app_id]));
    if (exists) return;

    const firstAccessible = app.clients.find((c) => c.is_accessible);
    next[app.app_id] = (firstAccessible || app.clients[0]).id;
  });

  return next;
}

export function getDefaultAdminCreateUserForm() {
  return {
    username: "",
    password: "",
    email: "",
    is_system_admin: false,
  };
}

export function getDefaultAdminCreateClientForm() {
  return {
    client_id: "",
    client_name: "",
  };
}

export function getDefaultAdminApplicationForm() {
  return {
    app_id: "",
    app_name: "",
    slug: "",
    internal_url: "",
    public_url: "",
    entry_path: "",
    health_path: "",
    launch_mode: "dynamic_proxy",
    description: "",
    is_enabled: true,
  };
}

export function getDefaultAdminSubscriptionForm(clientId = "") {
  return {
    client_id: clientId ? String(clientId) : "",
    app_id: "",
    status: "active",
    is_enabled: true,
    start_date: "",
    end_date: "",
  };
}

export function getDefaultAdminPermissionForm(clientId = "") {
  return {
    permission_id: "",
    user_id: "",
    username: "",
    client_id: clientId ? String(clientId) : "",
    app_id: "",
    role: "member",
  };
}

export function normalizeAdminAppsCatalog(rows = []) {
  return (Array.isArray(rows) ? rows : []).map((row) => ({
    id: row.app_id || row.id,
    name: row.app_name || row.name,
    slug: row.slug || "",
    internal_url: row.internal_url || "",
    public_url: row.public_url || "",
    entry_path: row.entry_path || "",
    health_path: row.health_path || "",
    launch_mode: row.launch_mode || "dynamic_proxy",
    description: row.description || "",
    is_enabled:
      typeof row.is_enabled === "boolean"
        ? row.is_enabled
        : Number(row.is_enabled || 0) === 1,
  }));
}

export function normalizePermissionRow(row) {
  return {
    permission_id: row.permission_id,
    user_id: row.user_id,
    username: row.username,
    client_id: row.client_id,
    client_name: row.client_name,
    app_id: row.app_id,
    app_name: row.app_name,
    role: row.role || "member",
  };
}

export function getAdminSelectedClientName(adminClients = [], adminSelectedClientId = "") {
  const found = adminClients.find(
    (c) => String(c.client_id) === String(adminSelectedClientId)
  );
  return found?.client_name || "";
}