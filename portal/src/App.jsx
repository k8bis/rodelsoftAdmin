import React, { useEffect, useMemo, useState } from "react";
import "./shared-shell.css";
import "./App.css";

import Header from "./components/Header";
import LoginView from "./components/LoginView";
import AppsView from "./components/AppsView";
import AdminModal from "./components/AdminModal";

import {
  buildDefaultSelectedClients,
  getDefaultAdminApplicationForm,
  getDefaultAdminCreateClientForm,
  getDefaultAdminCreateUserForm,
  getDefaultAdminPermissionForm,
  getDefaultAdminSubscriptionForm,
  getAdminSelectedClientName,
  getSelectedClient,
  isGlobalAdminTab,
} from "./utils/adminHelpers";

import {
  buildLaunchUrl,
  fetchMe,
  fetchMyApps as fetchMyAppsRequest,
  loginRequest,
  logoutRequest,
} from "./services/sessionService";

import {
  createGlobalApplication,
  createGlobalClient,
  createGlobalUser,
  createPermission,
  fetchAdminTabData as fetchAdminTabDataRequest,
  loadAdminAppsCatalog as loadAdminAppsCatalogRequest,
  loadAdminClients as loadAdminClientsRequest,
  updateGlobalApplication,
  updateGlobalClient,
  updateGlobalUser,
  updatePermissionRole,
  updateSubscription,
  upsertSubscription,
  extractAdminErrorMessage,
} from "./services/adminService";

