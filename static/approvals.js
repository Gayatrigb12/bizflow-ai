async function fetchPendingActions() {
  const res = await fetchWithAuth('/api/ai/pending-actions');
  if (!res.ok) {
    if (res.status === 403) {
      return [];
    }
    throw new Error('Failed to load pending approvals');
  }
  return res.json();
}

async function approvePendingAction(actionId, comment = '') {
  const res = await fetchWithAuth(`/api/ai/pending-actions/${actionId}/approve`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ reviewer: 'admin', comment }),
  });
  if (!res.ok) throw new Error('Failed to approve pending action');
  return res.json();
}

async function rejectPendingAction(actionId, comment = '') {
  const res = await fetchWithAuth(`/api/ai/pending-actions/${actionId}/reject`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ reviewer: 'admin', comment }),
  });
  if (!res.ok) throw new Error('Failed to reject pending action');
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

function formatDate(dateString) {
  if (!dateString) return 'Unknown';
  const date = new Date(dateString);
  return date.toLocaleString('en-IN', { dateStyle: 'medium', timeStyle: 'short' });
}

function renderEmptyState() {
  const list = document.getElementById('pendingActionsList');
  list.innerHTML = `
    <div class="empty-state">
      <i>✅</i>
      <p>No pending AI approvals at the moment. AI actions will appear here once they require review.</p>
    </div>
  `;
}

function renderPendingActions(items) {
  const list = document.getElementById('pendingActionsList');
  if (!Array.isArray(items) || items.length === 0) {
    renderEmptyState();
    return;
  }

  const searchText = document.getElementById('approvalsSearch').value.trim().toLowerCase();
  const filter = document.getElementById('approvalsFilter').value;

  const filtered = items.filter((item) => {
    const payload = item.payload || {};
    const reply = String(payload.reply || '').toLowerCase();
    const actionTypes = (payload.actions || []).map((a) => String(a.type || '')).join(' ').toLowerCase();
    const metadata = `${item.requested_by || ''} ${item.status || ''}`.toLowerCase();
    const matchesSearch = !searchText || reply.includes(searchText) || actionTypes.includes(searchText) || metadata.includes(searchText);
    const matchesFilter = filter === 'all' || item.action_type === filter;
    return matchesSearch && matchesFilter;
  });

  if (filtered.length === 0) {
    list.innerHTML = `
      <div class="empty-state">
        <i>🔎</i>
        <p>No approvals match your search or filter. Clear the search or try a broader filter.</p>
      </div>
    `;
    return;
  }

  list.innerHTML = '';
  for (const item of filtered) {
    const card = document.createElement('div');
    card.className = 'approval-card';
    const payload = item.payload || {};
    const reply = String(payload.reply || 'No summary available');
    const actions = Array.isArray(payload.actions) ? payload.actions : [];

    const actionDetails = actions.map((action) => {
      const detail = Object.entries(action)
        .filter(([key]) => key !== 'type')
        .map(([key, value]) => `${key}: ${JSON.stringify(value)}`)
        .join(', ');
      return `<div class="approval-item"><strong>${escapeHtml(action.type || 'Unknown')}</strong>${detail ? ` — ${escapeHtml(detail)}` : ''}</div>`;
    }).join('');

    card.innerHTML = `
      <div class="approval-header">
        <div>
          <span class="approval-label">Request #${item.id}</span>
          <span class="approval-meta">Requested by ${escapeHtml(item.requested_by || 'AI')}</span>
        </div>
        <span class="status-badge pending">${escapeHtml(item.status || 'pending')}</span>
      </div>
      <div class="approval-info">
        <div>Created at: ${escapeHtml(formatDate(item.created_at))}</div>
      </div>
      <div class="approval-section">
        <div class="section-title">AI Summary</div>
        <div class="approval-text">${escapeHtml(reply)}</div>
      </div>
      <div class="approval-section">
        <div class="section-title">Actions</div>
        <div class="approval-actions-list">${actionDetails}</div>
      </div>
      <div class="approval-actions-row">
        <textarea class="approval-comment" placeholder="Optional review note"></textarea>
        <button class="send-btn approve-btn" data-action-id="${item.id}">Approve</button>
        <button class="send-btn reject-btn" data-action-id="${item.id}">Reject</button>
      </div>
    `;

    card.querySelector('.approve-btn').addEventListener('click', async () => {
      const comment = card.querySelector('.approval-comment').value.trim();
      try {
        await approvePendingAction(item.id, comment);
        toast(`Approved request #${item.id}`, 'info', 4000);
        loadAndRender();
      } catch (err) {
        console.error(err);
        toast('Unable to approve request', 'error', 6000);
      }
    });

    card.querySelector('.reject-btn').addEventListener('click', async () => {
      const comment = card.querySelector('.approval-comment').value.trim();
      if (!confirm(`Reject request #${item.id}?`)) return;
      try {
        await rejectPendingAction(item.id, comment);
        toast(`Rejected request #${item.id}`, 'info', 4000);
        loadAndRender();
      } catch (err) {
        console.error(err);
        toast('Unable to reject request', 'error', 6000);
      }
    });

    list.appendChild(card);
  }
}

async function loadAndRender() {
  try {
    const items = await fetchPendingActions();
    renderPendingActions(items);
  } catch (err) {
    console.error(err);
    toast('Failed to load approvals', 'error', 6000);
    renderEmptyState();
  }
}

function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

window.addEventListener('DOMContentLoaded', async () => {
  await initNav();
  loadAndRender();

  const searchInput = document.getElementById('approvalsSearch');
  const filterSelect = document.getElementById('approvalsFilter');
  const refreshBtn = document.getElementById('refreshBtn');

  searchInput?.addEventListener('input', () => {
    loadAndRender();
  });

  filterSelect?.addEventListener('change', () => {
    loadAndRender();
  });

  refreshBtn?.addEventListener('click', () => {
    loadAndRender();
  });
});
