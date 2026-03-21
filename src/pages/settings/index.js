import React from 'react';
import Card from 'react-bootstrap/Card';
import './settings.css';

function Settings() {
    return (
        <div className="settings-container">
            <h1>Настройки</h1>

            <Card className="settings-card">
                <Card.Body className="empty-state">
                    <div className="empty-icon">
                        <i className="bi bi-gear"></i>
                    </div>
                    <h2>Скоро появятся новые настройки</h2>
                    <p>Здесь вы сможете настроить параметры приложения</p>
                </Card.Body>
            </Card>
        </div>
    );
}

export default Settings;
