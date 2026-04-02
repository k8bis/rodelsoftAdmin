console.log("POS_JS_V4_CONTEXT_FIX");

let categories = [];
let products = [];
let cart = {};

const NAV = window.RODELSOFT_NAV || {};
const POSCFG = window.POS_CONFIG || {};

const APP_BASE_PATH =
  NAV.APP_HOME_URL ||
  POSCFG.APP_BASE_PATH ||
  "/pos";

const APP_MENU_URL =
  NAV.APP_MENU_URL ||
  POSCFG.APP_MENU_URL ||
  "/";

const LOGOUT_URL =
  NAV.LOGOUT_URL ||
  POSCFG.LOGOUT_URL ||
  `${APP_BASE_PATH}/logout`;

const LOGIN_FALLBACK_URL =
  NAV.LOGIN_FALLBACK_URL ||
  POSCFG.LOGIN_FALLBACK_URL ||
  POSCFG.LOGOUT_REDIRECT_URL ||
  "/";

// =========================
// Contexto actual (app_id / client_id)
// =========================
const currentUrl = new URL(window.location.href);
const APP_ID = currentUrl.searchParams.get("app_id");
const CLIENT_ID = currentUrl.searchParams.get("client_id");

const CONTEXT_QUERY = new URLSearchParams();
if (APP_ID) CONTEXT_QUERY.set("app_id", APP_ID);
if (CLIENT_ID) CONTEXT_QUERY.set("client_id", CLIENT_ID);

const CONTEXT_SUFFIX = CONTEXT_QUERY.toString() ? `?${CONTEXT_QUERY.toString()}` : "";

const API_BASE = `${APP_BASE_PATH}/api`;
const SESSION_CHECK_URL = `${APP_BASE_PATH}/session-check${CONTEXT_SUFFIX}`;
const CATEGORIES_URL = `${API_BASE}/categories${CONTEXT_SUFFIX}`;
const PRODUCTS_URL = `${API_BASE}/products${CONTEXT_SUFFIX}`;
const SALES_URL = `${API_BASE}/sales${CONTEXT_SUFFIX}`;

console.log("APP_BASE_PATH =", APP_BASE_PATH);
console.log("API_BASE =", API_BASE);
console.log("APP_MENU_URL =", APP_MENU_URL);
console.log("LOGOUT_URL =", LOGOUT_URL);
console.log("LOGIN_FALLBACK_URL =", LOGIN_FALLBACK_URL);
console.log("APP_ID =", APP_ID);
console.log("CLIENT_ID =", CLIENT_ID);
console.log("CONTEXT_SUFFIX =", CONTEXT_SUFFIX);
console.log("SESSION_CHECK_URL =", SESSION_CHECK_URL);
console.log("CATEGORIES_URL =", CATEGORIES_URL);
console.log("PRODUCTS_URL =", PRODUCTS_URL);
console.log("SALES_URL =", SALES_URL);

function redirectToLogin() {
    window.location.replace(LOGIN_FALLBACK_URL);
}

async function validateSessionOrRedirect() {
    try {
        const response = await fetch(SESSION_CHECK_URL, {
            method: "GET",
            credentials: "same-origin",
            cache: "no-store",
            redirect: "follow"
        });

        console.log("validateSessionOrRedirect status =", response.status);
        console.log("validateSessionOrRedirect redirected =", response.redirected);
        console.log("validateSessionOrRedirect final url =", response.url);

        if (response.redirected) {
            console.warn("Sesión inválida detectada por redirect del servidor. Redirigiendo al login...");
            redirectToLogin();
            return false;
        }

        if (!response.ok) {
            console.warn("Sesión inválida o expirada. Redirigiendo al login...");
            redirectToLogin();
            return false;
        }

        return true;
    } catch (error) {
        console.error("Error validando sesión:", error);
        redirectToLogin();
        return false;
    }
}

async function handleApiResponse(response, endpointName = "API") {
    if (response.redirected) {
        console.warn(`${endpointName} respondió con redirect. Redirigiendo al login...`);
        redirectToLogin();
        throw new Error("Sesión expirada o inválida");
    }

    if (response.status === 401) {
        console.warn(`${endpointName} respondió 401. Redirigiendo al login...`);
        redirectToLogin();
        throw new Error("Sesión expirada o inválida");
    }

    return response;
}

