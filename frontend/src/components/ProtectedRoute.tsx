import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from '../store/auth';

export const ProtectedRoute = () => {
  const { isAuthenticated } = useAuth();

  if (!isAuthenticated) {
    // Если не авторизован, кидаем на логин
    return <Navigate to="/login" replace />;
  }

  // Если авторизован, показываем дочерние страницы (Outlet)
  return <Outlet />;
};