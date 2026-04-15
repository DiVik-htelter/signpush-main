import React, { useState, useRef, useEffect } from 'react';
import Button from 'react-bootstrap/Button';
import Alert from 'react-bootstrap/Alert';
import Form from 'react-bootstrap/Form';
import axios from '../../api/axios';
import './signature-verification.css';

function SignatureVerification() {
    const [pdfFile, setPdfFile] = useState(null);
    const [documents, setDocuments] = useState([]);
    const [selectedDocumentId, setSelectedDocumentId] = useState('');
    const [selectedDocumentTitle, setSelectedDocumentTitle] = useState('');
    const [selectedDocumentBase64, setSelectedDocumentBase64] = useState('');
    const [isDocumentsLoading, setIsDocumentsLoading] = useState(false);
    const [isDocumentDataLoading, setIsDocumentDataLoading] = useState(false);
    const [signatureFile, setSignatureFile] = useState(null);
    const [isChecking, setIsChecking] = useState(false);
    const [alertMessage, setAlertMessage] = useState('');
    const [alertType, setAlertType] = useState('');
    const [verificationResult, setVerificationResult] = useState(null);

    const pdfInputRef = useRef(null);
    const signatureInputRef = useRef(null);

    useEffect(() => {
        (async function loadDocuments() {
            try {
                setIsDocumentsLoading(true);
                const response = await axios.get('/docs');
                setDocuments(response.data?.papers || []);
            } catch (err) {
                console.error('Ошибка при загрузке списка документов:', err);
                setDocuments([]);
            } finally {
                setIsDocumentsLoading(false);
            }
        })();
    }, []);

    const convertFileToDataUrl = (file) => {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = () => resolve(reader.result);
            reader.onerror = reject;
            reader.readAsDataURL(file);
        });
    };

    const handlePdfChange = (event) => {
        const file = event.target.files?.[0];
        if (!file) {
            return;
        }

        if (file.type !== 'application/pdf') {
            setAlertMessage('Основной файл должен быть в формате PDF');
            setAlertType('warning');
            return;
        }

        setPdfFile(file);
        setSelectedDocumentId('');
        setSelectedDocumentTitle('');
        setSelectedDocumentBase64('');
        setVerificationResult(null);
    };

    const handleSelectDocument = async (event) => {
        const docId = event.target.value;
        setSelectedDocumentId(docId);
        setPdfFile(null);
        setVerificationResult(null);

        if (!docId) {
            setSelectedDocumentTitle('');
            setSelectedDocumentBase64('');
            return;
        }

        try {
            setIsDocumentDataLoading(true);
            const selectedDoc = documents.find((doc) => String(doc.id) === String(docId));
            const response = await axios.patch('/docs', null, {
                params: { doc_id: docId },
            });

            setSelectedDocumentTitle(selectedDoc?.title || `Документ #${docId}`);
            setSelectedDocumentBase64(response.data?.base64 || '');
        } catch (err) {
            console.error('Ошибка при загрузке выбранного документа:', err);
            setSelectedDocumentTitle('');
            setSelectedDocumentBase64('');
            setAlertMessage(err.response?.data?.message || 'Не удалось загрузить выбранный документ');
            setAlertType('danger');
        } finally {
            setIsDocumentDataLoading(false);
        }
    };

    const handleSignatureChange = (event) => {
        const file = event.target.files?.[0];
        if (!file) {
            return;
        }

        const allowedTypes = ['application/pkcs7-signature', 'application/octet-stream', ''];
        const isAllowedType = allowedTypes.includes(file.type) || file.name.toLowerCase().endsWith('.sig');
        if (!isAllowedType) {
            setAlertMessage('Файл подписи должен быть в формате .sig');
            setAlertType('warning');
            return;
        }

        setSignatureFile(file);
        setVerificationResult(null);
    };

    const handleVerification = async () => {
        if ((!pdfFile && !selectedDocumentBase64) || !signatureFile) {
            setAlertMessage('Загрузите PDF и файл подписи');
            setAlertType('warning');
            return;
        }

        setIsChecking(true);
        setAlertMessage('');

        try {
            const documentBase64 = selectedDocumentBase64 || await convertFileToDataUrl(pdfFile);
            const signatureBase64 = await convertFileToDataUrl(signatureFile);

            const response = await axios.post('/document/verify/unep/', {
                document_base64: documentBase64,
                signature_base64: signatureBase64,
            });

            setVerificationResult(response.data);

            if (response.data?.is_valid) {
                setAlertMessage('Подпись валидна');
                setAlertType('success');
            } else {
                setAlertMessage(response.data?.message || 'Подпись невалидна');
                setAlertType('danger');
            }
        } catch (err) {
            console.error('Ошибка при проверке подписи:', err);
            setVerificationResult(null);
            setAlertMessage(err.response?.data?.message || 'Ошибка при проверке подписи');
            setAlertType('danger');
        } finally {
            setIsChecking(false);
        }
    };

    const getSigningTimeLabel = (attrs) => {
        if (!Array.isArray(attrs)) {
            return null;
        }

        const signingTimeAttr = attrs.find((attr) => (
            attr?.name === 'signing_time' || attr?.oid === '1.2.840.113549.1.9.5'
        ));

        const signingTimeValue = signingTimeAttr?.values?.[0]?.value;
        if (!signingTimeValue) {
            return null;
        }

        const parsedDate = new Date(signingTimeValue);
        if (Number.isNaN(parsedDate.getTime())) {
            return String(signingTimeValue);
        }

        return parsedDate.toLocaleString('ru-RU');
    };

    const signingTimeLabel = getSigningTimeLabel(verificationResult?.attrs);

    return (
        <div className="signature-verification-container">
            <h1>Проверка подписи</h1>

            {alertMessage && (
                <Alert variant={alertType} onClose={() => setAlertMessage('')} dismissible>
                    {alertMessage}
                </Alert>
            )}

            <div className="signature-verification-box">
                <div className="upload-row">
                    <Form.Label>Выбрать PDF из загруженных документов</Form.Label>
                    <Form.Select
                        value={selectedDocumentId}
                        onChange={handleSelectDocument}
                        disabled={isChecking || isDocumentsLoading || isDocumentDataLoading}
                    >
                        <option value="">-- Выберите документ --</option>
                        {documents.map((doc) => (
                            <option key={doc.id} value={doc.id}>
                                {doc.title}
                            </option>
                        ))}
                    </Form.Select>
                    {selectedDocumentTitle && (
                        <div className="file-name">Выбран документ: {selectedDocumentTitle}</div>
                    )}
                    {isDocumentDataLoading && (
                        <div className="file-name">Загрузка документа...</div>
                    )}
                </div>

                <div className="source-divider">или</div>

                <div className="upload-row">
                    <Form.Label>Основной PDF файл</Form.Label>
                    <input
                        ref={pdfInputRef}
                        type="file"
                        accept="application/pdf"
                        onChange={handlePdfChange}
                        disabled={isChecking || isDocumentDataLoading}
                    />
                    {pdfFile && <div className="file-name">{pdfFile.name}</div>}
                </div>

                <div className="upload-row">
                    <Form.Label>Файл подписи (.sig)</Form.Label>
                    <input
                        ref={signatureInputRef}
                        type="file"
                        accept=".sig,application/pkcs7-signature,application/octet-stream"
                        onChange={handleSignatureChange}
                        disabled={isChecking}
                    />
                    {signatureFile && <div className="file-name">{signatureFile.name}</div>}
                </div>

                <div className="actions-row">
                    <Button
                        variant="primary"
                        onClick={handleVerification}
                        disabled={(!pdfFile && !selectedDocumentBase64) || !signatureFile || isChecking || isDocumentDataLoading}
                    >
                        {isChecking ? 'Проверка...' : 'Проверка'}
                    </Button>
                </div>
            </div>

            {verificationResult && (
                <div className="verification-result">
                    <h3>Результат проверки</h3>
                    <div><strong>Валидность:</strong> {verificationResult.is_valid ? 'Да' : 'Нет'}</div>
                    {signingTimeLabel && (
                        <div><strong>Дата и время подписи:</strong> {signingTimeLabel}</div>
                    )}

                    {verificationResult.checks && (
                        <div className="checks-block">
                            <h4>Детализация проверок</h4>
                            <ul>
                                {Object.entries(verificationResult.checks).map(([key, value]) => (
                                    <li key={key}>{key}: {String(value)}</li>
                                ))}
                            </ul>
                        </div>
                    )}

                    {verificationResult.attrs?.length > 0 && (
                        <div className="attrs-block">
                            <h4>Signed Attributes</h4>
                            {verificationResult.attrs.map((attr, index) => (
                                <div className="attr-item" key={`${attr.oid}-${index}`}>
                                    <div><strong>name:</strong> {attr.name}</div>
                                    <div><strong>oid:</strong> {attr.oid}</div>
                                    <pre>{JSON.stringify(attr.values, null, 2)}</pre>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}

export default SignatureVerification;
