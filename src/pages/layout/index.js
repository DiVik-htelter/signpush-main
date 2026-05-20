import React, { useContext } from 'react';
import Header from "../../components/header/header";
import Sidebar from "../../components/sidebar/sidebar";
import Footer from "../../components/footer/footer";
import {Outlet, useLocation} from "react-router-dom";
import { SidebarContext } from '../../context/SidebarContext';
import './layout.css';

function Layout() {
  const { isCollapsed } = useContext(SidebarContext);
  const location = useLocation();
  
  // Не показываем sidebar margin на страницах логина/регистрации
  const isAuthPage = location.pathname === '/login' || location.pathname === '/registration';

  return (
    <div className="layout">
      <Header />
      <div className="layout-container">
        <Sidebar />
        <main className={`layout-content ${isCollapsed ? 'sidebar-collapsed' : ''}`}>
          <div className="container">
            <Outlet />
          </div>
        </main>
      </div>
      {!isAuthPage && <Footer className={isCollapsed ? 'sidebar-collapsed' : ''} />}
    </div>
  );
}

export default Layout;
