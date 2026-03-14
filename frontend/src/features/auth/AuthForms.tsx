import React, { useState } from 'react';
import { authApi } from './api';

interface AuthProps {
    onSuccess: (token: string) => void;
}

export const AuthForms = ({ onSuccess }: AuthProps) => {
    const [isLogin, setIsLogin] = useState(true);
    const [form, setForm] = useState({ username: '', password: '' });

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            if (isLogin) {
                const data = await authApi.login(form.username, form.password);
                onSuccess(data.access_token);
            } else {
                await authApi.register(form);
                alert('Регистрация успешна! Теперь войдите.');
                setIsLogin(true);
            }
        } catch (err: any) {
            alert(err.response?.data?.detail || 'Ошибка доступа');
        }
    };

    return (
        <div className="auth-card">
            <h2>{isLogin ? 'Вход' : 'Регистрация'}</h2>
            <form onSubmit={handleSubmit}>
                <input
                    placeholder="Имя пользователя"
                    onChange={e => setForm({ ...form, username: e.target.value })}
                />
                <input
                    type="password"
                    placeholder="Пароль"
                    onChange={e => setForm({ ...form, password: e.target.value })}
                />
                <button type="submit">{isLogin ? 'Войти' : 'Создать'}</button>
            </form>
            <button onClick={() => setIsLogin(!isLogin)} className="toggle-btn">
                {isLogin ? 'Нет аккаунта?' : 'Уже есть аккаунт?'}
            </button>
        </div>
    );
};