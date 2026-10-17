const API_URL =
  import.meta.env.VITE_API_URL ??
  "http://127.0.0.1:8000";

export async function apiRequest(
  path: string,
  options: RequestInit = {},
) {
  const token = localStorage.getItem("access_token");

  const headers = new Headers(options.headers);

  headers.set("Content-Type", "application/json");

  if (token) {
    headers.set(
      "Authorization",
      `Bearer ${token}`,
    );
  }

  const response = await fetch(
    `${API_URL}${path}`,
    {
      ...options,
      headers,
    },
  );

  if (!response.ok) {
    const data = await response
      .json()
      .catch(() => null);

    throw new Error(
      data?.detail ?? "Ошибка запроса",
    );
  }

  return response.json();
}