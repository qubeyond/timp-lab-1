import React, { useEffect, useState } from 'react';
import { postsApi } from './api';
import type { PostResponse } from './types';

export const PostModule = () => {
    const [posts, setPosts] = useState<PostResponse[]>([]);
    const [newPost, setNewPost] = useState({ title: '', body: '' });

    const loadPosts = async () => {
        try {
            const data = await postsApi.getAll();
            setPosts(data);
        } catch (err) {
            console.error("Ошибка загрузки постов");
        }
    };

    useEffect(() => { loadPosts(); }, []);

    const handleCreate = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            await postsApi.create(newPost);
            setNewPost({ title: '', body: '' }); // Очистка формы
            loadPosts(); // Обновление списка
        } catch (err) {
            alert("Не удалось создать пост. Вы авторизованы?");
        }
    };

    return (
        <div className="posts-container">
            {/* Форма создания */}
            <form onSubmit={handleCreate} className="create-post-form">
                <h3>Создать пост</h3>
                <input
                    placeholder="Заголовок"
                    value={newPost.title}
                    onChange={e => setNewPost({ ...newPost, title: e.target.value })}
                />
                <textarea
                    placeholder="Текст поста..."
                    value={newPost.body}
                    onChange={e => setNewPost({ ...newPost, body: e.target.value })}
                />
                <button type="submit">Опубликовать</button>
            </form>

            <hr />

            {/* Лента */}
            <div className="posts-grid">
                {posts.map(post => (
                    <div key={post.id} className="post-card">
                        <h4>{post.title}</h4>
                        <p>{post.body}</p>
                        <small>{new Date(post.created_at).toLocaleString()}</small>
                    </div>
                ))}
            </div>
        </div>
    );
};