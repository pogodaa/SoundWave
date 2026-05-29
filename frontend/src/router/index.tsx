// frontend/src/router/index.tsx — Конфигурация React Router v6: публичные/защищённые маршруты
import { createBrowserRouter, Navigate } from 'react-router-dom';
import { ProtectedRoute } from '../components/ProtectedRoute';
import Layout from '../components/Layout';
import LoginPage from '../pages/LoginPage';
import HomePage from '../pages/HomePage';
import RegisterPage from '../pages/RegisterPage';
import TracksPage from '../pages/TracksPage';
import PlaylistsPage from '../pages/PlaylistsPage';
import PlaylistDetailPage from '../pages/PlaylistDetailPage';
import LikedPage from '../pages/LikedPage';
import ProfilePage from '../pages/ProfilePage';
import RecommendationsPage from '../pages/RecommendationsPage';
// <-- Сюда потом импортируем PlaylistsPage, HistoryPage и др.

export const router = createBrowserRouter([
  // === ПУБЛИЧНЫЕ МАРШРУТЫ (без авторизации) ===
  {
    path: '/login',
    element: <LoginPage />,
  },
  {
    path: '/register',
    element: <RegisterPage />,
  },
  
  // === ЗАЩИЩЁННЫЕ МАРШРУТЫ (требуют авторизации) ===
  {
    element: <ProtectedRoute />, // Проверяет наличие access_token
    children: [
      {
        element: <Layout />, // Глобальный лейаут с хедером + плеером
        children: [
          { path: '/', element: <HomePage /> },
          { path: '/tracks', element: <TracksPage /> },
          { path: '/recommendations', element: <RecommendationsPage /> },
          { path: '/playlists', element: <PlaylistsPage /> },
          { path: '/playlists/:playlistId', element: <PlaylistDetailPage /> },
          { path: '/liked', element: <LikedPage /> },
          { path: '/profile', element: <ProfilePage /> },
          // { path: '/history', element: <HistoryPage /> },     // <-- раскомментировать, когда будет готов
        ],
      },
    ],
  },
  
  // === 404 ===
  {
    path: '*',
    element: <Navigate to="/" replace />,
  },
]);