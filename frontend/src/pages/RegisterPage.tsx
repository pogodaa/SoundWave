import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import api from '../api/client';
import { Music, Lock, User, Mail } from 'lucide-react';

// Схема валидации, строго соответствующая backend/app/schemas/user.py (UserCreate)
const registerSchema = z.object({
  username: z.string()
    .min(3, 'Никнейм должен содержать минимум 3 символа')
    .max(20, 'Никнейм не должен превышать 20 символов')
    .regex(/^[a-zA-Z0-9_-]+$/, 'Разрешены только латиница, цифры, "_" и "-"'),
  email: z.string().email('Введите корректный адрес электронной почты'),
  password: z.string()
    .min(8, 'Пароль должен содержать минимум 8 символов')
    .max(20, 'Пароль не должен превышать 20 символов'),
  password_confirm: z.string()
    .min(8, 'Пароль должен содержать минимум 8 символов')
    .max(20, 'Пароль не должен превышать 20 символов'),
}).refine((data) => data.password === data.password_confirm, {
  message: 'Пароли не совпадают',
  path: ['password_confirm'],
});

type RegisterForm = z.infer<typeof registerSchema>;

export default function RegisterPage() {
  const navigate = useNavigate();
  const [error, setError] = useState<string | null>(null);

  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<RegisterForm>({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      username: '',
      email: '',
      password: '',
      password_confirm: ''
    }
  });

  const onSubmit = async (data: RegisterForm) => {
    setError(null);
    try {
      await api.post('/auth/register', {
        username: data.username,
        email: data.email,
        password: data.password,
        password_confirm: data.password_confirm,
      });
      // При успешной регистрации перенаправляем на страницу входа
      navigate('/login');
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      if (typeof detail === 'string') {
        setError(detail);
      } else if (Array.isArray(detail)) {
        setError(detail.map((e: any) => e.msg || JSON.stringify(e)).join('; '));
      } else {
        setError('Ошибка при регистрации. Попробуйте позже.');
      }
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-900 px-4 py-12">
      <div className="w-full max-w-md space-y-8 bg-gray-800 p-8 rounded-2xl shadow-2xl border border-gray-700">
        {/* Заголовок и логотип */}
        <div className="text-center">
          <div className="mx-auto h-16 w-16 bg-blue-600 rounded-full flex items-center justify-center mb-4">
            <Music className="h-8 w-8 text-white" />
          </div>
          <h2 className="text-3xl font-bold text-white">Создать аккаунт</h2>
          <p className="mt-2 text-sm text-gray-400">Заполните данные для регистрации</p>
        </div>

        {/* Блок ошибки */}
        {error && (
          <div className="p-4 rounded-lg bg-red-500/10 border border-red-500/50 text-red-400 text-sm text-center">
            {error}
          </div>
        )}

        {/* Форма регистрации */}
        <form onSubmit={handleSubmit(onSubmit)} className="mt-8 space-y-5">
          <div className="space-y-4">
            {/* Поле: Никнейм */}
            <div>
              <label htmlFor="username" className="block text-sm font-medium text-gray-300">Никнейм</label>
              <div className="mt-1 relative rounded-md shadow-sm">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <User className="h-5 w-5 text-gray-500" />
                </div>
                <input
                  id="username"
                  {...register('username')}
                  type="text"
                  className="block w-full pl-10 pr-3 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors sm:text-sm"
                  placeholder="cool_gamer_99"
                />
              </div>
              {errors.username && <p className="mt-1 text-sm text-red-400">{errors.username.message}</p>}
            </div>

            {/* Поле: Email */}
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-300">Email</label>
              <div className="mt-1 relative rounded-md shadow-sm">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Mail className="h-5 w-5 text-gray-500" />
                </div>
                <input
                  id="email"
                  {...register('email')}
                  type="email"
                  className="block w-full pl-10 pr-3 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors sm:text-sm"
                  placeholder="user@example.com"
                />
              </div>
              {errors.email && <p className="mt-1 text-sm text-red-400">{errors.email.message}</p>}
            </div>

            {/* Поле: Пароль */}
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-300">Пароль</label>
              <div className="mt-1 relative rounded-md shadow-sm">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Lock className="h-5 w-5 text-gray-500" />
                </div>
                <input
                  id="password"
                  {...register('password')}
                  type="password"
                  className="block w-full pl-10 pr-3 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors sm:text-sm"
                  placeholder="••••••••"
                />
              </div>
              {errors.password && <p className="mt-1 text-sm text-red-400">{errors.password.message}</p>}
            </div>

            {/* Поле: Подтверждение пароля */}
            <div>
              <label htmlFor="password_confirm" className="block text-sm font-medium text-gray-300">Подтвердите пароль</label>
              <div className="mt-1 relative rounded-md shadow-sm">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Lock className="h-5 w-5 text-gray-500" />
                </div>
                <input
                  id="password_confirm"
                  {...register('password_confirm')}
                  type="password"
                  className="block w-full pl-10 pr-3 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors sm:text-sm"
                  placeholder="••••••••"
                />
              </div>
              {errors.password_confirm && <p className="mt-1 text-sm text-red-400">{errors.password_confirm.message}</p>}
            </div>
          </div>

          {/* Кнопка регистрации */}
          <div>
            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full flex justify-center py-3 px-4 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
            >
              {isSubmitting ? (
                <span className="flex items-center">
                  <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Регистрация...
                </span>
              ) : (
                'Зарегистрироваться'
              )}
            </button>
          </div>
        </form>

        {/* Ссылка на вход */}
        <div className="text-center mt-4">
          <p className="text-sm text-gray-400">
            Уже есть аккаунт?{' '}
            <button
              onClick={() => navigate('/login')}
              className="font-medium text-blue-500 hover:text-blue-400 transition-colors"
            >
              Войти
            </button>
          </p>
        </div>
      </div>
    </div>
  );
}