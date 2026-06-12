async function fetchAnalyticsSummary() {
  const res = await fetchWithAuth('/api/analytics/summary');
  if (!res.ok) throw new Error('Failed to load analytics summary');
  return res.json();
}

async function fetchReportSummary() {
  const res = await fetchWithAuth('/api/reports/summary');
  if (!res.ok) throw new Error('Failed to load report summary');
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

function renderStatCards(state) {
  const stats = [
    { label: 'Products', value: state.inventory.length },
    { label: 'Orders', value: state.orders.length },
    { label: 'Customers', value: state.customers.length },
    { label: 'Low stock', value: state.low_stock_count },
    { label: 'Total revenue', value: state.revenue.toFixed ? state.revenue.toFixed(2) : state.revenue },
  ];

  const container = document.getElementById('reportStats');
  container.innerHTML = '';
  for (const stat of stats) {
    const card = document.createElement('div');
    card.className = 'stat-card';
    card.innerHTML = `
      <div class="stat-label">${stat.label}</div>
      <div class="stat-value">${stat.value}</div>
    `;
    container.appendChild(card);
  }
}

function renderBestSellers(products) {
  const grid = document.getElementById('bestSellers');
  grid.innerHTML = '';
  products.slice(0, 6).forEach(product => {
    const card = document.createElement('div');
    card.className = 'product-card';
    card.innerHTML = `
      <div class="pc-name">${product.name}</div>
      <div class="pc-sku">${product.sku || ''}</div>
      <div class="pc-price">Revenue: ₹ ${parseFloat(product.revenue || 0).toFixed(2)}</div>
      <div class="pc-unit">Qty sold: ${product.quantity_sold || 0}</div>
    `;
    grid.appendChild(card);
  });
}

function renderTopCustomers(customers) {
  const list = document.getElementById('topCustomers');
  list.innerHTML = '';
  customers.slice(0, 6).forEach(customer => {
    const row = document.createElement('div');
    row.className = 'customer-row';
    row.innerHTML = `
      <div class="customer-avatar">${(customer.name || '?')[0] || '?'}</div>
      <div class="customer-info">
        <div class="ci-name">${customer.name}</div>
        <div class="ci-phone">Orders: ${customer.order_count || 0}</div>
      </div>
      <div class="customer-stats">
        <div class="cs-spent">₹ ${parseFloat(customer.total_spent || 0).toFixed(2)}</div>
      </div>
    `;
    list.appendChild(row);
  });
}

window.addEventListener('DOMContentLoaded', async () => {
  await initNav();
  try {
    const [reportState, analytics] = await Promise.all([
      fetchReportSummary(),
      fetchAnalyticsSummary(),
    ]);

    renderStatCards(reportState);
    renderBestSellers(analytics.products.best_sellers || []);
    renderTopCustomers(analytics.customers.top_customers || []);
  } catch (err) {
    console.error(err);
    toast('Unable to load reporting summary', 'error', 6000);
  }
});
