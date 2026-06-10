const state = {
  inventory: [],
  orders: [],
  customers: [],
  activity: []
};

let typingEl = null;

function formatINR(amount) {
  return '₹' + Number(amount).toLocaleString('en-IN', { maximumFractionDigits: 2 });
}

function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

function getInitials(name) {
  const parts = (name || '').trim().split(/\s+/);
  if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase();
  return (name || '??').slice(0, 2).toUpperCase();
}

function nowTime() {
  return new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' });
}

async function init() {
  try {
    const res = await fetch('/api/state');
    const data = await res.json();
    executeState(data);
    showPanel('dashboard');
  } catch (e) {
    console.error('Failed to load state', e);
    document.getElementById('statusText').textContent = 'Error loading';
  }

  const chatInput = document.getElementById('chatInput');
  chatInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });
}

function showPanel(name) {
  document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));

  const panel = document.getElementById('panel-' + name);
  const nav = document.querySelector(`.nav-item[data-panel="${name}"]`);
  if (panel) panel.classList.add('active');
  if (nav) nav.classList.add('active');

  if (name === 'inventory') renderInventory();
  else if (name === 'orders') renderOrders();
  else if (name === 'customers') renderCustomers();
  else if (name === 'dashboard') updateDashboard();
}

function executeState(newState) {
  if (!newState) return;
  state.inventory = newState.inventory || [];
  state.orders = newState.orders || [];
  state.customers = newState.customers || [];
  state.activity = newState.activity || [];
  updateAllBadges();
  updateDashboard();
  if (document.getElementById('panel-inventory').classList.contains('active')) renderInventory();
  if (document.getElementById('panel-orders').classList.contains('active')) renderOrders();
  if (document.getElementById('panel-customers').classList.contains('active')) renderCustomers();
}

function updateAllBadges() {
  document.getElementById('badge-inventory').textContent = state.inventory.length;
  document.getElementById('badge-orders').textContent = state.orders.length;
  document.getElementById('badge-customers').textContent = state.customers.length;
}

function updateDashboard() {
  document.getElementById('dash-orders').textContent = state.orders.length;
  document.getElementById('dash-products').textContent = state.inventory.length;
  document.getElementById('dash-customers').textContent = state.customers.length;

  const revenue = state.orders
    .filter(o => o.status === 'paid')
    .reduce((sum, o) => sum + (o.total || 0), 0);
  document.getElementById('dash-revenue').textContent = formatINR(revenue);

  const container = document.getElementById('recent-activity');
  const items = (state.activity || []).slice(0, 8);
  if (!items.length) {
    container.innerHTML = '<div class="empty-state"><i class="ti ti-activity"></i><p>No activity yet. Use AI Chat to get started.</p></div>';
    return;
  }
  container.innerHTML = items.map(a => `
    <div class="activity-item">
      <span class="act-text">${escapeHtml(a.text || '')}</span>
      <span class="act-meta">
        ${a.value ? `<span class="act-value">${escapeHtml(a.value)}</span>` : ''}
        <span class="act-time">${escapeHtml(a.time || '')}</span>
      </span>
    </div>
  `).join('');
}

function appendMsg(role, html) {
  const area = document.getElementById('chatArea');
  const msg = document.createElement('div');
  msg.className = `msg ${role}`;
  msg.innerHTML = `
    <div class="msg-bubble">${html}</div>
    <div class="msg-meta">${nowTime()}</div>
  `;
  area.appendChild(msg);
  area.scrollTop = area.scrollHeight;
  return msg;
}

function appendAiMsg(reply, actions) {
  let extra = '';
  const orderAction = (actions || []).find(a => a.type === 'create_order');
  const productAction = (actions || []).find(a => a.type === 'add_product');

  if (orderAction) {
    const order = state.orders[0];
    if (order) {
      const lines = (order.items || []).map(i =>
        `<div class="ac-line"><span>${escapeHtml(i.name)} × ${i.qty}</span><span>${formatINR(i.subtotal)}</span></div>`
      ).join('');
      extra = `
        <div class="action-card">
          <div class="ac-title">${escapeHtml(order.id)} — ${escapeHtml(order.customer)}</div>
          ${lines}
          <div class="ac-total"><span>Total</span><span>${formatINR(order.total)}</span></div>
        </div>
      `;
    }
  } else if (productAction) {
    const name = productAction.name || '';
    const p = state.inventory.find(x => x.name.toLowerCase() === name.toLowerCase());
    if (p) {
      extra = `
        <div class="action-card">
          <div class="ac-title">Inventory updated</div>
          <div class="ac-line"><span>${escapeHtml(p.name)}</span><span>${p.qty} ${escapeHtml(p.unit)}</span></div>
          <div class="ac-line"><span>Price</span><span>${formatINR(p.price)}</span></div>
        </div>
      `;
    }
  }

  appendMsg('ai', escapeHtml(reply) + extra);
}

