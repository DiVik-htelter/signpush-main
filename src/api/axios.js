import axios from "axios";
import Cookies from 'js-cookie';

const instance = axios.create({
    baseURL: 'http://127.0.0.1:80/api/'
    //baseURL: '/api/'
});

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
        
        // Добавляем email в заголовок, если существует
        if (Cookies.get('user')) {
            config.headers['email'] = Cookies.get('user');
        } else {
            config.headers['email'] = -1;
        }
        
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
        // Обработка ошибок сети или других ошибок
        if (error.response?.status === 401 || error.response?.status === 403) {
            // Если ошибка авторизации, удаляем токен
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