import { apiClient } from '../../api/client';
import type { PostResponse, PostCreate } from './types';

export const postsApi = {
    // Получить все посты
    getAll: async (): Promise<PostResponse[]> => {
        const response = await apiClient.get('/posts');
        return response.data;
    },

    // Создать новый пост (токен прикрепится автоматически через interceptor)
    create: async (data: PostCreate): Promise<PostResponse> => {
        const response = await apiClient.post('/posts', data);
        return response.data;
    },

    // Удалить пост
    delete: async (id: string): Promise<void> => {
        await apiClient.delete(`/posts/${id}`);
    }
};