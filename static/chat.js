let typingEl = null;

function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

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

function appendAiMsg(reply, actions) {
  let extra = '';
  const orderAction = (actions || []).find((a) => a.type === 'create_order');
  const productAction = (actions || []).find((a) => a.type === 'add_product');

  if (orderAction && orderAction.invoice_number) {
    extra = `<div class="action-card"><div class="ac-title">Order ${escapeHtml(orderAction.invoice_number)}</div></div>`;
  } else if (productAction && productAction.name) {
    extra = `<div class="action-card"><div class="ac-title">Product: ${escapeHtml(productAction.name)}</div></div>`;
  }

  appendMsg('ai', escapeHtml(reply).replace(/\n/g, '<br>') + extra);
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

async function sendMessage() {
  const input = document.getElementById('chatInput');
  const text = input.value.trim();
  if (!text) return;

  const sendBtn = document.getElementById('sendBtn');
  const statusText = document.getElementById('statusText');
  const contextSelect = document.getElementById('chatContext');
  const context = contextSelect ? contextSelect.value : 'general';

  appendMsg('user', escapeHtml(text));
  input.value = '';
  sendBtn.disabled = true;
  statusText.textContent = 'Thinking...';
  showTyping();

  try {
    const res = await fetchWithAuth('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text, context }),
    });
    const data = await res.json();
    hideTyping();

    if (!res.ok || data.error) {
      appendMsg('error', escapeHtml(data.error || 'Request failed') + (data.details ? ': ' + escapeHtml(data.details) : ''));
      toast(data.error || 'Chat failed', 'error', 6000);
    } else {
      appendAiMsg(data.reply || 'Done.', data.actions || []);
      if (data.pending_approval) {
        toast('Action queued for manager approval', 'info', 5000);
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

function sendChip(text) {
  document.getElementById('chatInput').value = text;
  sendMessage();
}

async function loadChatHistory() {
  const contextSelect = document.getElementById('chatContext');
  const context = contextSelect ? contextSelect.value : 'general';
  const area = document.getElementById('chatArea');
  area.innerHTML = '';

  try {
    const res = await fetchWithAuth(`/api/chat/history?context=${encodeURIComponent(context)}`);
    if (!res.ok) throw new Error('Failed to load chat history');
    const history = await res.json();
    if (Array.isArray(history) && history.length > 0) {
      history.forEach((m) => {
        if (m.role === 'user') {
          appendMsg('user', escapeHtml(m.message));
        } else {
          appendAiMsg(m.message, m.actions || []);
        }
      });
    } else {
      appendMsg('ai', 'Hello! I can help manage inventory, orders, and customers. Try a command or use the chips below.');
    }
  } catch (err) {
    console.error(err);
    appendMsg('ai', 'Hello! I can help manage inventory, orders, and customers. Try a command or use the chips below.');
  }
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

  const contextSelect = document.getElementById('chatContext');
  if (contextSelect) {
    contextSelect.addEventListener('change', loadChatHistory);
  }
});
