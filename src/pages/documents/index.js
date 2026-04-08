import Table from 'react-bootstrap/Table';
import Button from 'react-bootstrap/Button';
import Dropdown from 'react-bootstrap/Dropdown';
import React, { useRef, useState } from "react";
import { useEffect } from "react";
import "./documents.css";
import PdfReader from "../../components/pdf-reader/pdf-reader";
import Paginator from "../../components/paginator/paginator";
import axios from '../../api/axios';
import Cookies from 'js-cookie';
import { DateTime } from "luxon";



// отображает документы свойственные конкретному аккаунту 

function Index() {
    const [fileList, setFileList] = useState([]);
    const [file, setFileName] = useState('');
    const [fileId, setFileId] = useState('');
    const [isViewerOpen, setIsViewerOpen] = useState(false);
    const openTimerRef = useRef(null);
    const closeTimerRef = useRef(null);
    const scrollRafRef = useRef(null);
    const listEndRef = useRef(null);
    const [pages, setPages] = useState([1]);
    const [currentPage, setCurrentPage] = useState(0);
    const [documentType, setDocumentType] = useState('Все документы');

    const DOCUMENTS_URL = 'http://127.0.0.1:8000/api/docs';
    const offset = 10;
    const VIEWER_ANIMATION_MS = 300;

    useEffect(() => {
        return () => {
            if (openTimerRef.current) {
                clearTimeout(openTimerRef.current);
            }
            if (closeTimerRef.current) {
                clearTimeout(closeTimerRef.current);
            }
            if (scrollRafRef.current) {
                window.cancelAnimationFrame(scrollRafRef.current);
            }
        };
    }, []);

    useEffect(() => {
        (async function () {
            try {
                const result = await axios.get(
                    DOCUMENTS_URL
                );

                result.data.papers.map(item => {
                    item.created_at = DateTime.fromSeconds(item.created_at).toFormat('ff');

                    return item;
                })
                
                setFileList(result.data?.papers);
                const countOfDocuments = result.data?.papers.length;

                Cookies.set('documentsCount', countOfDocuments, { path: '/' });

                let countUnsignedDocuments = 0;
                for (let i = 0; i < countOfDocuments; i++) {
                    if (fileList[i].signing_status === 'unsigned') {
                        countUnsignedDocuments++;
                    }
                }
                Cookies.set('documentsCountUnsigned', countUnsignedDocuments, { path: '/' });
                Cookies.set('documentsCountFullySigned', countOfDocuments - countUnsignedDocuments, { path: '/' });

                setPages(countOfDocuments)
            } catch (err) {
                console.log(err);
        
                return;
            }
        })();
    }, [currentPage]);

    // 👇 files is not an array, but it's iterable, spread to get an array of files
    const files = (fileList ? [...fileList] : []).filter((item) => {
        if (documentType === 'unsigned' || documentType === 'fully_signed' || documentType === 'partially_signed') {
            return item.signing_status === documentType;
        }

        return true;
    });
    const documentsCount = files.length;

    const setPage = async (currentPage) => {
        setCurrentPage(currentPage.selected);
    }

    const setType = async (type) => {
        // Тут нужно разделить логику по фильтрации документов 
        // fileList[i].signing_status === 'unsigned' 
        setCurrentPage(0);
        setDocumentType(type);
    }

    const showPdfClick = async (doc) => {
        if (openTimerRef.current) {
            clearTimeout(openTimerRef.current);
        }
        if (closeTimerRef.current) {
            clearTimeout(closeTimerRef.current);
        }

        if (fileId === doc.id && file) {
            setIsViewerOpen(false);
            closeTimerRef.current = setTimeout(() => {
                setFileName('');
                setFileId('');
                closeTimerRef.current = null;
            }, VIEWER_ANIMATION_MS);
            return;
        }

        let selectedDocument = doc;

        if (selectedDocument.base64 === undefined) {
            let result = await axios.patch(
                DOCUMENTS_URL, null,
                {
                    params:{
                        doc_id: selectedDocument.id
                    }
                }
            );

            selectedDocument = {
                ...selectedDocument,
                base64: result.data?.base64
            };

            setFileList((prev) => prev.map((item) => (
                item.id === selectedDocument.id
                    ? { ...item, base64: selectedDocument.base64 }
                    : item
            )));
        }
        setIsViewerOpen(false);
        setFileName(selectedDocument.base64);
        setFileId(selectedDocument.id);

        openTimerRef.current = setTimeout(() => {
            setIsViewerOpen(true);
            openTimerRef.current = null;
        }, 20);
    }

    const deleteDoc = async (doc) => {
        await axios.delete(
                    DOCUMENTS_URL,
                    { 
                        params:{
                            doc_id: doc.id
                        }
                    }
                );
                window.location.reload()

    }

    const saveDoc = async (doc) => {
    
        try {
            const response = await axios.get(
                `http://127.0.0.1:8000/api/docs/download/`,
                { 
                    params: { doc_id: doc.id },
                    responseType: 'blob', // КРИТИЧНО: указываем, что ждем бинарные данные
                }
            );
            console.log(response.data)
            // Создаем временную ссылку в памяти браузера для Blob-объекта
            const url = window.URL.createObjectURL(new Blob([response.data])); // response.data
            const link = document.createElement('a');
            link.href = url;
            
            // Устанавливаем имя файла (берем из объекта документа)
            link.setAttribute('download', doc.title + '.pdf'); 
            
            // Добавляем ссылку в DOM, кликаем и удаляем
            document.body.appendChild(link);
            link.click();
            
            link.parentNode.removeChild(link);
            window.URL.revokeObjectURL(url); // Освобождаем память
        } catch (err) {
            console.error("Ошибка при скачивании:", err);
            alert("Не удалось скачать файл");
        }
    }

    const scrollToListEnd = () => {
        if (!listEndRef.current) {
            return;
        }

        if (scrollRafRef.current) {
            window.cancelAnimationFrame(scrollRafRef.current);
            scrollRafRef.current = null;
        }

        const startY = window.pageYOffset;
        const targetY = listEndRef.current.getBoundingClientRect().top + window.pageYOffset;
        const distance = targetY - startY;
        const duration = Math.min(380, Math.max(220, Math.abs(distance) * 0.22));
        let startTime = null;

        const animate = (timestamp) => {
            if (!startTime) {
                startTime = timestamp;
            }

            const elapsed = timestamp - startTime;
            const progress = Math.min(elapsed / duration, 1);
            const easedProgress = 1 - Math.pow(1 - progress, 2.2);

            window.scrollTo(0, startY + (distance * easedProgress));

            if (progress < 1) {
                scrollRafRef.current = window.requestAnimationFrame(animate);
            } else {
                scrollRafRef.current = null;
            }
        };

        scrollRafRef.current = window.requestAnimationFrame(animate);
    };

    return (
        <div className='documents'>
            <div className='summary'>
                Показано {documentsCount} из {pages?.length}
            </div>
            <div id="toolbar" className='row toolbar'>
                <div className='col'>
                    <nav aria-label="Page navigation">
                        <Paginator items={pages} itemsPerPage={offset} currentPage={currentPage} handlePageClick={setPage} />
                    </nav>
                </div>
                <div className='col col-auto'>
                    <nav aria-label="Page navigation">
                        <Dropdown>
                            <Dropdown.Toggle id="dropdown-basic">
                                {documentType}
                            </Dropdown.Toggle>

                            <Dropdown.Menu>
                                <Dropdown.Item href="#/action-1" onClick={() => setType('unsigned')}>Необходимо подписать</Dropdown.Item>
                                <Dropdown.Item href="#/action-2" onClick={() => setType('fully_signed')}>Подписанные</Dropdown.Item>
                                <Dropdown.Item href="#/action-3" onClick={() => setType('partially_signed')}>Частично подписанные</Dropdown.Item>
                                <Dropdown.Item href="#/action-4" onClick={() => setType('Все документы')}>Все документы</Dropdown.Item>
                            </Dropdown.Menu>
                        </Dropdown>
                    </nav>
                </div>
            </div>
            <Table striped bordered hover>
                <thead>
                <tr>
                    <th>Документ(Имя файла)</th>
                    <th className='hash-column'>Hash</th>
                    <th>Дата создания</th>
                    <th>Размер документа</th>
                    <th>Действия</th>
                </tr>
                </thead>
                <tbody>
                {files.map((doc) => (
                    <React.Fragment key={doc.id}>
                        <tr className={doc.signing_status === 'fully_signed' ? 'fully-signed-row' : ''}>
                            <td>
                                <div>{doc.title}</div>
                            </td>
                            <td className='hash-column'>{doc.hash}</td>
                            <td>{doc.created_at}</td>
                            <td></td>
                            <td colSpan={2}>
                                <div className="action-button">
                                    <Button onClick={() => showPdfClick(doc)}>
                                        {fileId === doc.id && file && isViewerOpen ? 'Скрыть' : 'Просмотр'}
                                    </Button>
                                </div>
                                <div className='action-button'>
                                    <Button onClick={() => deleteDoc(doc)}>Удалить</Button>
                                </div>
                                <div className='action-button'>
                                    <Button onClick={() => saveDoc(doc)}>Скачать</Button>
                                </div>
                            </td>
                        </tr>
                        {fileId === doc.id && file && (
                            <tr>
                                <td colSpan={5}>
                                    <div className={`pdf-viewer-row ${isViewerOpen ? 'open' : 'closed'}`}>
                                        <div className='pdf-viewer-center'>
                                        <PdfReader file={file} documentId={fileId}></PdfReader>
                                        </div>
                                    </div>
                                </td>
                            </tr>
                        )}
                    </React.Fragment>
                ))}
                </tbody>
            </Table>

            <div ref={listEndRef} />

            <button
                type='button'
                className='scroll-to-end-btn'
                onClick={scrollToListEnd}
                aria-label='Прокрутить к концу списка документов'
                title='К концу списка'
            >
                ↓
            </button>
        </div>
    );
}

export default Index;