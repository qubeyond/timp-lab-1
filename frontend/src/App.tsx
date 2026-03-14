import { AuthForms, useAuth } from './features/auth';
import { PostModule } from './features/posts';
import './App.css';

function App() {
    const { isAuthenticated, saveToken, logout } = useAuth();

    return (
        <div className="app-container">
            <header className="app-header">
                <h1>My Social Lab</h1>
                {isAuthenticated && (
                    <button onClick={logout} className="logout-btn">Выйти</button>
                )}
            </header>

            <main>
                {!isAuthenticated ? (
                    <div className="welcome-screen">
                        <AuthForms onSuccess={saveToken} />
                    </div>
                ) : (
                    <PostModule />
                )}
            </main>
        </div>
    );
}

export default App;