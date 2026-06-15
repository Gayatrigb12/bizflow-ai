function getApiBaseUrl() {
  const configured = (window.BIZFLOW_CONFIG && window.BIZFLOW_CONFIG.API_BASE_URL) || '';
  if (configured) {
    return configured.replace(/\/$/, '');
  }
  return window.location.origin;
}

function apiUrl(path) {
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  return `${getApiBaseUrl()}${normalizedPath}`;
}

async function parseApiError(res, fallback = 'Request failed') {
  try {
    const data = await res.json();
    if (typeof data === 'string') return data;
    if (data.message) return data.message;
    if (data.error && typeof data.error === 'string') return data.error;
    if (data.details) return data.details;
    return fallback;
  } catch (_err) {
    return fallback;
  }
}
