let typingEl = null;
let chatSessionId = localStorage.getItem('bizflow_chat_session') || `session-${Date.now()}`;
localStorage.setItem('bizflow_chat_session', chatSessionId);

function nowTime() {
  return new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' });
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

function renderActionCards(actions) {
  return (actions || []).map((action) => {
    if (action.error) {
      return `<div class="action-card error"><div class="ac-title">${escapeHtml(action.type)} failed</div><div>${escapeHtml(action.error)}</div></div>`;
    }

    if (action.type === 'create_order' && action.invoice_number) {
      return `<div class="action-card"><div class="ac-title">Order ${escapeHtml(action.invoice_number)}</div><div>Total: ₹ ${parseFloat(action.total || 0).toFixed(2)}</div></div>`;
    }

    if ((action.type === 'add_product' || action.type === 'update_product' || action.type === 'set_stock' || action.type === 'update_stock') && action.name) {
      return `<div class="action-card"><div class="ac-title">Product: ${escapeHtml(action.name)}</div><div>Qty: ${escapeHtml(action.quantity)}</div></div>`;
    }

    if ((action.type === 'add_customer' || action.type === 'update_customer') && action.name) {
      return `<div class="action-card"><div class="ac-title">Customer: ${escapeHtml(action.name)}</div></div>`;
    }

    if (action.type === 'delete_product' && action.name) {
      return `<div class="action-card"><div class="ac-title">Deleted product ${escapeHtml(action.name)}</div></div>`;
    }

    if (action.type === 'update_order_status' && action.invoice_number) {
      return `<div class="action-card"><div class="ac-title">Order ${escapeHtml(action.invoice_number)} → ${escapeHtml(action.status)}</div></div>`;
    }

    return '';
  }).join('');
}

function appendAiMsg(reply, actions, validation) {
  const invalid = (validation || []).filter((item) => !item.valid);
  let validationHtml = '';
  if (invalid.length) {
    const lines = invalid.flatMap((item) => item.errors || []);
    if (lines.length) {
      validationHtml = `<div class="action-card error"><div class="ac-title">Validation</div><div>${lines.map(escapeHtml).join('<br>')}</div></div>`;
    }
  }

  const cards = renderActionCards(actions);
  appendMsg('ai', escapeHtml(reply).replace(/\n/g, '<br>') + cards + validationHtml);
}

async function loadChatHistory() {
  try {
    const res = await fetchWithAuth(`/api/chat/history?limit=30&session_id=${encodeURIComponent(chatSessionId)}`);
    if (!res.ok) return;
    const history = await res.json();
    const area = document.getElementById('chatArea');
    area.innerHTML = '';
    if (!history.length) {
      appendMsg('ai', 'Hello! I can help manage inventory, orders, and customers. Try a command or use the chips below.');
      return;
    }

    for (const item of history.slice().reverse()) {
      appendMsg('user', escapeHtml(item.user_prompt));
      appendAiMsg(item.ai_response, item.metadata?.actions || [], []);
    }
  } catch (err) {
    console.error(err);
  }
}

function escapeHtml(text) {
  if (text === null || text === undefined) return '';

  return text
    .toString()
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
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
    const res = await fetchWithAuth('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text, session_id: chatSessionId }),
    });
    const data = await res.json();
    hideTyping();

    if (!res.ok || data.error) {
      const errMsg = data.message || (typeof data.error === 'string' ? data.error : 'Request failed');
      appendMsg('error', escapeHtml(errMsg) + (data.details ? ': ' + escapeHtml(data.details) : ''));
      toast(errMsg || 'Chat failed', 'error', 6000);
    } else {
      appendAiMsg(data.reply || 'Done.', data.actions || [], data.validation || []);
      if (data.approval_required) {
        toast('Action queued for manager approval', 'info', 5000);
      }
      const modules = modulesFromActions(data.actions || []);
      if (modules.length) {
        broadcastDataChange(modules);
      }
    }
  } catch (err) {
    hideTyping();
    appendMsg('error', 'Network error. Please try again.');
    console.error(err);
  } finally {
    sendBtn.disabled = false;
    statusText.textContent = 'Ready';
    document.getElementById('chatArea').scrollTop = document.getElementById('chatArea').scrollHeight;
  }
}

function showTyping() {
  const area = document.getElementById('chatArea');
  typingEl = document.createElement('div');
  typingEl.className = 'typing-indicator';
  typingEl.innerHTML = '<span></span><span></span><span></span>';
  area.appendChild(typingEl);
  area.scrollTop = area.scrollHeight;
}

function hideTyping() {
  if (typingEl && typingEl.parentNode) {
    typingEl.parentNode.removeChild(typingEl);
  }
  typingEl = null;
}

function sendChip(text) {
  document.getElementById('chatInput').value = text;
  sendMessage();
}

window.addEventListener('DOMContentLoaded', async () => {
  await initNav();
  await loadChatHistory();

  const chatInput = document.getElementById('chatInput');
  chatInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });
});