async function loadData() {
    try {
        console.log("Cargando categorías desde:", CATEGORIES_URL);
        console.log("Cargando productos desde:", PRODUCTS_URL);

        const [categoriesResRaw, productsResRaw] = await Promise.all([
            fetch(CATEGORIES_URL, { credentials: "same-origin", cache: "no-store", redirect: "follow" }),
            fetch(PRODUCTS_URL, { credentials: "same-origin", cache: "no-store", redirect: "follow" })
        ]);

        const categoriesRes = await handleApiResponse(categoriesResRaw, "categories");
        const productsRes = await handleApiResponse(productsResRaw, "products");

        console.log("categoriesRes.status =", categoriesRes.status);
        console.log("productsRes.status =", productsRes.status);

        if (!categoriesRes.ok) {
            const text = await categoriesRes.text();
            console.error("Respuesta /categories:", text);
            throw new Error(`Error cargando categorías: ${categoriesRes.status}`);
        }

        if (!productsRes.ok) {
            const text = await productsRes.text();
            console.error("Respuesta /products:", text);
            throw new Error(`Error cargando productos: ${productsRes.status}`);
        }

        categories = await categoriesRes.json();
        products = await productsRes.json();

        console.log("Categorías cargadas:", categories);
        console.log("Productos cargados:", products);

        renderCategories();
        renderProducts(products);
        renderCart();

    } catch (error) {
        console.error("Error cargando catálogo:", error);

        if (String(error.message).includes("Sesión expirada o inválida")) {
            return;
        }

        const grid = document.getElementById("productsGrid");
        if (grid) {
            grid.innerHTML = `
                <div class="error-box">
                    No se pudo cargar el catálogo de productos.<br>
                    Revisa consola y logs del contenedor.
                </div>
            `;
        }
    }
}

function renderCategories() {
    const container = document.getElementById("categoriesContainer");
    if (!container) {
        console.warn("No existe #categoriesContainer");
        return;
    }

    container.innerHTML = "";

    const allBtn = document.createElement("button");
    allBtn.className = "category-btn active";
    allBtn.textContent = "Todas";
    allBtn.dataset.category = "all";
    allBtn.addEventListener("click", () => filterByCategory("all", allBtn));
    container.appendChild(allBtn);

    categories.forEach(category => {
        const btn = document.createElement("button");
        btn.className = "category-btn";
        btn.textContent = category.name;
        btn.dataset.category = category.id;
        btn.addEventListener("click", () => filterByCategory(category.id, btn));
        container.appendChild(btn);
    });
}

function renderProducts(filteredProducts = products) {
    const grid = document.getElementById("productsGrid");
    if (!grid) {
        console.warn("No existe #productsGrid");
        return;
    }

    grid.innerHTML = "";

    if (!filteredProducts || filteredProducts.length === 0) {
        grid.innerHTML = `<div class="loading-box">No hay productos disponibles.</div>`;
        return;
    }

    filteredProducts.forEach(product => {
        const card = document.createElement("div");
        card.className = "product-card";
        card.addEventListener("click", () => addToCart(product.id));

        const stock = product.stock_quantity ?? 0;
        const price = Number(product.price || 0);

        card.innerHTML = `
            <div class="product-name">${product.name}</div>
            <div class="product-price">$${price.toFixed(2)}</div>
            <div class="product-stock">Stock: ${stock}</div>
        `;

        grid.appendChild(card);
    });
}

function filterByCategory(categoryId, clickedBtn = null) {
    document.querySelectorAll(".category-btn").forEach(btn => btn.classList.remove("active"));

    if (clickedBtn) {
        clickedBtn.classList.add("active");
    }

    if (categoryId === "all") {
        renderProducts(products);
        return;
    }

    const filtered = products.filter(p => String(p.category_id) === String(categoryId));
    renderProducts(filtered);
}

function addToCart(productId) {
    const product = products.find(p => String(p.id) === String(productId));
    if (!product) return;

    if (cart[productId]) {
        if (cart[productId].quantity + 1 > (product.stock_quantity ?? 0)) {
            alert(`Stock insuficiente para ${product.name}`);
            return;
        }
        cart[productId].quantity += 1;
    } else {
        if ((product.stock_quantity ?? 0) < 1) {
            alert(`Sin stock disponible para ${product.name}`);
            return;
        }
        cart[productId] = { ...product, quantity: 1 };
    }

    renderCart();
}

function renderCart() {
    const container = document.getElementById("cartItems");
    const totalEl = document.getElementById("cartTotal");

    if (!container || !totalEl) return;

    container.innerHTML = "";
    let total = 0;

    const items = Object.values(cart);

    if (items.length === 0) {
        container.innerHTML = `<div class="empty-cart">El carrito está vacío.</div>`;
        totalEl.textContent = "Total: $0.00";
        return;
    }

    items.forEach(item => {
        const itemTotal = Number(item.price) * item.quantity;
        total += itemTotal;

        const itemEl = document.createElement("div");
        itemEl.className = "cart-item";
        itemEl.innerHTML = `
            <div>
                <div style="font-weight: bold;">${item.name}</div>
                <div style="color: #666; font-size: 0.9rem;">$${Number(item.price).toFixed(2)} c/u</div>
            </div>
            <div class="quantity-controls">
                <button class="quantity-btn" onclick="updateQuantity(${item.id}, ${item.quantity - 1})">-</button>
                <span>${item.quantity}</span>
                <button class="quantity-btn" onclick="updateQuantity(${item.id}, ${item.quantity + 1})">+</button>
            </div>
            <div style="font-weight: bold;">$${itemTotal.toFixed(2)}</div>
        `;
        container.appendChild(itemEl);
    });

    totalEl.textContent = `Total: $${total.toFixed(2)}`;
}

