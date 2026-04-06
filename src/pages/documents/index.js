import Table from 'react-bootstrap/Table';
import Button from 'react-bootstrap/Button';
import Dropdown from 'react-bootstrap/Dropdown';
import React, { useState } from "react";
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
    const [pages, setPages] = useState([1]);
    const [currentPage, setCurrentPage] = useState(0);
    const [documentType, setDocumentType] = useState('Все документы');

    const DOCUMENTS_URL = 'http://127.0.0.1:8000/api/docs';
    const offset = 10;

    useEffect(() => {
        (async function () {
            try {
                const result = await axios.get(
                    DOCUMENTS_URL
                );

                let countOfDocuments = result.data?.message?.substring(
                    result.data?.message.indexOf('are ') + 4, 
                    result.data?.message.lastIndexOf('papers')
                );

                result.data.papers.map(item => {
                    item.created_at = DateTime.fromSeconds(item.created_at).toFormat('ff');

                    return item;
                })
    

                console.log(result.data.papers)
                Cookies.set('documentsCount', result.data?.papers.length, { path: '/' });
                setFileList(result.data?.papers);
                setPages(Array(Number(countOfDocuments)));
            } catch (err) {
                console.log(err);
        
                return;
            }
        })();
    }, [currentPage]);

    // 👇 files is not an array, but it's iterable, spread to get an array of files
    const files = (fileList ? [...fileList] : []).filter((item) => {
        if (documentType === 'unsigned' || documentType === 'fully_signed') {
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
        setFileName(selectedDocument.base64);
        setFileId(selectedDocument.id);
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
                                <Dropdown.Item href="#/action-3" onClick={() => setType('Все документы')}>Все документы</Dropdown.Item>
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
                {files.map((file) => (
                    <tr key={file.id}>
                        <td>{file.title}</td>
                        <td className='hash-column'>{file.hash}</td>
                        <td>{file.created_at}</td>
                        <td></td>
                        <td colSpan={2}>
                            <div className="action-button">
                                <Button onClick={() => showPdfClick(file)}>Просмотр</Button>
                            </div>
                            <div className='action-button'>
                                <Button onClick={() => deleteDoc(file)}>Удалить</Button>
                            </div>
                            <div className='action-button'>
                                <Button onClick={() => saveDoc(file)}>Скачать</Button>
                            </div>
                        </td>
                    </tr>
                ))}
                </tbody>
            </Table>
            {file && <PdfReader file={file} documentId={fileId}></PdfReader>}
        </div>
    );
}

export default Index;