let customersCache = [];
let selectedCustomerId = null;

async function fetchCustomers() {
  const res = await fetchWithAuth('/api/customers');
  if (!res.ok) throw new Error(await parseApiError(res, 'Failed to load customers'));
  return res.json();
}

async function fetchCustomerProfile(id) {
  const res = await fetchWithAuth(`/api/customers/${id}`);
  if (!res.ok) throw new Error(await parseApiError(res, 'Failed to load customer'));
  return res.json();
}

async function createCustomer(payload) {
  const res = await fetchWithAuth('/api/customers', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(await parseApiError(res, 'Failed to create customer'));
  return res.json();
}

async function updateCustomer(customerId, payload) {
  const res = await fetchWithAuth(`/api/customers/${customerId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(await parseApiError(res, 'Failed to update customer'));
  return res.json();
}

async function deleteCustomer(customerId) {
  const res = await fetchWithAuth(`/api/customers/${customerId}`, { method: 'DELETE' });
  if (!res.ok) throw new Error(await parseApiError(res, 'Failed to delete customer'));
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

function filterCustomers(items) {
  const query = document.getElementById('customersSearch')?.value.trim().toLowerCase() || '';
  const filter = document.getElementById('customersFilter')?.value || 'all';

  let list = Array.isArray(items) ? items.slice() : [];

  if (filter === 'repeat') {
    list = list.filter((customer) => (customer.order_count || 0) > 1);
  } else if (filter === 'newest') {
    list.sort((a, b) => {
      const aDate = a.created_at ? new Date(a.created_at).getTime() : 0;
      const bDate = b.created_at ? new Date(b.created_at).getTime() : 0;
      return bDate - aDate;
    });
  }

  return list.filter((customer) => {
    if (!query) return true;
    return customer.name?.toLowerCase().includes(query) ||
      customer.phone?.toLowerCase().includes(query);
  });
}

function renderCustomers(list) {
  const container = document.getElementById('customersList');
  const filtered = Array.isArray(list) ? list : [];
  container.innerHTML = '';

  if (filtered.length === 0) {
    container.innerHTML = `
      <div class="empty-state">
        <i>🔍</i>
        <p>No matching customers found. Try a different search term or expand the filter.</p>
      </div>
    `;
    return;
  }

  for (const c of filtered) {
    const row = document.createElement('div');
    row.className = 'customer-row';
    row.style.cursor = 'pointer';
    row.innerHTML = `
      <div class="customer-avatar">${escapeHtml((c.name || '')[0] || '?')}</div>
      <div class="customer-info">
        <div class="ci-name">${escapeHtml(c.name)}</div>
        <div class="ci-phone">${escapeHtml(c.phone || '')}</div>
      </div>
      <div class="customer-stats">
        <div class="cs-spent">₹ ${parseFloat(c.total_spent || 0).toFixed(2)}</div>
        <div class="cs-orders">${c.order_count || 0} orders</div>
      </div>
    `;
    row.addEventListener('click', () => showCustomerProfile(c.id));
    container.appendChild(row);
  }
}

async function showCustomerProfile(customerId) {
  selectedCustomerId = customerId;
  const panel = document.getElementById('customerProfilePanel');
  if (!panel) return;

  try {
    const profile = await fetchCustomerProfile(customerId);
    panel.style.display = 'block';
    document.getElementById('profileName').textContent = profile.name || '';
    document.getElementById('profilePhone').textContent = profile.phone || '—';
    document.getElementById('profileEmail').textContent = profile.email || '—';
    document.getElementById('profileAddress').textContent = profile.address || '—';
    document.getElementById('profileSpent').textContent = `₹ ${parseFloat(profile.total_spent || 0).toFixed(2)}`;
    document.getElementById('profileOrders').textContent = `${profile.order_count || 0} orders`;

    document.getElementById('editCustomerId').value = profile.id;
    document.getElementById('editName').value = profile.name || '';
    document.getElementById('editPhone').value = profile.phone || '';
    document.getElementById('editEmail').value = profile.email || '';
    document.getElementById('editAddress').value = profile.address || '';

    const historyEl = document.getElementById('purchaseHistory');
    const orders = profile.orders || [];
    if (!orders.length) {
      historyEl.innerHTML = '<p class="panel-sub">No purchase history yet.</p>';
    } else {
      historyEl.innerHTML = orders.map((o) => `
        <div class="order-row" style="margin-bottom:8px">
          <div class="or-id">${escapeHtml(o.invoice_number)}</div>
          <div class="or-date">${escapeHtml(o.created_at || '')}</div>
          <div class="or-amount">₹ ${parseFloat(o.total || 0).toFixed(2)}</div>
          <div>${escapeHtml(o.status || '')}</div>
        </div>
      `).join('');
    }
  } catch (err) {
    console.error(err);
    toast(err.message || 'Failed to load customer profile', 'error', 6000);
  }
}

function hideCustomerProfile() {
  const panel = document.getElementById('customerProfilePanel');
  if (panel) panel.style.display = 'none';
  selectedCustomerId = null;
}

async function loadAndRender() {
  try {
    customersCache = await fetchCustomers();
    renderCustomers(filterCustomers(customersCache));
    if (selectedCustomerId) {
      await showCustomerProfile(selectedCustomerId);
    }
  } catch (err) {
    console.error(err);
    toast(err.message || 'Failed to load customers', 'error', 6000);
  }
}

window.addEventListener('DOMContentLoaded', async () => {
  await initNav();
  loadAndRender();
  registerDataRefreshHandler(() => loadAndRender(), 'customers');

  const searchInput = document.getElementById('customersSearch');
  const filterSelect = document.getElementById('customersFilter');

  searchInput?.addEventListener('input', () => renderCustomers(filterCustomers(customersCache)));
  filterSelect?.addEventListener('change', () => renderCustomers(filterCustomers(customersCache)));

  document.getElementById('closeProfileBtn')?.addEventListener('click', hideCustomerProfile);

  document.getElementById('customerForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const form = e.target;
    try {
      await createCustomer({
        name: form.name.value.trim(),
        phone: form.phone.value.trim(),
        email: form.email.value.trim(),
        address: form.address.value.trim(),
      });
      toast('Customer created', 'info', 3000);
      form.reset();
      broadcastDataChange('customers');
      loadAndRender();
    } catch (err) {
      console.error(err);
      toast(err.message || 'Failed to create customer', 'error', 6000);
    }
  });

  document.getElementById('editCustomerForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const customerId = document.getElementById('editCustomerId').value;
    if (!customerId) return;
    try {
      await updateCustomer(customerId, {
        name: document.getElementById('editName').value.trim(),
        phone: document.getElementById('editPhone').value.trim(),
        email: document.getElementById('editEmail').value.trim(),
        address: document.getElementById('editAddress').value.trim(),
      });
      toast('Customer updated', 'info', 3000);
      broadcastDataChange('customers');
      loadAndRender();
    } catch (err) {
      console.error(err);
      toast(err.message || 'Failed to update customer', 'error', 6000);
    }
  });

  document.getElementById('deleteCustomerBtn')?.addEventListener('click', async () => {
    const customerId = document.getElementById('editCustomerId').value;
    if (!customerId || !confirm('Delete this customer?')) return;
    try {
      await deleteCustomer(customerId);
      toast('Customer deleted', 'info', 3000);
      hideCustomerProfile();
      broadcastDataChange('customers');
      loadAndRender();
    } catch (err) {
      console.error(err);
      toast(err.message || 'Failed to delete customer', 'error', 6000);
    }
  });
});
