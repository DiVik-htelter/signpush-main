import React, { useContext } from 'react';
import Header from "../../components/header/header";
import Sidebar from "../../components/sidebar/sidebar";
import {Outlet} from "react-router-dom";
import { SidebarContext } from '../../context/SidebarContext';
import './layout.css';

function Layout() {
  const { isCollapsed } = useContext(SidebarContext);

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
    </div>
  );
}

export default Layout;
