const DATA_CHANGE_CHANNEL = 'bizflow-data-change';
const DATA_CHANGE_STORAGE_KEY = 'bizflow_data_change';

const INVENTORY_ACTIONS = new Set([
  'add_product',
  'update_product',
  'update_stock',
  'set_stock',
  'delete_product',
]);

const ORDER_ACTIONS = new Set(['create_order', 'update_order_status']);
const CUSTOMER_ACTIONS = new Set(['add_customer', 'update_customer']);

const refreshHandlers = new Map();

function normalizeModules(modules) {
  const list = Array.isArray(modules) ? modules : [modules];
  return [...new Set(list.filter(Boolean).map((item) => String(item)))];
}

function modulesFromActions(actions) {
  const modules = new Set();
  for (const action of actions || []) {
    const type = action && action.type;
    if (!type) continue;
    if (INVENTORY_ACTIONS.has(type)) modules.add('inventory');
    if (ORDER_ACTIONS.has(type)) {
      modules.add('orders');
      if (type === 'create_order') modules.add('inventory');
    }
    if (CUSTOMER_ACTIONS.has(type)) modules.add('customers');
  }
  return [...modules];
}

function dispatchRefresh(modules) {
  const normalized = normalizeModules(modules);
  if (!normalized.length) return;

  for (const moduleName of normalized) {
    const handlers = refreshHandlers.get(moduleName) || [];
    handlers.forEach((handler) => {
      try {
        handler();
      } catch (err) {
        console.error(`Data refresh handler failed for ${moduleName}`, err);
      }
    });
  }
}

function publishDataChange(modules) {
  const normalized = normalizeModules(modules);
  if (!normalized.length) return;

  const payload = { modules: normalized, ts: Date.now() };

  if (typeof BroadcastChannel !== 'undefined') {
    const channel = new BroadcastChannel(DATA_CHANGE_CHANNEL);
    channel.postMessage(payload);
    channel.close();
  }

  try {
    localStorage.setItem(DATA_CHANGE_STORAGE_KEY, JSON.stringify(payload));
  } catch (_err) {
    // Ignore storage failures in private mode.
  }

  dispatchRefresh(normalized);
}

function broadcastDataChange(modules) {
  publishDataChange(modules);
}

function registerDataRefreshHandler(handler, moduleName) {
  if (!moduleName || typeof handler !== 'function') return;
  const existing = refreshHandlers.get(moduleName) || [];
  existing.push(handler);
  refreshHandlers.set(moduleName, existing);
}

if (typeof BroadcastChannel !== 'undefined') {
  const channel = new BroadcastChannel(DATA_CHANGE_CHANNEL);
  channel.addEventListener('message', (event) => {
    const modules = event.data && event.data.modules;
    if (modules && modules.length) {
      dispatchRefresh(modules);
    }
  });
}

window.addEventListener('storage', (event) => {
  if (event.key !== DATA_CHANGE_STORAGE_KEY || !event.newValue) return;
  try {
    const payload = JSON.parse(event.newValue);
    if (payload.modules && payload.modules.length) {
      dispatchRefresh(payload.modules);
    }
  } catch (_err) {
    // Ignore malformed payloads.
  }
});
