import { useEffect, useState } from 'react'
import api from './api/client'
import type { Post } from './types'
import './App.css'

function App() {
  const [posts, setPosts] = useState<Post[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Функция для загрузки постов из твоего эндпоинта /posts
    const fetchPosts = async () => {
      try {
        const response = await api.get('/posts')
        setPosts(response.data)
      } catch (error) {
        console.error('Ошибка при загрузке постов:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchPosts()
  }, [])

  return (
    <div className="app-container">
      <h1>Лента постов</h1>
      
      {loading ? (
        <p>Загрузка...</p>
      ) : (
        <div className="posts-grid">
          {posts.map((post) => (
            <div key={post.id} className="post-card">
              <h3>{post.title}</h3>
              <p>{post.body}</p>
              <small>{new Date(post.created_at).toLocaleDateString()}</small>
            </div>
          ))}
          {posts.length === 0 && <p>Постов пока нет</p>}
        </div>
      )}
    </div>
  )
}

export default App