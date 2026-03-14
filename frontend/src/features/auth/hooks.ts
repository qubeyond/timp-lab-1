import { useState } from 'react';

export const useAuth = () => {
    const [token, setToken] = useState<string | null>(localStorage.getItem('token'));

    const saveToken = (accessToken: string) => {
        localStorage.setItem('token', accessToken);
        setToken(accessToken);
    };

    const logout = () => {
        localStorage.removeItem('token');
        setToken(null);
    };

    return {
        isAuthenticated: !!token,
        saveToken,
        logout
    };
};