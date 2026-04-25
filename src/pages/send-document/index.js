import React, { useState, useEffect } from 'react';
import Table from 'react-bootstrap/Table';
import Button from 'react-bootstrap/Button';
import Form from 'react-bootstrap/Form';
import InputGroup from 'react-bootstrap/InputGroup';
import Alert from 'react-bootstrap/Alert';
import Modal from 'react-bootstrap/Modal';
import axios from '../../api/axios';
import Cookies from 'js-cookie';
import './send-document.css';

function SendDocument() {
    const [fileList, setFileList] = useState([]);
    const [searchQuery, setSearchQuery] = useState('');
    const [selectedRecipient, setSelectedRecipient] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [alertMessage, setAlertMessage] = useState('');
    const [alertType, setAlertType] = useState('');
    const [showModal, setShowModal] = useState(false);
    const [selectedDocument, setSelectedDocument] = useState(null);

    const DOCUMENTS_URL = 'docs';

    // Загрузка документов пользователя при монтировании компонента

    useEffect(() => {
        loadDocuments();
    }, []);

    const loadDocuments = async () => {
        try {
            const result = await axios.get(
                DOCUMENTS_URL
            );

            if (result.data?.papers) {
                setFileList(result.data.papers);
            }
        } catch (err) {
            console.error('Ошибка при загрузке документов:', err);
            setAlertMessage('Не удалось загрузить документы');
            setAlertType('danger');
        }
    };

    const handleSearch = async (e) => {
        e.preventDefault();
        
        if (!searchQuery.trim()) {
            setAlertMessage('Пожалуйста, введите email пользователя');
            setAlertType('warning');
            return;
        }

        setIsLoading(true);
        try {
            // Здесь можно добавить API запрос для поиска пользователя
            // На данный момент просто устанавливаем выбранного пользователя
            setSelectedRecipient(searchQuery);
            setAlertMessage(`Пользователь ${searchQuery} выбран`);
            setAlertType('success');
        } catch (err) {
            console.error('Ошибка при поиске:', err);
            setAlertMessage('Пользователь не найден');
            setAlertType('danger');
        } finally {
            setIsLoading(false);
        }
    };

    const handleSendDocument = async (document) => {
        if (!selectedRecipient) {
            setAlertMessage('Пожалуйста, сначала выберите пользователя');
            setAlertType('warning');
            return;
        }

        if (selectedRecipient === Cookies.get('user')) {
            setAlertMessage('Вы не можете отправить документ самому себе');
            setAlertType('warning');
            return;
        }

        setIsLoading(true);
        try {
            // Здесь будет API запрос для отправки документа
             const result = await axios.post('/document/send', {
                 document_id: document.id,
                 email_to_send: selectedRecipient
             });

            setAlertMessage(`Документ "${document.title}" отправлен пользователю ${selectedRecipient}`);
            setAlertType('success');
            setShowModal(false);
            setSelectedDocument(null);
        } catch (err) {
            console.error('Ошибка при отправке документа:', err);
            setAlertMessage('Ошибка при отправке документа ' + err.response.data.message);
            setAlertType('danger');
        } finally {
            setIsLoading(false);
        }
    };

    const openSendModal = (document) => {
        setSelectedDocument(document);
        setShowModal(true);
    };

    return (
        <div className="send-document-container">
            <h1>Отправить документ</h1>

            {alertMessage && (
                <Alert variant={alertType} onClose={() => setAlertMessage('')} dismissible>
                    {alertMessage}
                </Alert>
            )}

            {/* Поиск пользователя */}
            <div className="search-section">
                <h3>Выберите получателя</h3>
                <Form onSubmit={handleSearch}>
                    <InputGroup className="search-group">
                        <Form.Control
                            placeholder="Введите email получателя"
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            disabled={isLoading}
                        />
                        <Button
                            variant="primary"
                            onClick={handleSearch}
                            disabled={isLoading || !searchQuery}
                        >
                            {isLoading ? 'Поиск...' : 'Поиск'}
                        </Button>
                    </InputGroup>
                </Form>

                {selectedRecipient && (
                    <div className="recipient-info">
                        <span className="recipient-label">Получатель:</span>
                        <span className="recipient-email">{selectedRecipient}</span>
                        <Button
                            variant="link"
                            onClick={() => {
                                setSelectedRecipient('');
                                setSearchQuery('');
                            }}
                            className="change-recipient"
                        >
                            Изменить
                        </Button>
                    </div>
                )}
            </div>

            {/* Таблица документов */}
            <div className="documents-section">
                <h3>Ваши документы</h3>
                {fileList.length > 0 ? (
                    <Table striped bordered hover responsive>
                        <thead>
                            <tr>
                                <th>Название</th>
                                <th>Дата создания</th>
                                <th className="actions-column">Действия</th>
                            </tr>
                        </thead>
                        <tbody>
                            {fileList.map((file, idx) => (
                                <tr key={idx}>
                                    <td>{file.title}</td>
                                    <td>{new Date(file.created_at * 1000).toLocaleDateString('ru-RU')}</td>
                                    <td className="actions-column">
                                        <Button
                                            variant="primary"
                                            size="sm"
                                            onClick={() => openSendModal(file)}
                                            disabled={!selectedRecipient}
                                        >
                                            <i className="bi bi-send"></i> Отправить
                                        </Button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </Table>
                ) : (
                    <Alert variant="info">
                        У вас нет документов для отправки
                    </Alert>
                )}
            </div>

            {/* Модальное окно подтверждения */}
            <Modal show={showModal} onHide={() => setShowModal(false)}>
                <Modal.Header closeButton>
                    <Modal.Title>Подтверждение отправки</Modal.Title>
                </Modal.Header>
                <Modal.Body>
                    {selectedDocument && (
                        <div>
                            <p>
                                <strong>Документ:</strong> {selectedDocument.title}
                            </p>
                            <p>
                                <strong>Получатель:</strong> {selectedRecipient}
                            </p>
                            <p>Вы уверены, что хотите отправить этот документ?</p>
                        </div>
                    )}
                </Modal.Body>
                <Modal.Footer>
                    <Button variant="secondary" onClick={() => setShowModal(false)}>
                        Отмена
                    </Button>
                    <Button
                        variant="primary"
                        onClick={() => handleSendDocument(selectedDocument)}
                        disabled={isLoading}
                    >
                        {isLoading ? 'Отправка...' : 'Отправить'}
                    </Button>
                </Modal.Footer>
            </Modal>
        </div>
    );
}

export default SendDocument;
