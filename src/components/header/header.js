import { Link, useLocation } from "react-router-dom";
import { useContext } from "react";
import { SidebarContext } from "../../context/SidebarContext";
import './header.css';

function Header() {
    const { isCollapsed } = useContext(SidebarContext);
    const location = useLocation();
    
    // Не показываем sidebar margin на страницах логина/регистрации
    const isAuthPage = location.pathname === '/login' || location.pathname === '/registration';

    return (
        <header className={`header ${isCollapsed && !isAuthPage ? 'sidebar-collapsed' : ''}`}>
            <Link to="/" className="header-logo">
                <img alt="logo" src="logo.png" className="logo"></img>
            </Link>
        </header>
    );
}

export default Header;