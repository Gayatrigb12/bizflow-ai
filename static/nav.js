const ROLE_LEVEL = { staff: 1, manager: 2, admin: 3 };

window.currentUserRole = 'staff';

async function loadCurrentUser() {
  const token = typeof getAccessToken === 'function' ? getAccessToken() : null;
  if (!token) {
    window.location.href = '/login';
    return null;
  }
  try {
    const res = await fetchWithAuth('/api/auth/status');
    if (!res.ok) throw new Error('status failed');
    const data = await res.json();
    window.currentUserRole = (data.user && data.user.role) || 'staff';
    return data.user;
  } catch {
    return null;
  }
}

function hasMinRole(minRole) {
  const current = ROLE_LEVEL[window.currentUserRole] || 1;
  const required = ROLE_LEVEL[minRole] || 1;
  return current >= required;
}

function applyRoleBasedNav() {
  document.querySelectorAll('[data-min-role]').forEach((el) => {
    const minRole = el.getAttribute('data-min-role');
    if (!hasMinRole(minRole)) {
      el.style.display = 'none';
    }
  });
}

async function downloadExport(url, filename) {
  try {
    const res = await fetchWithAuth(url);
    if (!res.ok) throw new Error('Export failed');
    const blob = await res.blob();
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = filename || 'export.csv';
    link.click();
    URL.revokeObjectURL(link.href);
  } catch (err) {
    console.error(err);
    if (typeof toast === 'function') {
      toast('Export failed', 'error', 6000);
    }
  }
}

async function downloadInvoice(invoice) {
  await downloadExport(`/api/export/invoice/${invoice}`, `invoice-${invoice}.pdf`);
}

async function initNav() {
  await loadCurrentUser();
  applyRoleBasedNav();
}
