// portal/src/services/adminService.js
import { apiRequest } from "./api";
import {
  normalizeAdminAppsCatalog,
  normalizePermissionRow,
} from "../utils/adminHelpers";

export const ADMIN_CLIENTS_API_URL = "/app1/internal/admin/clients";
export const ADMIN_USERS_BY_CLIENT_API_URL = "/app1/internal/admin/users-by-client";
export const ADMIN_SUBSCRIPTIONS_BY_CLIENT_API_URL =
  "/app1/internal/admin/subscriptions-by-client";
export const ADMIN_PERMISSIONS_BY_CLIENT_API_URL =
  "/app1/internal/admin/permissions-by-client";
export const ADMIN_GLOBAL_USERS_API_URL = "/app1/internal/admin/global-users";
export const ADMIN_GLOBAL_APPLICATIONS_API_URL =
  "/app1/internal/admin/global-applications";
export const ADMIN_GLOBAL_CLIENTS_API_URL = "/app1/internal/admin/global-clients";
export const ADMIN_CREATE_USER_API_URL = "/app1/internal/admin/create-user";
export const ADMIN_CREATE_CLIENT_API_URL = "/app1/internal/admin/create-client";
export const ADMIN_UPSERT_SUBSCRIPTION_API_URL =
  "/app1/internal/admin/upsert-subscription";
export const ADMIN_UPDATE_CLIENT_API_URL = "/app1/internal/admin/update-client";
export const ADMIN_UPDATE_USER_API_URL = "/app1/internal/admin/update-user";
export const ADMIN_CREATE_APPLICATION_API_URL =
  "/app1/internal/admin/create-application";
export const ADMIN_UPDATE_APPLICATION_API_URL =
  "/app1/internal/admin/update-application";
export const ADMIN_UPDATE_SUBSCRIPTION_API_URL =
  "/app1/internal/admin/update-subscription";
export const ADMIN_CREATE_PERMISSION_API_URL =
  "/app1/internal/admin/create-permission";
export const ADMIN_UPDATE_PERMISSION_ROLE_API_URL =
  "/app1/internal/admin/update-permission-role";

function normalizeSubscriptionRow(row) {
  if (!row || typeof row !== "object") {
    return {
      client_id: "",
      app_id: "",
      app_name: "",
      status: "inactive",
      is_enabled: false,
      start_date: "",
      end_date: "",
    };
  }

  const clientId =
    row.client_id ??
    row.customer_id ??
    row.id_cliente ??
    row.cliente_id ??
    "";

  const appId =
    row.app_id ??
    row.application_id ??
    row.id_app ??
    row.aplicacion_id ??
    row.id ??
    "";

  const appName =
    row.app_name ??
    row.application_name ??
    row.name ??
    row.nombre_aplicacion ??
    row.app ??
    "";

  const status =
    row.status ??
    row.subscription_status ??
    row.estado ??
    "inactive";

  const isEnabledRaw =
    row.is_enabled ??
    row.enabled ??
    row.activo ??
    row.is_active ??
    false;

  const isEnabled =
    typeof isEnabledRaw === "boolean"
      ? isEnabledRaw
      : ["1", "true", "t", "yes", "y", "si", "sí"].includes(
          String(isEnabledRaw).toLowerCase()
        );

  return {
    ...row,
    client_id: clientId,
    app_id: appId,
    app_name: appName,
    status: String(status || "inactive").toLowerCase(),
    is_enabled: isEnabled,
    start_date: row.start_date ?? row.fecha_inicio ?? "",
    end_date: row.end_date ?? row.fecha_fin ?? "",
  };
}

export function extractAdminErrorMessage(error, fallback = "Error interno del servidor") {
  if (!error) return fallback;

  if (typeof error === "string") {
    return error.trim() || fallback;
  }

  if (error?.response?.data?.detail) {
    const detail = error.response.data.detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) {
      return detail
        .map((item) => {
          if (typeof item === "string") return item;
          if (item?.msg) return item.msg;
          return JSON.stringify(item);
        })
        .join(" | ");
    }
    return JSON.stringify(detail);
  }

  if (error?.data?.detail) {
    const detail = error.data.detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) {
      return detail
        .map((item) => {
          if (typeof item === "string") return item;
          if (item?.msg) return item.msg;
          return JSON.stringify(item);
        })
        .join(" | ");
    }
    return JSON.stringify(detail);
  }

  if (error?.detail) {
    if (typeof error.detail === "string") return error.detail;
    return JSON.stringify(error.detail);
  }

  if (error?.message && typeof error.message === "string") {
    return error.message;
  }

  try {
    return JSON.stringify(error);
  } catch {
    return fallback;
  }
}

