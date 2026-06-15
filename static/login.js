window.addEventListener('DOMContentLoaded', () => {
  const existingToken = getAccessToken();
  if (existingToken) {
    window.location.href = '/dashboard';
    return;
  }

  const form = document.getElementById('loginForm');
  const statusEl = document.getElementById('loginStatus');

  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    statusEl.textContent = 'Signing in…';

    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value;

    try {
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      });

      const result = await response.json();
      if (!response.ok) {
        statusEl.textContent = result.error || 'Login failed';
        return;
      }

      setAccessToken(result.access_token);
      window.location.href = '/dashboard';
    } catch (error) {
      statusEl.textContent = 'Login failed. Please try again.';
      console.error(error);
    }
  });
});
