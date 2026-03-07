import Table from 'react-bootstrap/Table';
import Button from 'react-bootstrap/Button';
import React, { useState } from "react";
import jsSHA from "jssha";
import { DateTime } from "luxon";
import axios from '../../api/axios';
import Cookies from 'js-cookie';
import PdfReader from "../pdf-reader/pdf-reader";
import "./pdf-documents.css";

// Компонент, который возвращает заголовок таблица и строчки в перечне загруженных документов
// главная страница с добавлением документов
function PdfDocuments() {
    const [fileList, setFileList] = useState([]);
    const [inputKey, setInputKey] = useState(0);
    const [file, setFileName] = useState('');
    const [selectedDocumentId, setSelectedDocumentId] = useState(null); // ID выбранного документа для подписи
    const DOCUMENTS_URL = 'http://127.0.0.1:8000/api/insertDocs';

    const handleFileChange = async ({currentTarget: {files}}) => {
        if (files && files.length) {
            setFileList(existing => existing.concat(Array.from(files)));
        }

        const promise = getBase64(files[0]);
        const base64 = await promise;

        const base64String = base64
            .replace('data:', '')
            .replace(/^.+,/, '');

        const shaObj = new jsSHA("SHA-256", "B64");
        shaObj.update(base64String);

        files[0]['hash'] = shaObj.getHash("B64");
        files[0]['created_at'] = DateTime.fromMillis(files[0].lastModified).toFormat('ff');
        files[0]['base64'] = base64;

        // Reset the input by forcing a new one
        setInputKey(key => key + 1);
        const currentFile = files[0]
        

        try {
            const result = await axios.post(
                DOCUMENTS_URL,
                JSON.stringify({
                    'id': 1,
                    'title': currentFile.name,
                    'hash': currentFile.hash,
                    'created_at': Math.floor(Date.now() / 1000), // деление на 1000 и округление вниз необходимы для получения секунд
                    'login': Cookies.get('user'),
                    'base64': currentFile.base64
                 
                })
                ,{ 
                    headers : {
                        // говорит серверу что отправляет запрос в json формате и ожидает ответ так же в json
                        'Content-Type': 'application/json',
                        "Accept": "application/json"
                        //'apiKey': '2e4ee3528082873f6407f3a42a85854156bef0b0ccb8336fd8843a3f13e2ff09'
                    },
                }
            );

            console.log('Операция отправки документа в БД: '+ result.data.success)
        } catch (err) {
            console.log(err);
    
            return;
        }

        
    }

    // 👇 files is not an array, but it's iterable, spread to get an array of files
    const files = fileList ? [...fileList] : [];

    const showPdfClick = async (i) => {
        // Устанавливаем base64 содержимое для просмотра
        setFileName(fileList[i].base64);
        
        // Сохраняем ID документа (для локально загруженных файлов используем индекс)
        // В реальном приложении здесь будет ID из базы данных
        setSelectedDocumentId(i + 1); // Временное решение для локальных файлов
    }

  
    return (
        <div>
            <div className="file-upload-container">
                <input key={inputKey} type="file" id="selectedFile" className="fileUpload"
                       onChange={handleFileChange}
                       accept="application/pdf"
                />
                <label htmlFor="selectedFile">
                    <a className="button btn btn-primary">Выберите файл</a>
                </label>
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
                        {/* data-label атрибуты используются для карточного вида на мобильных */}
                        <td data-label="Документ">{file.name}</td>
                        <td data-label="Hash" className='hash-column'>{file.hash}</td>
                        <td data-label="Дата создания">{file.created_at}</td>
                        <td data-label="Размер">{(file.size / (1024)).toFixed(2) + ' KB'}</td>
                        <td data-label="Действия" colSpan={2}>
                            <div className="action-button">
                                <Button onClick={() => showPdfClick(i)}>
                                    <i className="bi bi-eye"></i> Просмотр
                                </Button>
                            </div>
                            <div className="action-button">
                                <Button variant="success">
                                    <i className="bi bi-pen"></i> Подпись
                                </Button>
                            </div>
                        </td>
                    </tr>
                ))}
                </tbody>
            </Table>
            {file && <PdfReader file={file} documentId={selectedDocumentId}></PdfReader>}
        </div>
    );
}

function getBase64(file) {
    return new Promise(function(resolve, reject) {
        var reader = new FileReader();
        reader.onload = function() { resolve(reader.result); };
        reader.onerror = reject;
        reader.readAsDataURL(file);
    });
}


export default PdfDocuments;