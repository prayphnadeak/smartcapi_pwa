const BASE_URL = `${import.meta.env.VITE_API_BASE_URL || '/api'}/v1`;

export async function login(username, password) {
  try {
    const resp = await fetch(`${BASE_URL}/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ username, password })
    });

    if (!resp.ok) {
      return { ok: false, error: 'Login gagal' };
    }

    const data = await resp.json();
    // data diharapkan berisi user dan token
    if (data.user) {
      localStorage.setItem('auth_user', JSON.stringify(data.user));
      if (data.token) localStorage.setItem('auth_token', data.token);
      return { ok: true, user: data.user };
    } else {
      return { ok: false, error: 'Response login tidak berisi user' };
    }
  } catch (e) {
    return { ok: false, error: e.message };
  }
}

export function logout() {
  localStorage.removeItem('auth_user');
  localStorage.removeItem('auth_token');
}