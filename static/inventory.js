let inventoryCache = [];

async function fetchProducts() {
  const res = await fetchWithAuth('/api/inventory');
  if (!res.ok) throw new Error(await parseApiError(res, 'Failed to load inventory'));
  return res.json();
}

async function createProduct(payload) {
  const res = await fetchWithAuth('/api/inventory', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(await parseApiError(res, 'Failed to create product'));
  return res.json();
}

async function updateProduct(productId, payload) {
  const res = await fetchWithAuth(`/api/inventory/${productId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(await parseApiError(res, 'Failed to update product'));
  return res.json();
}

async function deleteProduct(productId) {
  const res = await fetchWithAuth(`/api/inventory/${productId}`, { method: 'DELETE' });
  if (!res.ok) throw new Error(await parseApiError(res, 'Failed to delete product'));
  return res.json();
}

function toast(message, type = 'info', timeout = 4000) {
  const container = document.getElementById('toastContainer');
  if (!container) return;
  const el = document.createElement('div');
  el.className = 'toast ' + type;
  el.textContent = message;
  el.style.padding = '10px 14px';
  el.style.background = type === 'error' ? 'rgba(170,40,40,0.9)' : 'rgba(30,30,30,0.95)';
  el.style.color = 'white';
  el.style.borderRadius = '8px';
  container.appendChild(el);
  setTimeout(() => el.remove(), timeout);
}

function filterInventory(items) {
  const query = document.getElementById('inventorySearch')?.value.trim().toLowerCase() || '';
  const filter = document.getElementById('inventoryFilter')?.value || 'all';

  return items.filter((item) => {
    const matchesSearch = query === '' ||
      item.name.toLowerCase().includes(query) ||
      (item.sku || '').toLowerCase().includes(query) ||
      (item.unit || '').toLowerCase().includes(query);

    let matchesFilter = true;
    if (filter === 'low') {
      matchesFilter = item.quantity <= (item.low_stock_threshold || 0);
    } else if (filter === 'in_stock') {
      matchesFilter = item.quantity > (item.low_stock_threshold || 0);
    }

    return matchesSearch && matchesFilter;
  });
}

function renderProducts(list) {
  const grid = document.getElementById('inventoryGrid');
  const banner = document.getElementById('lowStockBanner');
  const filtered = Array.isArray(list) ? list : [];

  grid.innerHTML = '';
  if (filtered.length === 0) {
    grid.innerHTML = `
      <div class="empty-state">
        <i>⚠️</i>
        <p>No inventory items match your search or filter. Add products or adjust the filters.</p>
      </div>
    `;
    if (banner) {
      banner.hidden = true;
      banner.textContent = '';
    }
    return;
  }

  const lowStockCount = filtered.filter((item) => item.quantity <= (item.low_stock_threshold || 0)).length;
  if (banner) {
    if (lowStockCount > 0) {
      banner.hidden = false;
      banner.textContent = `${lowStockCount} low-stock product(s) visible. Review and restock soon.`;
    } else {
      banner.hidden = true;
      banner.textContent = '';
    }
  }

  for (const p of filtered) {
    const card = document.createElement('div');
    card.className = 'product-card' + (p.quantity <= (p.low_stock_threshold || 0) ? ' low-stock' : '');
    card.innerHTML = `
      <div class="pc-name">${escapeHtml(p.name)}</div>
      <div class="pc-sku">${escapeHtml(p.sku || '')}</div>
      <div style="display:flex;align-items:center;gap:8px;margin-top:8px">
        <div>
          <div class="pc-qty">${escapeHtml(p.quantity)}</div>
          <div class="pc-unit">${escapeHtml(p.unit || '')}</div>
        </div>
        <div style="margin-left:auto;text-align:right">
          <div class="pc-price">₹ ${parseFloat(p.price || 0).toFixed(2)}</div>
        </div>
      </div>
      <div style="margin-top:8px;display:flex;gap:8px">
        <button class="send-btn edit-btn" data-id="${p.id}">Edit</button>
        <button class="send-btn" style="background:#a33;color:#fff" data-id="${p.id}" data-delete>Delete</button>
      </div>
    `;
    grid.appendChild(card);
  }

  grid.querySelectorAll('.edit-btn').forEach((btn) => {
    btn.addEventListener('click', (e) => {
      const id = e.currentTarget.getAttribute('data-id');
      const product = filtered.find((x) => String(x.id) === String(id));
      if (!product) return;
      document.getElementById('p_id').value = product.id;
      document.getElementById('p_name').value = product.name;
      document.getElementById('p_sku').value = product.sku || '';
      document.getElementById('p_price').value = product.price || 0;
      document.getElementById('p_qty').value = product.quantity || 0;
      document.getElementById('p_unit').value = product.unit || 'pcs';
    });
  });

  grid.querySelectorAll('[data-delete]').forEach((btn) => {
    btn.addEventListener('click', async (e) => {
      const id = e.currentTarget.getAttribute('data-id');
      if (!confirm('Delete this product?')) return;
      try {
        await deleteProduct(id);
        toast('Product deleted', 'info', 3000);
        broadcastDataChange('inventory');
        loadAndRender();
      } catch (err) {
        console.error(err);
        toast(err.message || 'Failed to delete product', 'error', 6000);
      }
    });
  });
}

async function loadAndRender() {
  try {
    inventoryCache = await fetchProducts();
    renderProducts(filterInventory(inventoryCache));
  } catch (err) {
    console.error(err);
    toast(err.message || 'Failed to load products', 'error', 6000);
  }
}

window.addEventListener('DOMContentLoaded', async () => {
  await initNav();
  loadAndRender();
  registerDataRefreshHandler(() => loadAndRender(), 'inventory');

  const searchInput = document.getElementById('inventorySearch');
  const filterSelect = document.getElementById('inventoryFilter');

  searchInput?.addEventListener('input', () => renderProducts(filterInventory(inventoryCache)));
  filterSelect?.addEventListener('change', () => renderProducts(filterInventory(inventoryCache)));

  const form = document.getElementById('productForm');
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const id = document.getElementById('p_id').value;
    const payload = {
      name: document.getElementById('p_name').value,
      sku: document.getElementById('p_sku').value,
      price: parseFloat(document.getElementById('p_price').value || 0),
      quantity: parseFloat(document.getElementById('p_qty').value || 0),
      unit: document.getElementById('p_unit').value || 'pcs',
    };
    try {
      if (id) {
        await updateProduct(id, payload);
        toast('Product updated', 'info', 3000);
      } else {
        await createProduct(payload);
        toast('Product created', 'info', 3000);
      }
      form.reset();
      document.getElementById('p_id').value = '';
      broadcastDataChange('inventory');
      loadAndRender();
    } catch (err) {
      console.error(err);
      toast(err.message || 'Failed to save product', 'error', 6000);
    }
  });

  const cancelBtn = document.getElementById('cancelEdit');
  if (cancelBtn) cancelBtn.addEventListener('click', () => {
    document.getElementById('p_id').value = '';
    document.getElementById('productForm').reset();
  });
});
