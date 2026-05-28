// frontend/src/api/client.ts
import axios from 'axios';

// Создаем экземпляр axios с относительным baseURL
// Благодаря прокси в vite.config.ts запросы к /api/v1/* будут перенаправлены на localhost:8000
const api = axios.create({
  baseURL: '/api/v1',  // ← Относительный путь! Vite прокси перехватит
  headers: {
    'Content-Type': 'application/json',
  },
});

// Интерцептор запросов: добавляем токен, если он есть
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Интерцептор ответов: обрабатываем ошибки (например, истек токен)
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      const requestUrl = error.config?.url || '';
      const isAuthEndpoint =
        requestUrl.includes('/auth/login') ||
        requestUrl.includes('/auth/register') ||
        requestUrl.includes('/auth/refresh');
      
      if (!isAuthEndpoint) {
        console.warn('Сессия истекла, перенаправление на вход...');
        localStorage.removeItem('access_token');
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export default api;