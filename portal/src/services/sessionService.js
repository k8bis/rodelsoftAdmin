// portal/src/services/sessionService.js
import { apiRequest } from "./api";

export const LOGIN_API_URL = "/app1/login";
export const LOGOUT_API_URL = "/app1/logout";
export const ME_API_URL = "/app1/me";
export const MY_APPS_API_URL = "/app1/my/apps";
export const LAUNCH_BASE_URL = "/launch";

export async function fetchMe() {
  const { data } = await apiRequest(ME_API_URL, {
    method: "GET",
  });
  return data;
}

export async function fetchMyApps() {
  const { data } = await apiRequest(MY_APPS_API_URL, {
    method: "GET",
  });
  return Array.isArray(data) ? data : [];
}

export async function loginRequest(username, password) {
  const { data } = await apiRequest(LOGIN_API_URL, {
    method: "POST",
    body: { username, password },
  });
  return data;
}

export async function logoutRequest() {
  try {
    await apiRequest(LOGOUT_API_URL, {
      method: "POST",
    });
  } catch {
    // logout best-effort
  }
}

export function buildLaunchUrl(appId, clientId) {
  const params = new URLSearchParams({
    app_id: String(appId),
    client_id: String(clientId),
  });

  return `${LAUNCH_BASE_URL}?${params.toString()}`;
}