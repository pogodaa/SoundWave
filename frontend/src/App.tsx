// frontend/src/App.tsx — Корневой компонент приложения: инициализация auth + роутинг
import { useEffect } from 'react'
import { RouterProvider } from 'react-router-dom'
import { router } from './router'
import { useAuth } from './store/auth'

function App() {
  const { checkAuth } = useAuth()

  useEffect(() => {
    // Проверяем авторизацию при загрузке приложения (только один раз)
    checkAuth()
  }, [checkAuth])

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <RouterProvider router={router} />
    </div>
  )
}

export default App