function updateQuantity(productId, newQuantity) {
    const product = products.find(p => String(p.id) === String(productId));
    if (!product) return;

    if (newQuantity <= 0) {
        delete cart[productId];
    } else {
        if (newQuantity > (product.stock_quantity ?? 0)) {
            alert(`Stock insuficiente para ${product.name}`);
            return;
        }
        if (cart[productId]) {
            cart[productId].quantity = newQuantity;
        }
    }

    renderCart();
}

async function checkout() {
    const items = Object.values(cart);

    if (items.length === 0) {
        alert("El carrito está vacío.");
        return;
    }

    const payload = {
        items: items.map(item => ({
            product_id: item.id,
            quantity: item.quantity
        })),
        payment_method: "cash",
        notes: "Venta generada desde POS web"
    };

    console.log("Checkout payload:", payload);

    try {
        const responseRaw = await fetch(SALES_URL, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            credentials: "same-origin",
            cache: "no-store",
            redirect: "follow",
            body: JSON.stringify(payload)
        });

        const response = await handleApiResponse(responseRaw, "sales");

        console.log("checkout response.status =", response.status);

        const rawText = await response.text();
        console.log("checkout raw response =", rawText);

        let result;
        try {
            result = rawText ? JSON.parse(rawText) : {};
        } catch {
            result = { detail: rawText || "Respuesta no JSON del servidor" };
        }

        if (!response.ok) {
            const msg = result.detail || `Error HTTP ${response.status}`;
            alert(`No se pudo procesar la venta: ${msg}`);
            return;
        }

        alert(`Venta procesada correctamente. Folio: ${result.id ?? "N/A"}`);

        cart = {};
        await loadData();

    } catch (error) {
        console.error("Error en checkout:", error);

        if (String(error.message).includes("Sesión expirada o inválida")) {
            return;
        }

        alert("Error inesperado al procesar la venta.");
    }
}

function setupSearch() {
    const searchInput = document.getElementById("searchInput");
    if (!searchInput) {
        console.warn("No existe #searchInput");
        return;
    }

    searchInput.addEventListener("input", function (e) {
        const searchTerm = e.target.value.toLowerCase().trim();

        if (!searchTerm) {
            renderProducts(products);
            return;
        }

        const filtered = products.filter(p =>
            String(p.name || "").toLowerCase().includes(searchTerm)
        );

        renderProducts(filtered);
    });
}

function setupUserMenu() {
    const userMenuBtn = document.getElementById("userMenuBtn");
    const userDropdown = document.getElementById("userDropdown");
    const appsMenuBtn = document.getElementById("appsMenuBtn");
    const logoutBtn = document.getElementById("logoutBtn");

    if (!userMenuBtn || !userDropdown) return;

    userMenuBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        userDropdown.classList.toggle("show");
    });

    document.addEventListener("click", () => {
        userDropdown.classList.remove("show");
    });

    userDropdown.addEventListener("click", (e) => {
        e.stopPropagation();
    });

    if (appsMenuBtn) {
        appsMenuBtn.addEventListener("click", () => {
            window.location.href = APP_MENU_URL;
        });
    }

    if (logoutBtn) {
        logoutBtn.addEventListener("click", async () => {
            try {
                console.log("Ejecutando logout centralizado en:", LOGOUT_URL);

                const response = await fetch(LOGOUT_URL, {
                    method: "POST",
                    credentials: "include",
                    cache: "no-store",
                    redirect: "follow"
                });

                console.log("logout response.status =", response.status);
                console.log("logout response.redirected =", response.redirected);
                console.log("logout response.url =", response.url);

                if (!response.ok && response.status !== 302) {
                    console.warn("Logout devolvió estado inesperado:", response.status);
                }
            } catch (error) {
                console.warn("Error ejecutando logout centralizado:", error);
            }

            // Siempre regresar al login/portal después de invalidar sesión
            window.location.replace(LOGIN_FALLBACK_URL);
        });
    }
}

function setupButtons() {
    const refreshBtn = document.getElementById("refreshBtn");
    const checkoutBtn = document.getElementById("checkoutBtn");

    if (refreshBtn) {
        refreshBtn.addEventListener("click", loadData);
    }

    if (checkoutBtn) {
        checkoutBtn.addEventListener("click", checkout);
    }
}

async function bootPOS() {
    // Si no hay contexto, mejor salir limpio al login/catálogo
    if (!APP_ID || !CLIENT_ID) {
        console.warn("Faltan app_id o client_id en la URL. Redirigiendo...");
        redirectToLogin();
        return;
    }

    const isValid = await validateSessionOrRedirect();
    if (!isValid) return;

    setupSearch();
    setupButtons();
    setupUserMenu();
    loadData();
}

document.addEventListener("DOMContentLoaded", function () {
    bootPOS();
});

// Importante para botón Atrás / bfcache
window.addEventListener("pageshow", async function () {
    const isValid = await validateSessionOrRedirect();
    if (!isValid) return;
});