export default function App() {
  const [username, setUser] = useState("admin");
  const [password, setPass] = useState("adminpass");
  const [authed, setAuthed] = useState(false);
  const [msg, setMsg] = useState("");
  const [loading, setLoading] = useState(false);
  const [initializing, setInitializing] = useState(true);
  const [msgType, setMsgType] = useState("info");
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const [isSystemAdmin, setIsSystemAdmin] = useState(false);
  const [hasAdminScope, setHasAdminScope] = useState(false);

  const [rawApps, setRawApps] = useState([]);
  const [selectedClientByApp, setSelectedClientByApp] = useState({});

  const [adminModalOpen, setAdminModalOpen] = useState(false);
  const [adminTab, setAdminTab] = useState("users");

  const [adminClients, setAdminClients] = useState([]);
  const [adminSelectedClientId, setAdminSelectedClientId] = useState("");
  const [adminLoadingClients, setAdminLoadingClients] = useState(false);
  const [adminLoadingData, setAdminLoadingData] = useState(false);

  const [adminUsers, setAdminUsers] = useState([]);
  const [adminSubscriptions, setAdminSubscriptions] = useState([]);
  const [adminPermissions, setAdminPermissions] = useState([]);
  const [adminGlobalUsers, setAdminGlobalUsers] = useState([]);
  const [adminGlobalApplications, setAdminGlobalApplications] = useState([]);
  const [adminGlobalClients, setAdminGlobalClients] = useState([]);
  const [adminAppsCatalog, setAdminAppsCatalog] = useState([]);

  // datasets específicos para "Nuevo permiso"
  const [adminPermissionUsers, setAdminPermissionUsers] = useState([]);
  const [adminPermissionApps, setAdminPermissionApps] = useState([]);

  const [adminCreateUserForm, setAdminCreateUserForm] = useState(
    getDefaultAdminCreateUserForm()
  );
  const [adminCreateClientForm, setAdminCreateClientForm] = useState(
    getDefaultAdminCreateClientForm()
  );
  const [adminApplicationForm, setAdminApplicationForm] = useState(
    getDefaultAdminApplicationForm()
  );
  const [adminSubscriptionForm, setAdminSubscriptionForm] = useState(
    getDefaultAdminSubscriptionForm()
  );
  const [adminPermissionForm, setAdminPermissionForm] = useState(
    getDefaultAdminPermissionForm()
  );

  const [adminActionLoading, setAdminActionLoading] = useState(false);
  const [adminActionMsg, setAdminActionMsg] = useState("");
  const [adminActionMsgType, setAdminActionMsgType] = useState("info");
  const [adminEditorOpen, setAdminEditorOpen] = useState(false);
  const [adminEditorMode, setAdminEditorMode] = useState("create");
  const [adminEditorType, setAdminEditorType] = useState("");

  const resetAdminActionMessages = () => {
    setAdminActionMsg("");
    setAdminActionMsgType("info");
  };

  const clearAdminDatasets = () => {
    setAdminUsers([]);
    setAdminSubscriptions([]);
    setAdminPermissions([]);
    setAdminGlobalUsers([]);
    setAdminGlobalApplications([]);
    setAdminGlobalClients([]);
  };

  const buildPermissionUsersDataset = (users) => {
    return Array.isArray(users) ? users : [];
  };

  const buildPermissionAppsDataset = (subscriptions) => {
    const allowedStatuses = new Set(["active", "trial"]);
    const rows = Array.isArray(subscriptions) ? subscriptions : [];

    const apps = rows
      .filter((row) => allowedStatuses.has(String(row.status || "").toLowerCase()))
      .filter((row) => Boolean(row.is_enabled))
      .map((row) => ({
        id: row.app_id,
        name: row.app_name,
      }));

    const seen = new Set();
    return apps.filter((app) => {
      const key = String(app.id);
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    });
  };

  const fetchMyApps = async () => {
    setMsg("");

    try {
      const data = await fetchMyAppsRequest();
      setRawApps(Array.isArray(data) ? data : []);
      setAuthed(true);
    } catch (e) {
      const errorMessage = extractAdminErrorMessage(e);
      const normalized = String(errorMessage || "").toLowerCase();

      const isUnauthorized =
        normalized.includes("401") ||
        normalized.includes("no token") ||
        normalized.includes("unauthorized") ||
        normalized.includes("not authenticated") ||
        normalized.includes("no autenticado");

      if (isUnauthorized) {
        setRawApps([]);
        setAuthed(false);
        setMsg("");
        setMsgType("info");
        return;
      }

      setMsg(`Error /app1/my/apps: ${errorMessage}`);
      setMsgType("error");
      setRawApps([]);
      setAuthed(false);
    }
  };

  const restoreSession = async () => {
    try {
      await fetchMyApps();

      try {
        const meData = await fetchMe();

        if (meData?.user) {
          setUser(meData.user);
        }

        setIsSystemAdmin(Boolean(meData?.is_system_admin));
        setHasAdminScope(Boolean(meData?.has_admin_scope || meData?.is_system_admin));
      } catch {
        setIsSystemAdmin(false);
        setHasAdminScope(false);
      }
    } finally {
      setInitializing(false);
    }
  };

  useEffect(() => {
    restoreSession();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const login = async () => {
    setLoading(true);
    setMsg("");
    setMsgType("info");

    try {
      await loginRequest(username, password);
      await restoreSession();
      setMsg("");
    } catch (e) {
      setMsg(extractAdminErrorMessage(e));
      setMsgType("error");
      setAuthed(false);
    } finally {
      setLoading(false);
    }
  };

  const logout = async () => {
    try {
      await logoutRequest();
    } finally {
      setAuthed(false);
      setRawApps([]);
      setUserMenuOpen(false);
      setAdminModalOpen(false);
      setHasAdminScope(false);
      setIsSystemAdmin(false);
    }
  };

  useEffect(() => {
    setSelectedClientByApp((prev) => buildDefaultSelectedClients(rawApps, prev));
  }, [rawApps]);

  useEffect(() => {
    const handleClick = () => setUserMenuOpen(false);
    window.addEventListener("click", handleClick);
    return () => window.removeEventListener("click", handleClick);
  }, []);

  const fetchAdminClients = async () => {
    setAdminLoadingClients(true);
    resetAdminActionMessages();

    try {
      const rows = await loadAdminClientsRequest();
      setAdminClients(rows);

      if (!rows.length) {
        setAdminSelectedClientId("");
        clearAdminDatasets();
        return;
      }

      const exists = rows.some(
        (row) => String(row.client_id) === String(adminSelectedClientId)
      );

      if (!exists) {
        setAdminSelectedClientId(String(rows[0].client_id));
      }
    } catch (e) {
      setAdminActionMsg(extractAdminErrorMessage(e));
      setAdminActionMsgType("error");
      setAdminClients([]);
      setAdminSelectedClientId("");
      clearAdminDatasets();
    } finally {
      setAdminLoadingClients(false);
    }
  };

  const fetchAdminTabData = async (tab, clientId) => {
    if (!isGlobalAdminTab(tab) && !clientId) {
      clearAdminDatasets();
      return;
    }

    setAdminLoadingData(true);
    resetAdminActionMessages();

    try {
      if (tab === "permissions") {
        const [permissionsResult, usersResult, subscriptionsResult] = await Promise.all([
          fetchAdminTabDataRequest("permissions", clientId),
          fetchAdminTabDataRequest("users", clientId),
          fetchAdminTabDataRequest("subscriptions", clientId),
        ]);

        if (Object.prototype.hasOwnProperty.call(permissionsResult, "adminPermissions")) {
          setAdminPermissions(permissionsResult.adminPermissions);
        } else {
          setAdminPermissions([]);
        }

        if (Object.prototype.hasOwnProperty.call(usersResult, "adminUsers")) {
          setAdminUsers(usersResult.adminUsers);
        } else {
          setAdminUsers([]);
        }

        if (Object.prototype.hasOwnProperty.call(subscriptionsResult, "adminSubscriptions")) {
          setAdminSubscriptions(subscriptionsResult.adminSubscriptions);
        } else {
          setAdminSubscriptions([]);
        }

        return;
      }

      const result = await fetchAdminTabDataRequest(tab, clientId);

      if (Object.prototype.hasOwnProperty.call(result, "adminUsers")) {
        setAdminUsers(result.adminUsers);
      }
      if (Object.prototype.hasOwnProperty.call(result, "adminSubscriptions")) {
        setAdminSubscriptions(result.adminSubscriptions);
      }
      if (Object.prototype.hasOwnProperty.call(result, "adminPermissions")) {
        setAdminPermissions(result.adminPermissions);
      }
      if (Object.prototype.hasOwnProperty.call(result, "adminGlobalUsers")) {
        setAdminGlobalUsers(result.adminGlobalUsers);
      }
      if (Object.prototype.hasOwnProperty.call(result, "adminGlobalApplications")) {
        setAdminGlobalApplications(result.adminGlobalApplications);
      }
      if (Object.prototype.hasOwnProperty.call(result, "adminGlobalClients")) {
        setAdminGlobalClients(result.adminGlobalClients);
      }
    } catch (e) {
      setAdminActionMsg(extractAdminErrorMessage(e));
      setAdminActionMsgType("error");

      if (tab === "users") setAdminUsers([]);
      if (tab === "subscriptions") setAdminSubscriptions([]);
      if (tab === "permissions") {
        setAdminPermissions([]);
        setAdminUsers([]);
        setAdminSubscriptions([]);
      }
      if (tab === "global-users") setAdminGlobalUsers([]);
      if (tab === "global-applications") setAdminGlobalApplications([]);
      if (tab === "global-clients") setAdminGlobalClients([]);
    } finally {
      setAdminLoadingData(false);
    }
  };

  const loadAdminAppsCatalog = async () => {
    try {
      const rows = await loadAdminAppsCatalogRequest();
      setAdminAppsCatalog(rows);
    } catch (e) {
      setAdminAppsCatalog([]);
      setAdminActionMsg(extractAdminErrorMessage(e));
      setAdminActionMsgType("error");
    }
  };

  const ensurePermissionDatasets = async (clientId) => {
    const safeClientId = String(clientId || adminSelectedClientId || "");
    if (!safeClientId) {
      setAdminPermissionUsers([]);
      setAdminPermissionApps([]);
      return;
    }

    let nextUsers = Array.isArray(adminUsers) ? adminUsers : [];
    let nextSubscriptions = Array.isArray(adminSubscriptions) ? adminSubscriptions : [];

    const needsUsers = nextUsers.length === 0;
    const needsSubscriptions = nextSubscriptions.length === 0;

    if (needsUsers || needsSubscriptions) {
      try {
        const requests = [];
        if (needsUsers) requests.push(fetchAdminTabDataRequest("users", safeClientId));
        else requests.push(Promise.resolve({ adminUsers: nextUsers }));

        if (needsSubscriptions) {
          requests.push(fetchAdminTabDataRequest("subscriptions", safeClientId));
        } else {
          requests.push(Promise.resolve({ adminSubscriptions: nextSubscriptions }));
        }

        const [usersResult, subscriptionsResult] = await Promise.all(requests);

        nextUsers = Array.isArray(usersResult?.adminUsers) ? usersResult.adminUsers : nextUsers;
        nextSubscriptions = Array.isArray(subscriptionsResult?.adminSubscriptions)
          ? subscriptionsResult.adminSubscriptions
          : nextSubscriptions;

        if (needsUsers) setAdminUsers(nextUsers);
        if (needsSubscriptions) setAdminSubscriptions(nextSubscriptions);
      } catch (e) {
        setAdminActionMsg(extractAdminErrorMessage(e));
        setAdminActionMsgType("error");
      }
    }

    setAdminPermissionUsers(buildPermissionUsersDataset(nextUsers));
    setAdminPermissionApps(buildPermissionAppsDataset(nextSubscriptions));
  };

  const openAdminModal = async () => {
    setUserMenuOpen(false);
    setAdminModalOpen(true);
    setAdminTab(isSystemAdmin ? "global-users" : "users");
    resetAdminActionMessages();

    await fetchAdminClients();
    await loadAdminAppsCatalog();
  };

  useEffect(() => {
    if (!adminModalOpen) return;
    fetchAdminTabData(adminTab, adminSelectedClientId);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [adminModalOpen, adminTab, adminSelectedClientId]);

  // recalcular datasets de "Nuevo permiso" cuando cambia cliente / datasets
  useEffect(() => {
    const clientId = String(adminPermissionForm.client_id || "");

    if (adminEditorType !== "permission" || adminEditorMode !== "create" || !adminEditorOpen) {
      return;
    }

    const users = buildPermissionUsersDataset(adminUsers);
    setAdminPermissionUsers(users);

    const uniqueApps = buildPermissionAppsDataset(adminSubscriptions);
    setAdminPermissionApps(uniqueApps);

    if (
      adminPermissionForm.app_id &&
      !uniqueApps.some((app) => String(app.id) === String(adminPermissionForm.app_id))
    ) {
      setAdminPermissionForm((prev) => ({
        ...prev,
        app_id: "",
      }));
    }

    if (
      adminPermissionForm.user_id &&
      !users.some((user) => String(user.user_id || user.id) === String(adminPermissionForm.user_id))
    ) {
      setAdminPermissionForm((prev) => ({
        ...prev,
        user_id: "",
        username: "",
      }));
    }
  }, [
    adminEditorType,
    adminEditorMode,
    adminEditorOpen,
    adminPermissionForm.client_id,
    adminPermissionForm.app_id,
    adminPermissionForm.user_id,
    adminUsers,
    adminSubscriptions,
  ]);

  const openAdminEditor = async (type, mode = "create", row = null) => {
    resetAdminActionMessages();
    setAdminEditorType(type);
    setAdminEditorMode(mode);

    if (type === "global-user") {
      if (mode === "edit" && row) {
        setAdminCreateUserForm({
          user_id: row.user_id || "",
          username: row.username || "",
          password: "",
          email: row.email || "",
          is_system_admin: Boolean(row.is_system_admin),
        });
      } else {
        setAdminCreateUserForm(getDefaultAdminCreateUserForm());
      }
    }

    if (type === "global-client") {
      if (mode === "edit" && row) {
        setAdminCreateClientForm({
          client_id: row.client_id || "",
          client_name: row.client_name || "",
        });
      } else {
        setAdminCreateClientForm(getDefaultAdminCreateClientForm());
      }
    }

    if (type === "global-application") {
      if (mode === "edit" && row) {
        setAdminApplicationForm({
          app_id: row.app_id || "",
          app_name: row.app_name || "",
          slug: row.slug || "",
          internal_url: row.internal_url || "",
          public_url: row.public_url || "",
          entry_path: row.entry_path || "/",
          health_path: row.health_path || "/health",
          launch_mode: row.launch_mode || "dynamic_proxy",
          description: row.description || "",
          is_enabled: row.is_enabled !== undefined ? Boolean(row.is_enabled) : true,
        });
      } else {
        setAdminApplicationForm(getDefaultAdminApplicationForm());
      }
    }

    if (type === "subscription") {
      if (mode === "edit" && row) {
        setAdminSubscriptionForm({
          client_id: row.client_id
            ? String(row.client_id)
            : String(adminSelectedClientId || ""),
          app_id: row.app_id ? String(row.app_id) : "",
          status: row.status || "active",
          is_enabled: Boolean(row.is_enabled),
          start_date: row.start_date || "",
          end_date: row.end_date || "",
        });
      } else {
        setAdminSubscriptionForm(getDefaultAdminSubscriptionForm(adminSelectedClientId));
      }
    }

    if (type === "permission") {
      if (mode === "edit" && row) {
        setAdminPermissionForm({
          permission_id: row.permission_id ? String(row.permission_id) : "",
          user_id: row.user_id ? String(row.user_id) : "",
          username: row.username || "",
          client_id: row.client_id
            ? String(row.client_id)
            : String(adminSelectedClientId || ""),
          app_id: row.app_id ? String(row.app_id) : "",
          role: row.role || "member",
        });

        setAdminPermissionUsers(buildPermissionUsersDataset(adminUsers));
        setAdminPermissionApps(
          buildPermissionAppsDataset(
            adminSubscriptions,
            row.client_id ? String(row.client_id) : String(adminSelectedClientId || "")
          )
        );
      } else {
        const nextClientId = String(adminSelectedClientId || "");

        setAdminPermissionForm(getDefaultAdminPermissionForm(nextClientId));

        // Abrir primero el editor para que el useEffect de recalculo ya entre con el estado correcto
        setAdminEditorOpen(true);

        // Forzar datasets inmediatos y recarga defensiva si aún no están disponibles
        await ensurePermissionDatasets(nextClientId);
        return;
      }
    }

    setAdminEditorOpen(true);
  };

  const closeAdminModal = () => {
    setAdminModalOpen(false);
    setAdminEditorOpen(false);
    setAdminEditorType("");
    setAdminEditorMode("create");
    resetAdminActionMessages();
  };

  const closeAdminEditor = () => {
    setAdminEditorOpen(false);
    setAdminEditorType("");
    setAdminEditorMode("create");
    setAdminPermissionUsers([]);
    setAdminPermissionApps([]);
    resetAdminActionMessages();
  };

  const refreshAfterMutation = async (tab) => {
    const normalizedTab = tab === "subscription" ? "subscriptions" : tab;
    await fetchAdminTabData(normalizedTab, adminSelectedClientId);

    if (
      normalizedTab === "global-applications" ||
      normalizedTab === "subscriptions" ||
      normalizedTab === "permissions"
    ) {
      await loadAdminAppsCatalog();
    }
  };

  const handleCreateGlobalUser = async () => {
    resetAdminActionMessages();

    if (!String(adminCreateUserForm.username || "").trim()) {
      setAdminActionMsg("Debes capturar el username.");
      setAdminActionMsgType("warning");
      return;
    }

    if (!String(adminCreateUserForm.password || "").trim()) {
      setAdminActionMsg("Debes capturar el password inicial.");
      setAdminActionMsgType("warning");
      return;
    }

    setAdminActionLoading(true);

    try {
      const data = await createGlobalUser({
        username: String(adminCreateUserForm.username || "").trim(),
        password: String(adminCreateUserForm.password || "").trim(),
        email: String(adminCreateUserForm.email || "").trim() || null,
        is_system_admin: Boolean(adminCreateUserForm.is_system_admin),
      });

      setAdminActionMsg(data?.message || "Usuario global creado correctamente.");
      setAdminActionMsgType("success");

      await refreshAfterMutation("global-users");
      closeAdminEditor();
    } catch (e) {
      setAdminActionMsg(extractAdminErrorMessage(e));
      setAdminActionMsgType("error");
    } finally {
      setAdminActionLoading(false);
    }
  };

  const handleUpdateGlobalUser = async () => {
    resetAdminActionMessages();

    if (!adminCreateUserForm.user_id) {
      setAdminActionMsg("No se encontró el user_id.");
      setAdminActionMsgType("warning");
      return;
    }

    if (!String(adminCreateUserForm.username || "").trim()) {
      setAdminActionMsg("Debes capturar el username.");
      setAdminActionMsgType("warning");
      return;
    }

    setAdminActionLoading(true);

    try {
      const data = await updateGlobalUser({
        user_id: Number(adminCreateUserForm.user_id),
        username: String(adminCreateUserForm.username || "").trim(),
        email: String(adminCreateUserForm.email || "").trim() || null,
        is_system_admin: Boolean(adminCreateUserForm.is_system_admin),
      });

      setAdminActionMsg(data?.message || "Usuario global actualizado correctamente.");
      setAdminActionMsgType("success");

      await refreshAfterMutation("global-users");
      closeAdminEditor();
    } catch (e) {
      setAdminActionMsg(extractAdminErrorMessage(e));
      setAdminActionMsgType("error");
    } finally {
      setAdminActionLoading(false);
    }
  };

  const handleCreateGlobalClient = async () => {
    resetAdminActionMessages();

    if (!String(adminCreateClientForm.client_name || "").trim()) {
      setAdminActionMsg("Debes capturar el nombre del cliente.");
      setAdminActionMsgType("warning");
      return;
    }

    setAdminActionLoading(true);

    try {
      const data = await createGlobalClient({
        client_name: String(adminCreateClientForm.client_name || "").trim(),
      });

      setAdminActionMsg(data?.message || "Cliente creado correctamente.");
      setAdminActionMsgType("success");

      await refreshAfterMutation("global-clients");
      closeAdminEditor();
    } catch (e) {
      setAdminActionMsg(extractAdminErrorMessage(e));
      setAdminActionMsgType("error");
    } finally {
      setAdminActionLoading(false);
    }
  };

  const handleUpdateGlobalClient = async () => {
    resetAdminActionMessages();

    if (!adminCreateClientForm.client_id) {
      setAdminActionMsg("No se encontró el client_id.");
      setAdminActionMsgType("warning");
      return;
    }

    if (!String(adminCreateClientForm.client_name || "").trim()) {
      setAdminActionMsg("Debes capturar el nombre del cliente.");
      setAdminActionMsgType("warning");
      return;
    }

    setAdminActionLoading(true);

    try {
      const data = await updateGlobalClient({
        client_id: Number(adminCreateClientForm.client_id),
        client_name: String(adminCreateClientForm.client_name || "").trim(),
      });

      setAdminActionMsg(data?.message || "Cliente actualizado correctamente.");
      setAdminActionMsgType("success");

      await refreshAfterMutation("global-clients");
      closeAdminEditor();
    } catch (e) {
      setAdminActionMsg(extractAdminErrorMessage(e));
      setAdminActionMsgType("error");
    } finally {
      setAdminActionLoading(false);
    }
  };

  const handleCreateGlobalApplication = async () => {
    resetAdminActionMessages();

    if (!String(adminApplicationForm.app_name || "").trim()) {
      setAdminActionMsg("Debes capturar el nombre de la aplicación.");
      setAdminActionMsgType("warning");
      return;
    }

    if (!String(adminApplicationForm.slug || "").trim()) {
      setAdminActionMsg("Debes capturar el slug.");
      setAdminActionMsgType("warning");
      return;
    }

    if (!String(adminApplicationForm.internal_url || "").trim()) {
      setAdminActionMsg("Debes capturar la Internal URL.");
      setAdminActionMsgType("warning");
      return;
    }

    if (!String(adminApplicationForm.public_url || "").trim()) {
      setAdminActionMsg("Debes capturar la Public URL.");
      setAdminActionMsgType("warning");
      return;
    }

    setAdminActionLoading(true);

    try {
      const data = await createGlobalApplication({
        app_name: String(adminApplicationForm.app_name || "").trim(),
        slug: String(adminApplicationForm.slug || "").trim(),
        internal_url: String(adminApplicationForm.internal_url || "").trim(),
        public_url: String(adminApplicationForm.public_url || "").trim(),
        entry_path: String(adminApplicationForm.entry_path || "").trim() || "/",
        health_path: String(adminApplicationForm.health_path || "").trim() || "/health",
        launch_mode: adminApplicationForm.launch_mode || "dynamic_proxy",
        description: String(adminApplicationForm.description || "").trim() || null,
        is_enabled: Boolean(adminApplicationForm.is_enabled),
      });

      setAdminActionMsg(data?.message || "Aplicación creada correctamente.");
      setAdminActionMsgType("success");

      await refreshAfterMutation("global-applications");
      closeAdminEditor();
    } catch (e) {
      setAdminActionMsg(extractAdminErrorMessage(e));
      setAdminActionMsgType("error");
    } finally {
      setAdminActionLoading(false);
    }
  };

  const handleUpdateGlobalApplication = async () => {
    resetAdminActionMessages();

    if (!adminApplicationForm.app_id) {
      setAdminActionMsg("No se encontró el app_id.");
      setAdminActionMsgType("warning");
      return;
    }

    if (!String(adminApplicationForm.app_name || "").trim()) {
      setAdminActionMsg("Debes capturar el nombre de la aplicación.");
      setAdminActionMsgType("warning");
      return;
    }

    if (!String(adminApplicationForm.slug || "").trim()) {
      setAdminActionMsg("Debes capturar el slug.");
      setAdminActionMsgType("warning");
      return;
    }

    if (!String(adminApplicationForm.internal_url || "").trim()) {
      setAdminActionMsg("Debes capturar la Internal URL.");
      setAdminActionMsgType("warning");
      return;
    }

    if (!String(adminApplicationForm.public_url || "").trim()) {
      setAdminActionMsg("Debes capturar la Public URL.");
      setAdminActionMsgType("warning");
      return;
    }

    setAdminActionLoading(true);

    try {
      const data = await updateGlobalApplication({
        app_id: Number(adminApplicationForm.app_id),
        app_name: String(adminApplicationForm.app_name || "").trim(),
        slug: String(adminApplicationForm.slug || "").trim(),
        internal_url: String(adminApplicationForm.internal_url || "").trim(),
        public_url: String(adminApplicationForm.public_url || "").trim(),
        entry_path: String(adminApplicationForm.entry_path || "").trim() || "/",
        health_path: String(adminApplicationForm.health_path || "").trim() || "/health",
        launch_mode: adminApplicationForm.launch_mode || "dynamic_proxy",
        description: String(adminApplicationForm.description || "").trim() || null,
        is_enabled: Boolean(adminApplicationForm.is_enabled),
      });

      setAdminActionMsg(data?.message || "Aplicación actualizada correctamente.");
      setAdminActionMsgType("success");

      await refreshAfterMutation("global-applications");
      closeAdminEditor();
    } catch (e) {
      setAdminActionMsg(extractAdminErrorMessage(e));
      setAdminActionMsgType("error");
    } finally {
      setAdminActionLoading(false);
    }
  };

  const handleCreateSubscription = async () => {
    resetAdminActionMessages();

    if (!adminSubscriptionForm.client_id) {
      setAdminActionMsg("Debes seleccionar un cliente.");
      setAdminActionMsgType("warning");
      return;
    }

    if (!adminSubscriptionForm.app_id) {
      setAdminActionMsg("Debes seleccionar una aplicación.");
      setAdminActionMsgType("warning");
      return;
    }

    setAdminActionLoading(true);

    try {
      const data = await upsertSubscription({
        client_id: Number(adminSubscriptionForm.client_id),
        app_id: Number(adminSubscriptionForm.app_id),
        status: adminSubscriptionForm.status,
        is_enabled: Boolean(adminSubscriptionForm.is_enabled),
        start_date: adminSubscriptionForm.start_date || null,
        end_date: adminSubscriptionForm.end_date || null,
      });

      setAdminActionMsg(data?.message || "Suscripción creada correctamente.");
      setAdminActionMsgType("success");

      await refreshAfterMutation("subscriptions");
      closeAdminEditor();
    } catch (e) {
      setAdminActionMsg(extractAdminErrorMessage(e));
      setAdminActionMsgType("error");
    } finally {
      setAdminActionLoading(false);
    }
  };

  const handleUpdateSubscription = async () => {
    resetAdminActionMessages();

    if (!adminSubscriptionForm.client_id || !adminSubscriptionForm.app_id) {
      setAdminActionMsg("No se encontró el contexto de la suscripción.");
      setAdminActionMsgType("warning");
      return;
    }

    setAdminActionLoading(true);

    try {
      const data = await updateSubscription({
        client_id: Number(adminSubscriptionForm.client_id),
        app_id: Number(adminSubscriptionForm.app_id),
        status: adminSubscriptionForm.status,
        is_enabled: Boolean(adminSubscriptionForm.is_enabled),
        start_date: adminSubscriptionForm.start_date || null,
        end_date: adminSubscriptionForm.end_date || null,
      });

      setAdminActionMsg(data?.message || "Suscripción actualizada correctamente.");
      setAdminActionMsgType("success");

      await refreshAfterMutation("subscriptions");
      closeAdminEditor();
    } catch (e) {
      setAdminActionMsg(extractAdminErrorMessage(e));
      setAdminActionMsgType("error");
    } finally {
      setAdminActionLoading(false);
    }
  };

  const handleCreatePermission = async () => {
    resetAdminActionMessages();

    if (!adminPermissionForm.user_id) {
      setAdminActionMsg("Debes seleccionar un usuario.");
      setAdminActionMsgType("warning");
      return;
    }

    if (!adminPermissionForm.client_id) {
      setAdminActionMsg("Debes seleccionar un cliente.");
      setAdminActionMsgType("warning");
      return;
    }

    if (!adminPermissionForm.app_id) {
      setAdminActionMsg("Debes seleccionar una aplicación.");
      setAdminActionMsgType("warning");
      return;
    }

    setAdminActionLoading(true);

    try {
      const selectedUser =
        adminPermissionUsers.find(
          (row) => String(row.user_id || row.id) === String(adminPermissionForm.user_id)
        ) || null;

      const data = await createPermission({
        user_id: Number(adminPermissionForm.user_id),
        username: selectedUser?.username || String(adminPermissionForm.username || "").trim(),
        client_id: Number(adminPermissionForm.client_id),
        app_id: Number(adminPermissionForm.app_id),
        role: adminPermissionForm.role,
      });

      setAdminActionMsg(data?.message || "Permiso creado correctamente.");
      setAdminActionMsgType("success");

      await refreshAfterMutation("permissions");
      setAdminPermissionForm(getDefaultAdminPermissionForm(adminSelectedClientId));
      closeAdminEditor();
    } catch (e) {
      setAdminActionMsg(extractAdminErrorMessage(e));
      setAdminActionMsgType("error");
    } finally {
      setAdminActionLoading(false);
    }
  };

  const handleUpdatePermissionRole = async () => {
    resetAdminActionMessages();

    if (!adminPermissionForm.permission_id) {
      setAdminActionMsg("No se encontró el permission_id.");
      setAdminActionMsgType("warning");
      return;
    }

    setAdminActionLoading(true);

    try {
      const data = await updatePermissionRole({
        permission_id: Number(adminPermissionForm.permission_id),
        role: adminPermissionForm.role,
      });

      setAdminActionMsg(data?.message || "Permiso actualizado correctamente.");
      setAdminActionMsgType("success");

      await refreshAfterMutation("permissions");
      closeAdminEditor();
    } catch (e) {
      setAdminActionMsg(extractAdminErrorMessage(e));
      setAdminActionMsgType("error");
    } finally {
      setAdminActionLoading(false);
    }
  };

  const enterApp = (app) => {
    const selectedClient = getSelectedClient(app, selectedClientByApp);

    if (!selectedClient?.is_accessible) {
      setMsg("La app no está disponible para el cliente seleccionado.");
      setMsgType("warning");
      return;
    }

    const url = buildLaunchUrl(app.app_id, selectedClient.id);
    window.location.href = url;
  };

  const adminSelectedClientName = useMemo(
    () => getAdminSelectedClientName(adminClients, adminSelectedClientId),
    [adminClients, adminSelectedClientId]
  );

  if (initializing) {
    return (
      <div className="app-container">
        <header className="rs-shell-header">
          <div className="rs-shell-left">
            <picture>
              <source srcSet="/logos/rodelsoft-monogram-hex.svg" type="image/svg+xml" />
              <img
                src="/logos/rodelsoft-monogram-hex.png"
                alt="RodelSoft"
                className="rs-shell-logo"
              />
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
          <p className="app-footer-text">
            © 2026 RodelSoft. Todos los derechos reservados.
          </p>
        </footer>
      </div>
    );
  }

  return (
    <div className="app-container">
      <Header
        authed={authed}
        username={username}
        userMenuOpen={userMenuOpen}
        setUserMenuOpen={setUserMenuOpen}
        fetchMyApps={fetchMyApps}
        hasAdminScope={hasAdminScope}
        openAdminModal={openAdminModal}
        logout={logout}
      />

      <main className="main-content">
        {msg && <div className={`alert ${msgType}`}>{msg}</div>}

        {!authed ? (
          <LoginView
            username={username}
            setUser={setUser}
            password={password}
            setPass={setPass}
            loading={loading}
            login={login}
          />
        ) : (
          <AppsView
            rawApps={rawApps}
            selectedClientByApp={selectedClientByApp}
            setSelectedClientByApp={setSelectedClientByApp}
            enterApp={enterApp}
          />
        )}
      </main>

      <AdminModal
        adminModalOpen={adminModalOpen}
        closeAdminModal={closeAdminModal}
        adminLoadingClients={adminLoadingClients}
        adminClients={adminClients}
        adminSelectedClientId={adminSelectedClientId}
        setAdminSelectedClientId={setAdminSelectedClientId}
        fetchAdminClients={fetchAdminClients}
        adminSelectedClientName={adminSelectedClientName}
        isSystemAdmin={isSystemAdmin}
        adminTab={adminTab}
        setAdminTab={setAdminTab}
        adminActionMsg={adminActionMsg}
        adminActionMsgType={adminActionMsgType}
        adminLoadingData={adminLoadingData}
        adminGlobalUsers={adminGlobalUsers}
        adminGlobalApplications={adminGlobalApplications}
        adminGlobalClients={adminGlobalClients}
        adminUsers={adminUsers}
        adminSubscriptions={adminSubscriptions}
        adminPermissions={adminPermissions}
        openAdminEditor={openAdminEditor}
        adminEditorOpen={adminEditorOpen}
        closeAdminEditor={closeAdminEditor}
        adminEditorType={adminEditorType}
        adminEditorMode={adminEditorMode}
        adminActionLoading={adminActionLoading}
        adminCreateUserForm={adminCreateUserForm}
        setAdminCreateUserForm={setAdminCreateUserForm}
        adminCreateClientForm={adminCreateClientForm}
        setAdminCreateClientForm={setAdminCreateClientForm}
        adminApplicationForm={adminApplicationForm}
        setAdminApplicationForm={setAdminApplicationForm}
        adminSubscriptionForm={adminSubscriptionForm}
        setAdminSubscriptionForm={setAdminSubscriptionForm}
        adminPermissionForm={adminPermissionForm}
        setAdminPermissionForm={setAdminPermissionForm}
        adminAppsCatalog={adminAppsCatalog}
        adminPermissionUsers={adminPermissionUsers}
        adminPermissionApps={adminPermissionApps}
        handleCreateGlobalUser={handleCreateGlobalUser}
        handleUpdateGlobalUser={handleUpdateGlobalUser}
        handleCreateGlobalClient={handleCreateGlobalClient}
        handleUpdateGlobalClient={handleUpdateGlobalClient}
        handleCreateGlobalApplication={handleCreateGlobalApplication}
        handleUpdateGlobalApplication={handleUpdateGlobalApplication}
        handleCreateSubscription={handleCreateSubscription}
        handleUpdateSubscription={handleUpdateSubscription}
        handleCreatePermission={handleCreatePermission}
        handleUpdatePermissionRole={handleUpdatePermissionRole}
        reloadCurrentAdminTab={() => fetchAdminTabData(adminTab, adminSelectedClientId)}
      />

      <footer className="app-footer">
        <p className="app-footer-text">
          © 2026 RodelSoft. Todos los derechos reservados.
        </p>
      </footer>
    </div>
  );
}