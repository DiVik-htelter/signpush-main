import axios from "axios";
import Cookies from 'js-cookie';

const instance = axios.create({
    // По умолчанию используем относительный /api/ (через proxy) для корректной работы httpOnly cookies
    baseURL: process.env.REACT_APP_API_BASE_URL || '/api/'
});

// Отправлять cookies (httpOnly refresh-token) по умолчанию
instance.defaults.withCredentials = true;

let navigateFunction = null;
let currentPath = '/';

// Функция для установки функции навигации
export const setNavigate = (navigate) => {
    navigateFunction = navigate;
};

// Функция для установки текущего пути
export const setCurrentPath = (path) => {
    currentPath = path;
};

// Интерцептор для добавления token и email в заголовки всех запросов
instance.interceptors.request.use(
    (config) => {
        // Добавляем token в заголовок, если существует
        if (Cookies.get('token')) {
            config.headers['token'] = Cookies.get('token');
        } else {
            config.headers['token'] = -1;
        }
        
        // Ранее в заголовок добавляли email пользователя — больше не требуется
        
        // Устанавливаем Content-Type по умолчанию
        if (!config.headers['Content-Type']) {
            config.headers['Content-Type'] = 'application/json';
        }
        
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

// Интерцептор для проверки статуса во всех ответах
instance.interceptors.response.use(
    (response) => {
        // Проверяем наличие status в ответе
        if (response.data && response.data.status !== undefined) {
            if (response.data.status !== 0) {
                // Если status не равен 0, удаляем токен и перенаправляем на авторизацию
                Cookies.remove('token');
                Cookies.remove('user');
                
                // Перенаправляем на страницу логина, если навигация доступна и мы не на странице логина/регионистрации
                if (navigateFunction && currentPath !== '/login' && currentPath !== '/registration') {
                    navigateFunction('/login', { replace: true });
                }
            }
        }
        return response;
    },
    (error) => {
        // Автоматически пробуем обновить access token при 401
        const originalRequest = error.config;
        const isRefreshRequest = originalRequest?.url?.includes('auth/refresh');
        if (error.response?.status === 401 && !originalRequest._retry && !isRefreshRequest) {
            originalRequest._retry = true;
            // Попытка обновить токен через refresh endpoint
            return instance.post('auth/refresh')
                .then(res => {
                    if (res.data && res.data.token) {
                        // Сохраняем новый access token и повторяем запрос
                        Cookies.set('token', res.data.token);
                        originalRequest.headers['token'] = res.data.token;
                        return instance(originalRequest);
                    }
                    // иначе редирект на логин
                    Cookies.remove('token');
                    Cookies.remove('user');
                    if (navigateFunction && currentPath !== '/login' && currentPath !== '/registration') {
                        navigateFunction('/login', { replace: true });
                    }
                    return Promise.reject(error);
                })
                .catch(err => {
                    Cookies.remove('token');
                    Cookies.remove('user');
                    if (navigateFunction && currentPath !== '/login' && currentPath !== '/registration') {
                        navigateFunction('/login', { replace: true });
                    }
                    return Promise.reject(err);
                });
        }
        // Для прочих случаев
        if (error.response?.status === 401 || error.response?.status === 403) {
            Cookies.remove('token');
            Cookies.remove('user');
            if (navigateFunction && currentPath !== '/login' && currentPath !== '/registration') {
                navigateFunction('/login', { replace: true });
            }
        }
        return Promise.reject(error);
    }
);

export default instance;