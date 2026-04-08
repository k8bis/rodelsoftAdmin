// portal/src/services/api.js
export async function apiRequest(url, options = {}) {
  const {
    method = "GET",
    headers = {},
    body,
    credentials = "include",
    cache = "no-store",
  } = options;

  const finalOptions = {
    method,
    headers: {
      ...headers,
    },
    credentials,
    cache,
  };

  if (body !== undefined) {
    const isFormData = typeof FormData !== "undefined" && body instanceof FormData;

    if (isFormData) {
      finalOptions.body = body;
    } else {
      finalOptions.headers["Content-Type"] =
        finalOptions.headers["Content-Type"] || "application/json";
      finalOptions.body = typeof body === "string" ? body : JSON.stringify(body);
    }
  }

  const response = await fetch(url, finalOptions);

  const contentType = response.headers.get("content-type") || "";
  let data = null;

  if (contentType.includes("application/json")) {
    data = await response.json().catch(() => null);
  } else {
    const text = await response.text().catch(() => "");
    data = text || null;
  }

  if (!response.ok) {
    const detail =
      (data && typeof data === "object" && (data.detail || data.message)) ||
      (typeof data === "string" ? data : "") ||
      `Request failed (${response.status})`;

    throw new Error(detail);
  }

  return {
    ok: response.ok,
    status: response.status,
    data,
    response,
  };
}