import 'bootstrap/dist/css/bootstrap.min.css';
//import './site.css';
import './main.css';
import { useContext, useRef, useState, useEffect } from "react";
import {useLocation, useNavigate} from "react-router-dom";
import AuthContext from "../../context/AuthProvider";
import { useCookies} from 'react-cookie'
import Cookies from 'js-cookie';
import axios from '../../api/axios';
import detectOS from '../../components/detect-os/detect-os';

function Login() {
    const {setAuth} = useContext(AuthContext)
    const userRef = useRef();
    const passwordRef = useRef();
    const [user, setUser] = useState('');
    const [password, setPassword] = useState('');
    const [errMsg, setErrorMessage] = useState('');
    const [cookies, setCookie] = useCookies(['user']); 
    const [isLoginActive, setDisabled] = useState(false);

    const navigate = useNavigate();
    const location = useLocation()
    const from = location.state?.from?.pathname || '/';
    const LOGIN_URL = 'auth/'; // адрес, куда пойдет запрос на проверку

    useEffect(() => {
        if (window.YaAuthSuggest) {
            window.YaAuthSuggest.init(
                {
                    client_id: 'd0dd0f1b515f48bc8983269013ae760d', // Замените на ваш реальный client_id от Яндекса
                    response_type: 'token',
                    redirect_uri: 'https://sign-push.ru' + '/yandex-auth.html'
                },
                window.location.origin,
                {
                    view: "button",
                    parentId: "yandex-button-container",
                    buttonSize: 'm',
                    buttonView: 'main',
                    buttonTheme: 'light',
                    buttonBorderRadius: "0",
                    buttonIcon: 'ya',
                }
            )
            .then(({handler}) => handler())
            .then(data => {
                console.log('Сообщение с токеном', data);
                // Отправляем токен на наш бэкенд
                handleYandexAuth(data.access_token);
            })
            .catch(error => console.log('Обработка ошибки Яндекса', error));
        } else {
            console.log("YaAuthSuggest is not defined");
        }
    }, []);

    const handleYandexAuth = async (token) => {
        setDisabled(true);
        try {
            const response = await axios.post(
                'auth/yandex',
                JSON.stringify({ token: token })
            );

            if (response?.data?.status === 0) { 
                let expires = new Date();
                expires.setTime(expires.getTime() + 1000000);

                const yandexUserMail = response?.data?.email;
                setCookie('user', yandexUserMail, { path: '/',  expires}); 
                setCookie('token', response?.data?.token, { path: '/',  expires});

                setAuth({ user: yandexUserMail }); 
                setDisabled(false);
                navigate(from, { replace: true });
            } else {
                setErrorMessage(response?.data?.message || 'Не удалось авторизоваться через Яндекс.');
                setDisabled(false);
            }
        } catch (err) {
            console.log(err);
            setErrorMessage('Ошибка связи с сервером при Яндекс авторизации!');
            setDisabled(false);
        }
    };

    const handleSubmit = async (e) => {
        let response;

        const os = detectOS();

        e.preventDefault();

        try {
            setDisabled(true);
            response = await axios.post(
                LOGIN_URL,
                JSON.stringify({
                    'mail':user,
                    'password':password
                })
            );

        } catch (err) {
            console.log(err);
            setErrorMessage('Что-то пошло не так!');
            setDisabled(false);
            return;
        }

        if (response?.data?.status == 0) { 
            let expires = new Date()
            expires.setTime(expires.getTime() + 1000000);

            setCookie('user', user, { path: '/',  expires}); 
            setCookie('token', response?.data?.token || '213', { path: '/',  expires});

            setUser(''); 
            setPassword('');
            setAuth({user}); 

            setDisabled(false);
            navigate(from, { replace: true });

        } else {
            if (response?.data?.status === 2) {
                setErrorMessage('Не верный логин или пароль');
            } else {
                setErrorMessage(response?.data?.message || 'Неверный пароль или почта.');
            }

            setDisabled(false);
        }

    };

    return (
        <div className="">
            <header>
                <script src="https://smartcaptcha.cloud.yandex.ru/captcha.js" defer></script>
                <a href="/">
                    <img id="header_logo" src="logo_white.png" alt="SignPush"></img>
                </a>
            </header>

            <div className="site-login">
                <div className="row jumbotron">
                    <div className="col-lg-12">
                        <h3 className="h3 mb-3 font-weight-normal" id="pass-label">Вход по
                            паролю</h3>
                        <form id="sign-form" method="post" onSubmit={handleSubmit}>
                            <input required type="email" placeholder="example@example.ru" name="email" id="email"
                                   ref={userRef}
                                   value={user}
                                   onChange={(e) => setUser(e.target.value)}
                                   className="modal-login_input"/>
                            <input id="password" name="password" placeholder="Пароль" type="password"
                                   ref={passwordRef}
                                   value={password}
                                   onChange={(e) => setPassword(e.target.value)}
                                   required
                                   className="modal-login_input"/>

                            <div className="row" align="center">
                                <p className="error-message text-danger" align="center">{errMsg}</p>
                            </div>

                            <div
                                id="captcha-container"
                                class="smart-captcha"
                                data-sitekey="<ключ_клиента>"
                            ></div>
                            <button disabled={isLoginActive} className="btn btn-primary modal-login-submit" id="sign-in">
                                Продолжить
                            </button>
                            <div id="yandex-button-container" style={{marginTop: '15px'}} align="center"></div>
                        </form>

                        <div className="login-signup-link-container">
                            <p className="login-signup-text">
                                Нет аккаунта?{' '}
                                <a href="/registration" className="login-signup-link">Зарегистрируйтесь</a>
                            </p>
                        </div>
                    </div>
                </div>
            </div>

            <div id="message-modal" className="modal-login">
                <div className="modal-login-dialog">
                    <div className="modal-login-content">
                        <div className="modal-login-header">
                            <a href="#close" title="Close" className="close">×</a>
                        </div>
                        <div className="modal-login_body">
                            <p className="modal-login_body__text message" align="center"></p>
                        </div>
                    </div>
                </div>
            </div>

            <div id="verifyEmailModal" className="modal-login">
                <div className="modal-login-dialog">
                    <div className="modal-login-content">
                        <div className="modal-login-header">
                            <a href="#close" title="Close" className="close">×</a>
                        </div>
                        <div className="modal-login_body">
                            <div className="text-modal-wait">
                                <p className="modal-login_body__text" align="center">Пожалуйста активируйте аккаунт:</p>
                                <p className="modal-login_body__text" align="center"><a
                                    href="/resend-verification-email">Активировать</a></p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default Login;