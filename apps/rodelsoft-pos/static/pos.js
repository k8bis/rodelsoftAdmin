let categories = [];
        let products = [];
        let cart = {};

        async function loadData() {
            try {
                const [categoriesRes, productsRes] = await Promise.all([
                    fetch('/api/categories'),
                    fetch('/api/products')
                ]);

                categories = await categoriesRes.json();
                products = await productsRes.json();

                renderCategories();
                renderProducts();
            } catch (error) {
                console.error('Error cargando datos:', error);
            }
        }

        function renderCategories() {
            const container = document.getElementById('categoriesContainer');
            container.innerHTML = '<button class="category-btn active" data-category="all">Todas</button>';

            categories.forEach(category => {
                const btn = document.createElement('button');
                btn.className = 'category-btn';
                btn.textContent = category.name;
                btn.dataset.category = category.id;
                btn.onclick = () => filterByCategory(category.id);
                container.appendChild(btn);
            });
        }

        function renderProducts(filteredProducts = products) {
            const grid = document.getElementById('productsGrid');
            grid.innerHTML = '';

            filteredProducts.forEach(product => {
                const card = document.createElement('div');
                card.className = 'product-card';
                card.onclick = () => addToCart(product.id);

                card.innerHTML = `
                    <div class="product-name">${product.name}</div>
                    <div class="product-price">$${product.price.toFixed(2)}</div>
                `;

                grid.appendChild(card);
            });
        }

        function filterByCategory(categoryId) {
            document.querySelectorAll('.category-btn').forEach(btn => btn.classList.remove('active'));
            event.target.classList.add('active');

            if (categoryId === 'all') {
                renderProducts();
            } else {
                const filtered = products.filter(p => p.category_id == categoryId);
                renderProducts(filtered);
            }
        }

        function addToCart(productId) {
            const product = products.find(p => p.id == productId);
            if (!product) return;

            if (cart[productId]) {
                cart[productId].quantity += 1;
            } else {
                cart[productId] = { ...product, quantity: 1 };
            }

            renderCart();
        }

        function renderCart() {
            const container = document.getElementById('cartItems');
            const totalEl = document.getElementById('cartTotal');

            container.innerHTML = '';
            let total = 0;

            Object.values(cart).forEach(item => {
                const itemTotal = item.price * item.quantity;
                total += itemTotal;

                const itemEl = document.createElement('div');
                itemEl.className = 'cart-item';
                itemEl.innerHTML = `
                    <div>
                        <div style="font-weight: bold;">${item.name}</div>
                        <div style="color: var(--text-light); font-size: 0.9rem;">$${item.price.toFixed(2)} c/u</div>
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
            if (newQuantity <= 0) {
                delete cart[productId];
            } else {
                cart[productId].quantity = newQuantity;
            }
            renderCart();
        }

        async function checkout() {
            if (Object.keys(cart).length === 0) {
                alert('El carrito está vacío');
                return;
            }

            const items = Object.values(cart).map(item => ({
                product_id: item.id,
                quantity: item.quantity
            }));

            try {
                const response = await fetch('/api/sales', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        items: items,
                        payment_method: 'cash'
                    })
                });

                if (response.ok) {
                    alert('Venta procesada exitosamente!');
                    cart = {};
                    renderCart();
                    loadData();
                } else {
                    const error = await response.json();
                    alert('Error: ' + error.detail);
                }
            } catch (error) {
                console.error('Error procesando venta:', error);
                alert('Error procesando la venta');
            }
        }

        document.getElementById('searchInput').addEventListener('input', function(e) {
            const searchTerm = e.target.value.toLowerCase();
            const filtered = products.filter(p => p.name.toLowerCase().includes(searchTerm));
            renderProducts(filtered);
        });

        document.getElementById('checkoutBtn').addEventListener('click', checkout);
        document.getElementById('refreshBtn').addEventListener('click', function() {
            loadData();
        });

        const APP_MENU_URL = "__APP_MENU_URL__";
        const LOGOUT_REDIRECT_URL = "__LOGOUT_REDIRECT_URL__";

        const userMenuBtn = document.getElementById('userMenuBtn');
        const userDropdown = document.getElementById('userDropdown');

        if (userMenuBtn && userDropdown) {
            userMenuBtn.addEventListener('click', function(event) {
                event.stopPropagation();
                userDropdown.classList.toggle('show');
            });

            window.addEventListener('click', function() {
                userDropdown.classList.remove('show');
            });

            document.getElementById('logoutBtn').addEventListener('click', async function() {
                try {
                    await fetch('/logout', { method: 'POST' });
                } catch (e) {
                    console.error('Error en logout', e);
                }
                window.location.href = LOGOUT_REDIRECT_URL;
            });

            document.getElementById('appsMenuBtn').addEventListener('click', function() {
                window.location.href = APP_MENU_URL;
            });
        }

        loadData();