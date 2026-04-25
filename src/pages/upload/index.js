import React, { useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Button from 'react-bootstrap/Button';
import Alert from 'react-bootstrap/Alert';
import { DateTime } from 'luxon';
import jsSHA from 'jssha';
import axios from '../../api/axios';
import Cookies from 'js-cookie';
import './upload.css';

// Страница для загрузки документов пользователем
function Upload() {
    const [selectedFile, setSelectedFile] = useState(null);
    const [isLoading, setIsLoading] = useState(false);
    const [alertMessage, setAlertMessage] = useState('');
    const [alertType, setAlertType] = useState('');
    const fileInputRef = useRef(null);
    const navigate = useNavigate();
    const DOCUMENTS_URL = 'docs/download';

    const handleFileChange = async (event) => {
        const files = event.currentTarget.files;
        if (files && files.length) {
            const file = files[0];
            
            // Проверка типа файла
            if (file.type !== 'application/pdf') {
                setAlertMessage('Пожалуйста, выберите PDF файл');
                setAlertType('warning');
                return;
            }

            // Проверка размера файла (макс 50MB)
            if (file.size > 50 * 1024 * 1024) {
                setAlertMessage('Размер файла не должен превышать 50MB');
                setAlertType('warning');
                return;
            }

            setSelectedFile(file);
            setAlertMessage('');
        }
    };

    const getBase64 = (file) => {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = () => resolve(reader.result);
            reader.onerror = reject;
            reader.readAsDataURL(file);
        });
    };

    const handleUpload = async () => {
        if (!selectedFile) {
            setAlertMessage('Пожалуйста, выберите файл для загрузки');
            setAlertType('warning');
            return;
        }

        setIsLoading(true);
        try {
            const base64 = await getBase64(selectedFile);
            const base64String = base64
                .replace('data:', '')
                .replace(/^.+,/, '');

            const shaObj = new jsSHA('SHA-256', 'B64');
            shaObj.update(base64String);
            const hash = shaObj.getHash('B64');

            const result = await axios.post(
                DOCUMENTS_URL,
                JSON.stringify({
                    id: 1,
                    title: selectedFile.name,
                    hash: hash,
                    created_at: Math.floor(Date.now() / 1000),
                    email: Cookies.get('user'),
                    base64: base64,
                    deadline_at: -1
                })
            );

            if (result.data.success) {
                setAlertMessage('Документ успешно загружен!');
                setAlertType('success');
                setSelectedFile(null);
                
                setTimeout(() => {
                    navigate('/my-documents');
                }, 2000);
            } else {
                setAlertMessage('Ошибка при загрузке документа');
                setAlertType('danger');
            }
        } catch (err) {
            console.error('Ошибка:', err);
            setAlertMessage('Ошибка при загрузке документа: ' + (err.response?.data?.message || err.message));
            setAlertType('danger');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="upload-container">
            <h1>Загрузить документ</h1>
            
            {alertMessage && (
                <Alert variant={alertType} onClose={() => setAlertMessage('')} dismissible>
                    {alertMessage}
                </Alert>
            )}

            <div className="upload-box">
                <div className="upload-icon">
                    <i className="bi bi-cloud-arrow-up"></i>
                </div>
                
                <h2>Выберите PDF документ</h2>
                <p>для загрузки в систему</p>

                <input
                    type="file"
                    id="fileInput"
                    className="file-input"
                    accept="application/pdf"
                    onChange={handleFileChange}
                    disabled={isLoading}
                    ref={fileInputRef}
                />
                
                <div className="file-label">
                    <Button
                        variant="primary"
                        disabled={isLoading}
                        onClick={() => fileInputRef.current?.click()}
                    >
                        Выбрать файл
                    </Button>
                </div>

                {selectedFile && (
                    <div className="file-info">
                        <h4>Выбранный файл:</h4>
                        <p className="file-name">{selectedFile.name}</p>
                        <p className="file-size">
                            Размер: {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                        </p>
                    </div>
                )}
            </div>

            {selectedFile && (
                <div className="upload-actions">
                    <Button
                        variant="success"
                        onClick={handleUpload}
                        disabled={isLoading}
                        className="btn-upload"
                    >
                        {isLoading ? 'Загрузка...' : 'Загрузить документ'}
                    </Button>
                    <Button
                        variant="secondary"
                        onClick={() => {
                            setSelectedFile(null);
                            setAlertMessage('');
                        }}
                        disabled={isLoading}
                    >
                        Отмена
                    </Button>
                </div>
            )}
        </div>
    );
}

export default Upload;
