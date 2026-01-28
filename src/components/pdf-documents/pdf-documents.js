import Table from 'react-bootstrap/Table';
import Button from 'react-bootstrap/Button';
import React, { useState } from "react";
import jsSHA from "jssha";
import { DateTime } from "luxon";
import PdfReader from "../pdf-reader/pdf-reader";
import "./pdf-documents.css";

// Компонент, который возвращает строчку в перечне загруженных документов
// 
function PdfDocuments() {
    const [fileList, setFileList] = useState([]);
    const [inputKey, setInputKey] = useState(0);
    const [file, setFileName] = useState('');

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
    }

    // 👇 files is not an array, but it's iterable, spread to get an array of files
    const files = fileList ? [...fileList] : [];

    const showPdfClick = async (i) => {
        setFileName(fileList[i].base64);
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
                        <td>{file.name}</td>
                        <td className='hash-column'>{file.hash}</td>
                        <td>{file.created_at}</td>
                        <td>{(file.size / (1024)).toFixed(2) + ' KB'}</td>
                        <td colSpan={2}>
                            <div className="action-button">
                                <Button onClick={() => showPdfClick(i)}>Просмотр</Button>
                            </div>
                            <div className="action-button">
                                <Button>Подпись</Button>
                            </div>
                        </td>
                    </tr>
                ))}
                </tbody>
            </Table>
            {file && <PdfReader file={file}></PdfReader>}
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