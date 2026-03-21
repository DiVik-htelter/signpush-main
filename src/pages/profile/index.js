import React, { useState, useEffect } from 'react';
import Form from 'react-bootstrap/Form';
import Button from 'react-bootstrap/Button';
import Alert from 'react-bootstrap/Alert';
import Card from 'react-bootstrap/Card';
import Row from 'react-bootstrap/Row';
import Col from 'react-bootstrap/Col';
import axios from '../../api/axios';
import Cookies from 'js-cookie';
import './profile.css';

function Profile() {
    const [userInfo, setUserInfo] = useState({
        email: Cookies.get('user'),
        firstName: '',
        lastName: '',
        createdAt: ''
    });

    const [editMode, setEditMode] = useState(false);
    const [formData, setFormData] = useState({
        firstName: '',
        lastName: '',
        currentPassword: '',
        newPassword: '',
        confirmPassword: ''
    });

    const [stats, setStats] = useState({
        documentsCount: 0,
        signaturesCount: 0,
        pendingSignatures: 0
    });

    const [alertMessage, setAlertMessage] = useState('');
    const [alertType, setAlertType] = useState('');
    const [isLoading, setIsLoading] = useState(false);

    useEffect(() => {
        loadUserInfo();
        loadStats();
    }, []);

    const loadUserInfo = async () => {
        try {
            // Здесь будет API запрос для получения информации о пользователе
            // const result = await axios.get('/api/user/info', {
            //     params: { email: Cookies.get('user') }
            // });
            // setUserInfo(result.data);

            // Временные данные для демонстрации
            setUserInfo({
                email: Cookies.get('user'),
                firstName: 'Иван',
                lastName: 'Петров',
                createdAt: new Date().toLocaleDateString('ru-RU')
            });

            setFormData({
                firstName: 'Иван',
                lastName: 'Петров',
                currentPassword: '',
                newPassword: '',
                confirmPassword: ''
            });
        } catch (err) {
            console.error('Ошибка при загрузке информации:', err);
        }
    };

    const loadStats = async () => {
        try {
            // Здесь будет API запрос для получения статистики
            // const result = await axios.get('/api/user/stats', {
            //     params: { email: Cookies.get('user') }
            // });
            // setStats(result.data);

            // Временные данные для демонстрации
            setStats({
                documentsCount: 12,
                signaturesCount: 8,
                pendingSignatures: 2
            });
        } catch (err) {
            console.error('Ошибка при загрузке статистики:', err);
        }
    };

    const handleInputChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: value
        }));
    };

    const validateForm = () => {
        if (!formData.firstName.trim()) {
            setAlertMessage('Пожалуйста, введите имя');
            setAlertType('warning');
            return false;
        }

        if (!formData.lastName.trim()) {
            setAlertMessage('Пожалуйста, введите фамилию');
            setAlertType('warning');
            return false;
        }

        if (formData.newPassword) {
            if (!formData.currentPassword) {
                setAlertMessage('Введите текущий пароль');
                setAlertType('warning');
                return false;
            }

            if (formData.newPassword.length < 6) {
                setAlertMessage('Новый пароль должен быть не менее 6 символов');
                setAlertType('warning');
                return false;
            }

            if (formData.newPassword !== formData.confirmPassword) {
                setAlertMessage('Пароли не совпадают');
                setAlertType('warning');
                return false;
            }
        }

        return true;
    };

    const handleSaveChanges = async (e) => {
        e.preventDefault();

        if (!validateForm()) {
            return;
        }

        setIsLoading(true);
        try {
            // Здесь будет API запрос для обновления информации
            // const result = await axios.post('/api/user/update', {
            //     email: Cookies.get('user'),
            //     firstName: formData.firstName,
            //     lastName: formData.lastName,
            //     currentPassword: formData.currentPassword,
            //     newPassword: formData.newPassword
            // });

            setUserInfo({
                ...userInfo,
                firstName: formData.firstName,
                lastName: formData.lastName
            });

            setAlertMessage('Информация успешно обновлена!');
            setAlertType('success');
            setEditMode(false);
            
            // Очистка полей пароля
            setFormData(prev => ({
                ...prev,
                currentPassword: '',
                newPassword: '',
                confirmPassword: ''
            }));
        } catch (err) {
            console.error('Ошибка при обновлении:', err);
            setAlertMessage('Ошибка при обновлении информации');
            setAlertType('danger');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="profile-container">
            <h1>Мой профиль</h1>

            {alertMessage && (
                <Alert variant={alertType} onClose={() => setAlertMessage('')} dismissible>
                    {alertMessage}
                </Alert>
            )}

            {/* Статистика */}
            <div className="stats-section">
                <h3>Статистика</h3>
                <Row className="stats-row">
                    <Col xs={12} sm={6} md={4} className="stat-col">
                        <Card className="stat-card">
                            <Card.Body>
                                <div className="stat-icon">
                                    <i className="bi bi-file-earmark-pdf"></i>
                                </div>
                                <div className="stat-content">
                                    <p className="stat-label">Документов загружено</p>
                                    <p className="stat-value">{stats.documentsCount}</p>
                                </div>
                            </Card.Body>
                        </Card>
                    </Col>

                    <Col xs={12} sm={6} md={4} className="stat-col">
                        <Card className="stat-card">
                            <Card.Body>
                                <div className="stat-icon">
                                    <i className="bi bi-pen"></i>
                                </div>
                                <div className="stat-content">
                                    <p className="stat-label">Подписано документов</p>
                                    <p className="stat-value">{stats.signaturesCount}</p>
                                </div>
                            </Card.Body>
                        </Card>
                    </Col>

                    <Col xs={12} sm={6} md={4} className="stat-col">
                        <Card className="stat-card">
                            <Card.Body>
                                <div className="stat-icon">
                                    <i className="bi bi-hourglass-split"></i>
                                </div>
                                <div className="stat-content">
                                    <p className="stat-label">Ожидают подписи</p>
                                    <p className="stat-value">{stats.pendingSignatures}</p>
                                </div>
                            </Card.Body>
                        </Card>
                    </Col>
                </Row>
            </div>

            {/* Информация о пользователе */}
            <div className="user-info-section">
                <h3>Информация об аккаунте</h3>

                {!editMode ? (
                    <Card className="info-card">
                        <Card.Body>
                            <Row className="info-row">
                                <Col xs={12} sm={6}>
                                    <div className="info-item">
                                        <label>Email</label>
                                        <p>{userInfo.email}</p>
                                    </div>
                                </Col>
                                <Col xs={12} sm={6}>
                                    <div className="info-item">
                                        <label>Дата регистрации</label>
                                        <p>{userInfo.createdAt}</p>
                                    </div>
                                </Col>
                                <Col xs={12} sm={6}>
                                    <div className="info-item">
                                        <label>Имя</label>
                                        <p>{userInfo.firstName}</p>
                                    </div>
                                </Col>
                                <Col xs={12} sm={6}>
                                    <div className="info-item">
                                        <label>Фамилия</label>
                                        <p>{userInfo.lastName}</p>
                                    </div>
                                </Col>
                            </Row>

                            <Button
                                variant="primary"
                                onClick={() => setEditMode(true)}
                                className="edit-btn"
                            >
                                <i className="bi bi-pencil"></i> Редактировать
                            </Button>
                        </Card.Body>
                    </Card>
                ) : (
                    <Card className="info-card edit-card">
                        <Card.Body>
                            <Form onSubmit={handleSaveChanges}>
                                <Form.Group className="form-group">
                                    <Form.Label>Имя</Form.Label>
                                    <Form.Control
                                        type="text"
                                        name="firstName"
                                        value={formData.firstName}
                                        onChange={handleInputChange}
                                        disabled={isLoading}
                                    />
                                </Form.Group>

                                <Form.Group className="form-group">
                                    <Form.Label>Фамилия</Form.Label>
                                    <Form.Control
                                        type="text"
                                        name="lastName"
                                        value={formData.lastName}
                                        onChange={handleInputChange}
                                        disabled={isLoading}
                                    />
                                </Form.Group>

                                <hr />

                                <h5>Изменение пароля (опционально)</h5>

                                <Form.Group className="form-group">
                                    <Form.Label>Текущий пароль</Form.Label>
                                    <Form.Control
                                        type="password"
                                        name="currentPassword"
                                        value={formData.currentPassword}
                                        onChange={handleInputChange}
                                        placeholder="Введите для смены пароля"
                                        disabled={isLoading}
                                    />
                                </Form.Group>

                                <Form.Group className="form-group">
                                    <Form.Label>Новый пароль</Form.Label>
                                    <Form.Control
                                        type="password"
                                        name="newPassword"
                                        value={formData.newPassword}
                                        onChange={handleInputChange}
                                        disabled={isLoading}
                                    />
                                </Form.Group>

                                <Form.Group className="form-group">
                                    <Form.Label>Подтвердить новый пароль</Form.Label>
                                    <Form.Control
                                        type="password"
                                        name="confirmPassword"
                                        value={formData.confirmPassword}
                                        onChange={handleInputChange}
                                        disabled={isLoading}
                                    />
                                </Form.Group>

                                <div className="button-group">
                                    <Button
                                        variant="success"
                                        type="submit"
                                        disabled={isLoading}
                                    >
                                        {isLoading ? 'Сохранение...' : 'Сохранить изменения'}
                                    </Button>
                                    <Button
                                        variant="secondary"
                                        onClick={() => {
                                            setEditMode(false);
                                            setFormData({
                                                firstName: userInfo.firstName,
                                                lastName: userInfo.lastName,
                                                currentPassword: '',
                                                newPassword: '',
                                                confirmPassword: ''
                                            });
                                        }}
                                        disabled={isLoading}
                                    >
                                        Отмена
                                    </Button>
                                </div>
                            </Form>
                        </Card.Body>
                    </Card>
                )}
            </div>
        </div>
    );
}

export default Profile;
