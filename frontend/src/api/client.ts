import axios from 'axios';

export const apiClient = axios.create({
    // baseURL подхватит прокси из vite.config.ts (например, /api/v1)
    baseURL: '/api/v1',
    headers: {
        'Content-Type': 'application/json',
    },
});

// Добавляем токен в каждый запрос автоматически
apiClient.interceptors.request.use((config) => {
    const token = localStorage.getItem('token');
    if (token && config.headers) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});