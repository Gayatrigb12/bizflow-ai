function getAccessToken() {
  return localStorage.getItem('access_token') || null;
}

function setAccessToken(token) {
  localStorage.setItem('access_token', token);
  document.cookie = `access_token=${token}; path=/`;
}

function clearAuthTokens() {
  localStorage.removeItem('access_token');
  document.cookie = 'access_token=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/';
}

function logout() {
  clearAuthTokens();
  window.location.href = '/login';
}

async function fetchWithAuth(url, options = {}) {
  const headers = {
    ...(options.headers || {}),
    ...(getAccessToken() ? { Authorization: `Bearer ${getAccessToken()}` } : {}),
  };

  const response = await fetch(url, { ...options, headers });
  if (response.status === 401) {
    logout();
    throw new Error('Unauthorized');
  }
  return response;
}