export async function loadAdminClients() {
  const { data } = await apiRequest(ADMIN_CLIENTS_API_URL, { method: "GET" });
  return Array.isArray(data) ? data : [];
}

export async function loadAdminAppsCatalog() {
  const { data } = await apiRequest(ADMIN_GLOBAL_APPLICATIONS_API_URL, {
    method: "GET",
  });
  return normalizeAdminAppsCatalog(data);
}

export async function fetchAdminTabData(tab, clientId) {
  switch (tab) {
    case "users": {
      const { data } = await apiRequest(
        `${ADMIN_USERS_BY_CLIENT_API_URL}?client_id=${encodeURIComponent(clientId)}`,
        { method: "GET" }
      );
      return { adminUsers: Array.isArray(data) ? data : [] };
    }

    case "subscriptions": {
      const { data } = await apiRequest(
        `${ADMIN_SUBSCRIPTIONS_BY_CLIENT_API_URL}?client_id=${encodeURIComponent(clientId)}`,
        { method: "GET" }
      );

      return {
        adminSubscriptions: (Array.isArray(data) ? data : []).map(normalizeSubscriptionRow),
      };
    }

    case "permissions": {
      const { data } = await apiRequest(
        `${ADMIN_PERMISSIONS_BY_CLIENT_API_URL}?client_id=${encodeURIComponent(clientId)}`,
        { method: "GET" }
      );
      return {
        adminPermissions: (Array.isArray(data) ? data : []).map(normalizePermissionRow),
      };
    }

    case "global-users": {
      const { data } = await apiRequest(ADMIN_GLOBAL_USERS_API_URL, {
        method: "GET",
      });
      return { adminGlobalUsers: Array.isArray(data) ? data : [] };
    }

    case "global-applications": {
      const { data } = await apiRequest(ADMIN_GLOBAL_APPLICATIONS_API_URL, {
        method: "GET",
      });
      return { adminGlobalApplications: Array.isArray(data) ? data : [] };
    }

    case "global-clients": {
      const { data } = await apiRequest(ADMIN_GLOBAL_CLIENTS_API_URL, {
        method: "GET",
      });
      return { adminGlobalClients: Array.isArray(data) ? data : [] };
    }

    default:
      return {};
  }
}

export async function createGlobalUser(payload) {
  const { data } = await apiRequest(ADMIN_CREATE_USER_API_URL, {
    method: "POST",
    body: payload,
  });
  return data;
}

export async function updateGlobalUser(payload) {
  const { data } = await apiRequest(ADMIN_UPDATE_USER_API_URL, {
    method: "POST",
    body: payload,
  });
  return data;
}

export async function createGlobalClient(payload) {
  const { data } = await apiRequest(ADMIN_CREATE_CLIENT_API_URL, {
    method: "POST",
    body: payload,
  });
  return data;
}

export async function updateGlobalClient(payload) {
  const { data } = await apiRequest(ADMIN_UPDATE_CLIENT_API_URL, {
    method: "POST",
    body: payload,
  });
  return data;
}

export async function createGlobalApplication(payload) {
  const { data } = await apiRequest(ADMIN_CREATE_APPLICATION_API_URL, {
    method: "POST",
    body: payload,
  });
  return data;
}

export async function updateGlobalApplication(payload) {
  const { data } = await apiRequest(ADMIN_UPDATE_APPLICATION_API_URL, {
    method: "POST",
    body: payload,
  });
  return data;
}

export async function upsertSubscription(payload) {
  const { data } = await apiRequest(ADMIN_UPSERT_SUBSCRIPTION_API_URL, {
    method: "POST",
    body: payload,
  });
  return data;
}

export async function updateSubscription(payload) {
  const { data } = await apiRequest(ADMIN_UPDATE_SUBSCRIPTION_API_URL, {
    method: "POST",
    body: payload,
  });
  return data;
}

export async function createPermission(payload) {
  const { data } = await apiRequest(ADMIN_CREATE_PERMISSION_API_URL, {
    method: "POST",
    body: payload,
  });
  return data;
}

export async function updatePermissionRole(payload) {
  const { data } = await apiRequest(ADMIN_UPDATE_PERMISSION_ROLE_API_URL, {
    method: "POST",
    body: payload,
  });
  return data;
}