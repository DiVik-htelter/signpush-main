import 'bootstrap/dist/css/bootstrap.min.css';
//import './site.css';
import './main.css';
import { useContext, useRef, useState } from "react";
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
    const LOGIN_URL = 'http://127.0.0.1:8000/api/auth/'; // адрес, куда пойдет запрос на проверку

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

//// этот код нужен для работы фронтенда, даже если бекенд не запущен
//            let expires = new Date()
//            expires.setTime(expires.getTime() + 1000000);
//            setCookie('user', user, { path: '/',  expires});
//            setCookie('token', response?.data?.token || '213', { path: '/',  expires});

//            setUser('');
//            setPassword('');
//            setAuth({user});

//            setDisabled(false);
//            navigate(from, { replace: true });
////

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

                            <button disabled={isLoginActive} className="btn btn-primary modal-login-submit" id="sign-in">
                                Продолжить
                            </button>
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