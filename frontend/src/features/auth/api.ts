import { apiClient } from '../../api/client';
import type { UserResponse, UserCreate, Token } from './types';

export const authApi = {
    // Регистрация (JSON)
    register: async (data: UserCreate): Promise<UserResponse> => {
        const response = await apiClient.post('/register', data);
        return response.data;
    },

    // Логин (x-www-form-urlencoded)
    login: async (username: string, password: string): Promise<Token> => {
        // Используем URLSearchParams вместо FormData для x-www-form-urlencoded
        const params = new URLSearchParams();
        params.append('username', username);
        params.append('password', password);

        const response = await apiClient.post('/login', params, {
            // Явно перебиваем глобальный JSON заголовок для этого запроса
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
        });
        return response.data;
    },

    // Получение себя (Bearer Token прикрепит интерцептор)
    getMe: async (): Promise<UserResponse> => {
        const response = await apiClient.get('/users/me');
        return response.data;
    }
};