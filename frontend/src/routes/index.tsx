import { createBrowserRouter, Navigate } from 'react-router-dom';
import { AuthForms, useAuth } from '../features/auth';
import { PostModule } from '../features/posts';

export const useRouter = () => {
    const { isAuthenticated, saveToken } = useAuth();

    return createBrowserRouter([
        {
            path: "/",
            element: isAuthenticated ? <Navigate to="/posts" /> : <AuthForms onSuccess={saveToken} />,
        },
        {
            path: "/posts",
            element: isAuthenticated ? <PostModule /> : <Navigate to="/" />,
        },
    ]);
};