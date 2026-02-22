import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import './styles/mobile.css'; // Мобильные адаптивные стили
import App from './App';
import {AuthProvider} from './context/AuthProvider';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <>
    <AuthProvider>
      <App />
    </AuthProvider>
  </>
);
