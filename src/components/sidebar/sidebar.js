import React, { useState, useContext } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useCookies } from 'react-cookie';
import AuthContext from '../../context/AuthProvider';
import { SidebarContext } from '../../context/SidebarContext';
import './sidebar.css';

function Sidebar() {
    const [isOpen, setIsOpen] = useState(false);
    const { isCollapsed, setIsCollapsed } = useContext(SidebarContext);
    const { setAuth } = useContext(AuthContext);
    const [cookies, removeCookie] = useCookies(['user']);
    const navigate = useNavigate();

    const closeMenu = () => {
        setIsOpen(false);
    };

    const toggleMenu = () => {
        setIsOpen(!isOpen);
    };

    const toggleCollapse = () => {
        setIsCollapsed(!isCollapsed);
    };

    const handleLogout = (e) => {
        e.preventDefault();
        removeCookie('user');
        setAuth(null);
        closeMenu();
        navigate('/login', { replace: true });
    };

    return (
        <>
            {/* Кнопка для открытия меню (видна только на мобильных) */}
            <button className={`sidebar-toggle ${isOpen ? 'hidden' : ''}`} onClick={toggleMenu}>
                <i className="bi bi-list"></i>
            </button>

            {/* Оверлей для закрытия меню при клике вне его (только на мобильных) */}
            {isOpen && <div className="sidebar-overlay" onClick={closeMenu}></div>}

            {/* Боковая панель */}
            <aside className={`sidebar ${isOpen ? 'open' : ''} ${isCollapsed ? 'collapsed' : ''}`}>
                <div className="sidebar-header">
                    <div className="sidebar-header-top">
                        <button className="sidebar-close" onClick={closeMenu}>
                            <i className="bi bi-x"></i>
                        </button>
                        <button className="sidebar-collapse" onClick={toggleCollapse} title={isCollapsed ? 'Развернуть' : 'Свернуть'}>
                            <i className={`bi ${isCollapsed ? 'bi-chevron-right' : 'bi-chevron-left'}`}></i>
                        </button>
                    </div>
                    <div className="sidebar-user-info">
                        <span className="sidebar-user-email">{cookies?.user}</span>
                    </div>
                </div>

                <nav className="sidebar-nav">
                    <div className="sidebar-section">
                        <h5 className="section-title">Основное</h5>
                        <Link 
                            className="sidebar-item" 
                            to="/my-documents"
                            onClick={closeMenu}
                            title="Мои документы"
                        >
                            <i className="bi bi-file-earmark-pdf"></i>
                            <span>Мои документы</span>
                        </Link>

                        <Link 
                            className="sidebar-item" 
                            to="/upload"
                            onClick={closeMenu}
                            title="Загрузить документ"
                        >
                            <i className="bi bi-cloud-arrow-up"></i>
                            <span>Загрузить документ</span>
                        </Link>

                        <Link 
                            className="sidebar-item" 
                            to="/send-document"
                            onClick={closeMenu}
                            title="Отправить документ"
                        >
                            <i className="bi bi-send"></i>
                            <span>Отправить документ</span>
                        </Link>
                    </div>

                    <div className="sidebar-section">
                        <h5 className="section-title">Аккаунт</h5>
                        <Link 
                            className="sidebar-item" 
                            to="/profile"
                            onClick={closeMenu}
                            title="Профиль"
                        >
                            <i className="bi bi-person-circle"></i>
                            <span>Профиль</span>
                        </Link>

                        <Link 
                            className="sidebar-item" 
                            to="/settings"
                            onClick={closeMenu}
                            title="Настройки"
                        >
                            <i className="bi bi-gear"></i>
                            <span>Настройки</span>
                        </Link>
                    </div>
                </nav>

                <div className="sidebar-footer">
                    <button 
                        className="sidebar-item logout" 
                        onClick={handleLogout}
                        title="Выход"
                    >
                        <i className="bi bi-box-arrow-right"></i>
                        <span>Выход</span>
                    </button>
                </div>
            </aside>
        </>
    );
}

export default Sidebar;
