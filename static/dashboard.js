async function fetchAnalytics() {
  const res = await fetchWithAuth('/api/analytics/summary');
  if (!res.ok) throw new Error('Failed to load analytics');
  return res.json();
}

async function fetchPendingApprovalCount() {
  const res = await fetchWithAuth('/api/ai/pending-actions');
  if (!res.ok) return 0;
  const data = await res.json();
  return Array.isArray(data) ? data.length : 0;
}

function buildLineChart(ctx, labels, data, label) {
  return new Chart(ctx, {
    type: 'line',
    data: {
      labels,
      datasets: [{
        label,
        data,
        fill: false,
        borderColor: 'rgba(75, 192, 192, 1)',
      }],
    },
    options: { responsive: true, maintainAspectRatio: false },
  });
}

function buildBarChart(ctx, labels, data, label, color = 'rgba(54,162,235,0.6)') {
  return new Chart(ctx, {
    type: 'bar',
    data: { labels, datasets: [{ label, data, backgroundColor: color }] },
    options: { responsive: true, maintainAspectRatio: false },
  });
}

function showLoading(show = true) {
  const el = document.getElementById('loadingOverlay');
  if (!el) return;
  el.style.display = show ? 'flex' : 'none';
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

async function loadDashboard() {
  showLoading(true);
  try {
    const analytics = await fetchAnalytics();

    const monthly = analytics.revenue.monthly || [];
    const monthTotal = monthly.length ? monthly[monthly.length - 1].total : 0;
    document.getElementById('statRevenue').textContent = monthTotal.toFixed(2);
    document.getElementById('statCustomers').textContent = (analytics.customers.top_customers || []).length;
    document.getElementById('statLowStock').textContent = (analytics.inventory.low_stock_count || 0).toString();

    if (hasMinRole('manager')) {
      const pendingCount = await fetchPendingApprovalCount();
      document.getElementById('statApprovals').textContent = pendingCount.toString();
      if (pendingCount > 0) {
        toast(`You have ${pendingCount} pending AI approval request(s)`, 'info', 7000);
      }
    }

    const revenueDaily = (analytics.revenue.daily || []).map((x) => x.total);
    const revenueLabels = (analytics.revenue.daily || []).map((x) => x.period);
    buildLineChart(
      document.getElementById('revenueChart').getContext('2d'),
      revenueLabels,
      revenueDaily,
      'Daily Revenue',
    );

    const productSales = analytics.products.best_sellers || [];
    buildBarChart(
      document.getElementById('ordersChart').getContext('2d'),
      productSales.map((p) => p.name),
      productSales.map((p) => p.quantity_sold),
      'Top Products',
    );

    const lowStock = analytics.inventory.low_stock_products || [];
    buildBarChart(
      document.getElementById('inventoryChart').getContext('2d'),
      lowStock.map((p) => p.name),
      lowStock.map((p) => p.quantity),
      'Low Stock Qty',
      'rgba(255, 159, 64, 0.7)',
    );

    const newCustomers = analytics.customers.new_customers || [];
    buildBarChart(
      document.getElementById('customerChart').getContext('2d'),
      newCustomers.map((c) => c.name),
      newCustomers.map(() => 1),
      'New Customers',
      'rgba(153, 102, 255, 0.6)',
    );

    if ((analytics.inventory.low_stock_count || 0) > 0) {
      toast(`Warning: ${analytics.inventory.low_stock_count} low-stock product(s) need restocking`, 'warning', 7000);
    }

    showLoading(false);
  } catch (err) {
    console.error(err);
    showLoading(false);
    toast('Failed to load dashboard', 'error', 6000);
  }
}

async function init() {
  await initNav();
  await loadDashboard();
}

window.addEventListener('DOMContentLoaded', async () => {
  registerDataRefreshHandler(() => loadDashboard(), 'inventory');
  registerDataRefreshHandler(() => loadDashboard(), 'orders');
  registerDataRefreshHandler(() => loadDashboard(), 'customers');
  await init();
});
