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
    const [documentsCount, setDocumentsCount] = useState(0);

    const DOCUMENTS_URL = 'http://127.0.0.1:8000/api/docs';
    const offset = 10;

    useEffect(() => {
        (async function () {
            let params = {offset: currentPage * offset};

            switch (documentType) {
                case 'Необходимо подписать': 
                    params['signedByMe'] = 0;
                    break;
                case 'Ожидание подписи':
                    params['signed'] = 0;
                    params['signedByMe'] = 1;
                    params['sugnatures'] = 1;
                    break;
            }

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
                setDocumentsCount(result.data?.papers.length);
                Cookies.set('documentsCount', result.data?.papers.length, { path: '/' });
                setFileList(result.data?.papers);
                setPages(Array(Number(countOfDocuments)));
            } catch (err) {
                console.log(err);
        
                return;
            }
        })();
    }, [documentType, currentPage]);

    // 👇 files is not an array, but it's iterable, spread to get an array of files
    const files = fileList ? [...fileList] : [];

    const setPage = async (currentPage) => {
        setCurrentPage(currentPage.selected);
    }

    const setType = async (type) => {
        setCurrentPage(0);
        setDocumentType(type);
    }

    const showPdfClick = async (i) => {

        if (fileList[i].base64 == undefined) {
            let result = await axios.patch(
                DOCUMENTS_URL, null,
                {
                    params:{
                        doc_id: fileList[i].id
                    }
                }
            );
            fileList[i].base64 = result.data?.base64;
        }
        setFileName(fileList[i].base64);
        setFileId(fileList[i].id);
    }

    const deleteDoc = async (i) => {
        const result = await axios.delete(
                    DOCUMENTS_URL,
                    { 
                        params:{
                            doc_id: fileList[i].id
                        }
                    }
                );
                window.location.reload()

    }

    const saveDoc = async (i) => {
        const doc = fileList[i]; // Получаем данные текущего документа из стейта
    
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
                                <Dropdown.Item href="#/action-1" onClick={() => setType('Необходимо подписать')}>Необходимо подписать</Dropdown.Item>
                                <Dropdown.Item href="#/action-2" onClick={() => setType('Ожидание подписи')}>Ожидание подписи</Dropdown.Item>
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
                {files.map((file, i) => (
                    <tr key={i}>
                        <td>{file.title}</td>
                        <td className='hash-column'>{file.hash}</td>
                        <td>{file.created_at}</td>
                        <td></td>
                        <td colSpan={2}>
                            <div className="action-button">
                                <Button onClick={() => showPdfClick(i)}>Просмотр</Button>
                            </div>
                            <div className='action-button'>
                                <Button onClick={() => deleteDoc(i)}>Удалить</Button>
                            </div>
                            <div className='action-button'>
                                <Button onClick={() => saveDoc(i)}>Скачать</Button>
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