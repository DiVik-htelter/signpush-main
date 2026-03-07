import 'bootstrap/dist/css/bootstrap.min.css';
import './registration.css';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from '../../api/axios';

function Registration() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [errMsg, setErrorMessage] = useState('');
  const [successMsg, setSuccessMessage] = useState('');
  const [isRegistering, setIsRegistering] = useState(false);

  const navigate = useNavigate();
  const REGISTRATION_URL = 'http://127.0.0.1:8000/api/register/';

  const handleSubmit = async (e) => {
    let response;
    e.preventDefault();

    // Validation
    if (!email || !password || !confirmPassword || !firstName || !lastName) {
      setErrorMessage('Пожалуйста, заполните все поля');
      return;
    }

    if (password !== confirmPassword) {
      setErrorMessage('Пароли не совпадают');
      return;
    }

    if (password.length < 6) {
      setErrorMessage('Пароль должен содержать минимум 6 символов');
      return;
    }

    try {
      setIsRegistering(true);
      setErrorMessage('');
      response = await axios.post(
                  REGISTRATION_URL,
                  JSON.stringify({
                    'email': email,
                    'password': password,
                    'first_name': firstName,
                    'last_name': lastName
                  }),
                  {
                    headers: {
                      'Content-Type': 'application/json',
                      "Accept": "application/json"
                    },
                  }
                );
                
    } catch (err) {
        setErrorMessage('Извините, произошла непредвиденная ошибка');
        console.log(err);
    } finally{
      setIsRegistering(false)
    }

    
    if (response?.data?.status === 0 || response?.status === 201) {
      setSuccessMessage('Регистрация успешна! Перенаправляем на страницу входа...');
      setEmail('');
      setPassword('');
      setConfirmPassword('');
      setFirstName('');
      setLastName('');
      
    setTimeout(() => {
        navigate('/login');
      }, 2000);     
      
    } else {
        if(response?.data?.status === 2){
          setErrorMessage('Этот email уже зарегистрирован');
        } else{
          setErrorMessage(response?.data?.message || 'Ошибка при регистрации');
        }
      }
        
  };

  return (
    <div className="">
      <header>
        <a href="/">
          <img id="header_logo" src="logo_white.png" alt="SignPush"></img>
        </a>
      </header>

      <div className="site-registration">
        <div className="row jumbotron">
          <div className="col-lg-12">
            <h3 className="h3 mb-3 font-weight-normal" id="reg-title">
              Создание аккаунта
            </h3>
            
            {successMsg && (
              <div className="alert alert-success" role="alert">
                {successMsg}
              </div>
            )}

            {errMsg && (
              <div className="alert alert-danger" role="alert">
                {errMsg}
              </div>
            )}

            <form id="registration-form" method="post" onSubmit={handleSubmit}>
              <input
                required
                type="text"
                placeholder="Имя"
                name="firstName"
                id="firstName"
                value={firstName}
                onChange={(e) => setFirstName(e.target.value)}
                className="modal-reg_input"
              />
              
              <input
                required
                type="text"
                placeholder="Фамилия"
                name="lastName"
                id="lastName"
                value={lastName}
                onChange={(e) => setLastName(e.target.value)}
                className="modal-reg_input"
              />

              <input
                required
                type="email"
                placeholder="example@example.ru"
                name="email"
                id="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="modal-reg_input"
              />

              <input
                required
                type="password"
                placeholder="Пароль (мин. 6 символов)"
                name="password"
                id="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="modal-reg_input"
              />

              <input
                required
                type="password"
                placeholder="Подтвердите пароль"
                name="confirmPassword"
                id="confirmPassword"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className="modal-reg_input"
              />

              <div className="row" align="center">
                <p className="error-message text-danger" align="center"></p>
              </div>

              <button
                disabled={isRegistering}
                className="btn btn-primary modal-reg-submit"
                id="sign-up"
                type="submit"
              >
                {isRegistering ? 'Регистрация...' : 'Зарегистрироваться'}
              </button>
            </form>

            <div className="reg-login-link-container">
              <p className="reg-login-text">
                Уже есть аккаунт?{' '}
                <a href="/login" className="reg-login-link">Войти</a>
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Registration;