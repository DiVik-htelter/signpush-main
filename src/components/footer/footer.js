import React from 'react';
import './footer.css';

function Footer({ className = '' }) {
    return (
        <footer className={`footer ${className}`}>
            <div className="footer-content">
                <div className="footer-section">
                    <h5 className="footer-title">SignPush</h5>
                    <p className="footer-description">
                        Защищённая платформа для электронной подписи документов
                    </p>
                </div>

                <div className="footer-section">
                    <h5 className="footer-title">Контакты</h5>
                    <ul className="footer-links">
                        <li>
                            <i className="bi bi-envelope"></i>
                            <a href="mailto:fergysina1@gmail.com">fergysina1@gmail.com</a>
                        </li>
                        <li>
                            <i className="bi bi-telephone"></i>
                            <a href="tel:+7-933-992-17-22">+7 (933) 992-17-22</a>
                        </li>
                        <li>
                            <i className="bi bi-geo-alt"></i>
                            <span>Россия, г. Омск</span>
                        </li>
                    </ul>
                </div>

                <div className="footer-section">
                    <h5 className="footer-title">Ссылки</h5>
                    <ul className="footer-links">
                        <li><a href="/my-documents">Мои документы</a></li>
                        <li><a href="/profile">Профиль</a></li>
                        <li><a href="/settings">Настройки</a></li>
                    </ul>
                </div>

                <div className="footer-section">
                    <h5 className="footer-title">Информация</h5>
                    <ul className="footer-links">
                        <li><a href="/">О сервисе</a></li>
                        <li><a href="/">Условия использования</a></li>
                        <li><a href="/">Политика конфиденциальности</a></li>
                    </ul>
                </div>
            </div>

            <div className="footer-divider"></div>

            <div className="footer-bottom">
                <p className="footer-copyright">
                    &copy; 2026 Sign-Push. Все права защищены.
                </p>
                <p className="footer-version">
                    v1.1.0
                </p>
            </div>
        </footer>
    );
}

export default Footer;
