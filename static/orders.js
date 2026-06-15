let ordersCache = [];

async function fetchOrders() {
  const res = await fetchWithAuth('/api/orders');
  if (!res.ok) throw new Error(await parseApiError(res, 'Failed to load orders'));
  return res.json();
}

async function createOrder(payload) {
  const res = await fetchWithAuth('/api/orders', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(await parseApiError(res, 'Failed to create order'));
  return res.json();
}

async function updateOrderStatus(invoice, status) {
  const res = await fetchWithAuth(`/api/orders/${invoice}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ status }),
  });
  if (!res.ok) throw new Error(await parseApiError(res, 'Failed to update order'));
  return res.json();
}

async function deleteOrder(invoice) {
  const res = await fetchWithAuth(`/api/orders/${invoice}`, { method: 'DELETE' });
  if (!res.ok) throw new Error(await parseApiError(res, 'Failed to delete order'));
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

function filterOrders(items) {
  const query = document.getElementById('ordersSearch')?.value.trim().toLowerCase() || '';
  const filter = document.getElementById('ordersFilter')?.value || 'all';
  const dateFrom = document.getElementById('ordersDateFrom')?.value || '';
  const dateTo = document.getElementById('ordersDateTo')?.value || '';

  return items.filter((order) => {
    const matchesSearch = query === '' ||
      order.invoice_number?.toLowerCase().includes(query) ||
      order.customer?.toLowerCase().includes(query);

    const matchesFilter = filter === 'all' || order.status === filter;

    let matchesDate = true;
    if (order.created_at && (dateFrom || dateTo)) {
      const orderDate = order.created_at.slice(0, 10);
      if (dateFrom && orderDate < dateFrom) matchesDate = false;
      if (dateTo && orderDate > dateTo) matchesDate = false;
    }

    return matchesSearch && matchesFilter && matchesDate;
  });
}

function renderOrders(list) {
  const container = document.getElementById('ordersList');
  const filtered = Array.isArray(list) ? list : [];
  container.innerHTML = '';

  if (filtered.length === 0) {
    container.innerHTML = `
      <div class="empty-state">
        <i>📭</i>
        <p>No orders match your search. Try a different keyword or clear the filter.</p>
      </div>
    `;
    return;
  }

  for (const o of filtered) {
    const row = document.createElement('div');
    row.className = 'order-row';
    row.innerHTML = `
      <div class="or-id">${escapeHtml(o.invoice_number)}</div>
      <div class="or-customer">${escapeHtml(o.customer || 'Unknown')}</div>
      <div class="or-date">${escapeHtml(o.created_at || '')}</div>
      <div class="or-amount">₹ ${parseFloat(o.total || 0).toFixed(2)}</div>
      <div style="margin-left:12px;display:flex;gap:8px;align-items:center">
        <select data-invoice="${escapeHtml(o.invoice_number)}" data-prev="${escapeHtml(o.status)}" class="status-select">
          <option value="draft" ${o.status === 'draft' ? 'selected' : ''}>Draft</option>
          <option value="paid" ${o.status === 'paid' ? 'selected' : ''}>Paid</option>
          <option value="cancelled" ${o.status === 'cancelled' ? 'selected' : ''}>Cancelled</option>
        </select>
        <button data-invoice="${escapeHtml(o.invoice_number)}" class="send-btn invoice-btn" type="button" data-min-role="manager">Download PDF</button>
        <button data-invoice="${escapeHtml(o.invoice_number)}" class="send-btn delete-order-btn" type="button" style="background:#a33;color:#fff">Delete</button>
      </div>
    `;
    container.appendChild(row);
  }

  container.querySelectorAll('.status-select').forEach((el) => {
    el.addEventListener('change', async (e) => {
      const select = e.currentTarget;
      const invoice = select.getAttribute('data-invoice');
      const previous = select.getAttribute('data-prev');
      const status = select.value;
      try {
        const updated = await updateOrderStatus(invoice, status);
        const index = ordersCache.findIndex((order) => order.invoice_number === invoice);
        if (index >= 0) {
          ordersCache[index] = updated;
        }
        select.setAttribute('data-prev', status);
        toast('Order updated', 'info', 3000);
        broadcastDataChange('orders');
      } catch (err) {
        console.error(err);
        select.value = previous;
        toast(err.message || 'Failed to update order', 'error', 6000);
      }
    });
  });

  container.querySelectorAll('.invoice-btn').forEach((el) => {
    el.addEventListener('click', (e) => {
      const invoice = e.currentTarget.getAttribute('data-invoice');
      downloadInvoice(invoice);
    });
  });

  container.querySelectorAll('.delete-order-btn').forEach((el) => {
    el.addEventListener('click', async (e) => {
      const invoice = e.currentTarget.getAttribute('data-invoice');
      if (!confirm(`Delete order ${invoice}? Only draft/cancelled orders can be deleted.`)) return;
      try {
        await deleteOrder(invoice);
        ordersCache = ordersCache.filter((order) => order.invoice_number !== invoice);
        renderOrders(filterOrders(ordersCache));
        toast('Order deleted', 'info', 3000);
        broadcastDataChange('orders');
      } catch (err) {
        console.error(err);
        toast(err.message || 'Failed to delete order', 'error', 6000);
      }
    });
  });
}

async function loadAndRender() {
  try {
    ordersCache = await fetchOrders();
    renderOrders(filterOrders(ordersCache));
  } catch (err) {
    console.error(err);
    toast(err.message || 'Failed to load orders', 'error', 6000);
  }
}

window.addEventListener('DOMContentLoaded', async () => {
  await initNav();
  loadAndRender();
  registerDataRefreshHandler(() => loadAndRender(), 'orders');

  const searchInput = document.getElementById('ordersSearch');
  const filterSelect = document.getElementById('ordersFilter');
  const dateFrom = document.getElementById('ordersDateFrom');
  const dateTo = document.getElementById('ordersDateTo');

  searchInput?.addEventListener('input', () => renderOrders(filterOrders(ordersCache)));
  filterSelect?.addEventListener('change', () => renderOrders(filterOrders(ordersCache)));
  dateFrom?.addEventListener('change', () => renderOrders(filterOrders(ordersCache)));
  dateTo?.addEventListener('change', () => renderOrders(filterOrders(ordersCache)));

  document.getElementById('exportOrdersBtn')?.addEventListener('click', () => {
    downloadExport('/api/export/orders', 'orders.csv');
  });

  document.getElementById('orderForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const customer = document.getElementById('orderCustomer').value.trim();
    const productName = document.getElementById('orderProduct').value.trim();
    const qty = parseFloat(document.getElementById('orderQty').value || 0);
    if (!customer || !productName || qty <= 0) {
      toast('Customer, product, and quantity are required', 'error', 5000);
      return;
    }

    try {
      await createOrder({
        customer,
        items: [{ name: productName, qty }],
        status: document.getElementById('orderStatus').value || 'paid',
      });
      toast('Order created', 'info', 3000);
      e.target.reset();
      broadcastDataChange(['orders', 'inventory', 'customers']);
      loadAndRender();
    } catch (err) {
      console.error(err);
      toast(err.message || 'Failed to create order', 'error', 6000);
    }
  });
});