function showTyping() {
  const area = document.getElementById('chatArea');
  typingEl = document.createElement('div');
  typingEl.className = 'typing-indicator';
  typingEl.innerHTML = '<span></span><span></span><span></span>';
  area.appendChild(typingEl);
  area.scrollTop = area.scrollHeight;
  return typingEl;
}

function hideTyping() {
  if (typingEl && typingEl.parentNode) {
    typingEl.parentNode.removeChild(typingEl);
  }
  typingEl = null;
}

async function sendMessage() {
  const input = document.getElementById('chatInput');
  const text = input.value.trim();
  if (!text) return;

  const sendBtn = document.getElementById('sendBtn');
  const statusText = document.getElementById('statusText');

  appendMsg('user', escapeHtml(text));
  input.value = '';
  sendBtn.disabled = true;
  statusText.textContent = 'Thinking...';
  showTyping();

  try {
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text })
    });
    const data = await res.json();
    hideTyping();

    if (data.error) {
      const errMsg = document.createElement('div');
      errMsg.className = 'msg error';
      errMsg.innerHTML = `
        <div class="msg-bubble">${escapeHtml(data.error)}${data.details ? ': ' + escapeHtml(data.details) : ''}</div>
        <div class="msg-meta">${nowTime()}</div>
      `;
      document.getElementById('chatArea').appendChild(errMsg);
    } else {
      if (data.state) executeState(data.state);
      appendAiMsg(data.reply || 'Done.', data.actions || []);
    }
  } catch (e) {
    hideTyping();
    appendMsg('error', 'Network error. Is the server running?');
  } finally {
    sendBtn.disabled = false;
    statusText.textContent = 'Ready';
    document.getElementById('chatArea').scrollTop = document.getElementById('chatArea').scrollHeight;
  }
}

function sendChip(text) {
  document.getElementById('chatInput').value = text;
  showPanel('chat');
  sendMessage();
}

function renderInventory() {
  const grid = document.getElementById('inventoryGrid');
  if (!state.inventory.length) {
    grid.innerHTML = '<div class="empty-state"><i class="ti ti-package-off"></i><p>No products yet. Ask AI: "Add product Rice ₹60 qty 100 kg"</p></div>';
    return;
  }
  grid.innerHTML = state.inventory.map(p => {
    const low = p.qty <= (p.low_stock_threshold ?? 10);
    return `
      <div class="product-card ${low ? 'low-stock' : ''}">
        <div class="pc-name">${escapeHtml(p.name)}</div>
        <div class="pc-sku">${escapeHtml(p.sku || '')}</div>
        <div class="pc-qty">${p.qty}</div>
        <div class="pc-unit">${escapeHtml(p.unit || 'pcs')}</div>
        <div class="pc-price">${formatINR(p.price)} / ${escapeHtml(p.unit || 'pcs')}</div>
      </div>
    `;
  }).join('');
}

function renderOrders() {
  const list = document.getElementById('ordersList');
  if (!state.orders.length) {
    list.innerHTML = '<div class="empty-state"><i class="ti ti-receipt-off"></i><p>No orders yet. Create an invoice via AI Chat.</p></div>';
    return;
  }
  list.innerHTML = state.orders.map(o => {
    const status = (o.status || 'pending').toLowerCase();
    return `
      <div class="order-row">
        <span class="or-id">${escapeHtml(o.id)}</span>
        <span class="or-customer">${escapeHtml(o.customer)}</span>
        <span class="or-date">${escapeHtml(o.date || '')}</span>
        <span class="status-badge ${status}">${escapeHtml(o.status || 'pending')}</span>
        <span class="or-amount">${formatINR(o.total)}</span>
      </div>
    `;
  }).join('');
}

function renderCustomers() {
  const list = document.getElementById('customersList');
  if (!state.customers.length) {
    list.innerHTML = '<div class="empty-state"><i class="ti ti-users-off"></i><p>No customers yet. Add via AI Chat or create an invoice.</p></div>';
    return;
  }
  list.innerHTML = state.customers.map(c => `
    <div class="customer-row">
      <div class="customer-avatar">${escapeHtml(getInitials(c.name))}</div>
      <div class="customer-info">
        <div class="ci-name">${escapeHtml(c.name)}</div>
        <div class="ci-phone">${escapeHtml(c.phone || '—')}</div>
      </div>
      <div class="customer-stats">
        <div class="cs-spent">${formatINR(c.total_spent || 0)}</div>
        <div class="cs-orders">${c.orders || 0} orders</div>
      </div>
    </div>
  `).join('');
}

document.addEventListener('DOMContentLoaded', init);
