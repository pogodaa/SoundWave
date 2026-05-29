import { create } from 'zustand'
import api from '../api/client'

interface User {
  id: number
  username: string
  email: string
  role: string
  avatar_url: string
}

interface AuthState {
  token: string | null
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null
  login: (username: string, password: string) => Promise<boolean>
  logout: () => void
  checkAuth: () => Promise<void>
  updateAvatar: (avatarUrl: string) => void
}

export const useAuth = create<AuthState>((set, get) => ({
  token: localStorage.getItem('access_token'),
  user: null,
  isAuthenticated: !!localStorage.getItem('access_token'),
  isLoading: false,
  error: null,

  login: async (username: string, password: string) => {
    set({ isLoading: true, error: null })
    try {
      console.log('Login attempt:', { username }) // ← Отладка
      const response = await api.post('/auth/login', {
        username,
        password,
      })
      console.log('Login success:', response.data) // ← Отладка
      const { access_token } = response.data
      localStorage.setItem('access_token', access_token)
      set({
        token: access_token,
        isAuthenticated: true,
        isLoading: false
      })
      await get().checkAuth()
      return true
    } catch (error: any) {
      console.error('Login error:', error) // ← Отладка
      
      // Безопасное извлечение ошибки
      let errorMessage = 'Ошибка авторизации'
      try {
        const detail = error?.response?.data?.detail
        if (typeof detail === 'string') {
          errorMessage = detail
        } else if (Array.isArray(detail)) {
          errorMessage = detail
            .map((err: any) => err?.msg || JSON.stringify(err))
            .join('; ')
        } else if (detail && typeof detail === 'object') {
          errorMessage = detail?.msg || JSON.stringify(detail)
        }
      } catch (e) {
        console.error('Error parsing detail:', e)
        errorMessage = 'Ошибка сети или сервера'
      }
      
      set({
        error: errorMessage,
        isLoading: false
      })
      return false
    }
  },

  logout: () => {
    localStorage.removeItem('access_token')
    set({ 
      token: null, 
      user: null, 
      isAuthenticated: false,
      error: null 
    })
    window.location.href = '/login'
  },

  checkAuth: async () => {
    const token = localStorage.getItem('access_token')
    if (!token) {
      set({ isAuthenticated: false, user: null })
      return
    }
    
    try {
      const response = await api.get('/users/me')
      set({ 
        user: response.data, 
        isAuthenticated: true,
        error: null 
      })
    } catch (error) {
      console.error('Auth check failed:', error)
      localStorage.removeItem('access_token')
      set({ 
        token: null, 
        user: null, 
        isAuthenticated: false,
        error: null 
      })
    }
  },

  updateAvatar: (avatarUrl: string) => {
    set((state) => ({
      user: state.user ? { ...state.user, avatar_url: avatarUrl } : null,
    }))
  },
}))
