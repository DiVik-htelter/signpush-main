import React, { useEffect, useRef, useState, useCallback } from 'react';
import Paginator from "../paginator/paginator";
import "bootstrap-icons/font/bootstrap-icons.css";
import "./pdf-reader.css";
import "bootstrap/dist/css/bootstrap.min.css";
import SignatureModal from '../signature-modal/signature-modal';

export default function PdfReader({file}) {
    const canvasRef = useRef(null);
    const [pages, setPages] = useState([1]);
    const [pdf, setPdf] = useState([1]);
    const [currentPage, setCurrentPage] = useState(1);
    const [isThumbnailsVisible, toogleTumbnail] = useState(false);
    const [pdfRef, setPdfRef] = useState("");
    const [squareX, setXCoord] = useState(null);
    const [squareY, setYCoord] = useState(null);
    const [squareWidth, setWidth] = useState(null);
    const [squareHeight, setHeight] = useState(null);
    const zoomScale = 1;
    const rotateAngle = 0;
    var pdf_image = "";

    useEffect(() => {
        (async function () {
            if (file) {
                // We import this here so that it's only loaded during client-side rendering.
                const pdfJS = await import('pdfjs-dist/build/pdf');
                pdfJS.GlobalWorkerOptions.workerSrc = window.location.origin + '/pdf.worker.js';
                let pdf = await pdfJS.getDocument(file).promise;

                setPages(Array.from({length: pdf.numPages}, (_, i) => i + 1));
                const page = await pdf.getPage(1);
                const viewport = page.getViewport({ scale: 2.5 });

                // Prepare canvas using PDF page dimensions.
                const canvas = canvasRef.current;
                const canvasContext = canvas.getContext('2d');

                canvas.height = viewport.height;
                canvas.width = viewport.width;

                // Render PDF page into canvas context.
                const renderContext = { canvasContext, viewport };
                page.render(renderContext);
                setPdf(pdf);
            }
        })();
    }, [file]);

    const setPage = async (currentPage) => {
      //Log user input
      const page = await pdf.getPage(currentPage.selected + 1);
      const viewport = page.getViewport({ scale: 2 });

      // Prepare canvas using PDF page dimensions.
      const canvas = canvasRef.current;
      const canvasContext = canvas.getContext('2d');

      canvas.height = viewport.height;
      canvas.width = viewport.width;

       // Render PDF page into canvas context.
      const renderContext = { canvasContext, viewport };
      page.render(renderContext);
      
      setCurrentPage(currentPage.selected + 1);
      saveInitialCanvas();
    };

    const renderPage = useCallback(
        (currentPage, pdf = pdfRef) => {
          pdf &&
            pdf.getPage(currentPage).then(function (page) {
              const viewport = page.getViewport({ scale: zoomScale, rotation: rotateAngle });
              const canvas = canvasRef.current;
              canvas.height = viewport?.height;
              canvas.width = viewport?.width;
              const renderContext = {
                canvasContext: canvas?.getContext("2d"),
                viewport: viewport,
                textContent: pdfRef,
              };
    
              page.render(renderContext);
            });
        },
        [pdfRef, file]
      );
  var cursorInCanvas = false;
  var canvasOfDoc = canvasRef?.current;
  var ctx;
  var startX;
  var startY;
  var offsetX;
  var offsetY;

  const saveInitialCanvas = () => {
    if (canvasOfDoc?.getContext) {
      var canvasPic = new Image();
      canvasPic.src = canvasOfDoc.toDataURL();
      pdf_image = canvasPic;
    }
  };

  useEffect(() => {
    if (canvasOfDoc) {
      ctx = canvasOfDoc.getContext("2d");
      var canvasOffset = canvasOfDoc.getBoundingClientRect();
      offsetX = canvasOffset.left;
      offsetY = canvasOffset.top;
    }
  }, [canvasOfDoc, pdfRef,  renderPage, file]);

  function handleMouseIn(e) {
    if (typeof pdf_image == "string") {
      saveInitialCanvas();
    }
    e.preventDefault();
    e.stopPropagation();
    startX = ((e.offsetX * canvasOfDoc.width) / canvasOfDoc.clientWidth) | 0;
    startY = ((e.offsetY * canvasOfDoc.width) / canvasOfDoc.clientWidth) | 0;

    cursorInCanvas = true;
  }

  function handleMouseOut(e) {
    e.preventDefault();
    e.stopPropagation();
    cursorInCanvas = false;
  }

  function handleMouseUp(e) {
    e.preventDefault();
    e.stopPropagation();
    cursorInCanvas = false;
  }

  function handleMouseMove(e) {
    e.preventDefault();
    e.stopPropagation();
    if (!cursorInCanvas) {
      return;
    }
    let mouseX = ((e.offsetX * canvasOfDoc.width) / canvasOfDoc.clientWidth) | 0;
    let mouseY = ((e.offsetY * canvasOfDoc.width) / canvasOfDoc.clientWidth) | 0;

    var width = mouseX - startX;
    var height = mouseY - startY;
    if (ctx) {
      ctx?.clearRect(0, 0, canvasOfDoc.width, canvasOfDoc.height);
      ctx?.drawImage(pdf_image, 0, 0);
      ctx.beginPath();
      ctx.rect(startX, startY, width, height);
      ctx.strokeStyle = "#1B9AFF";
      ctx.lineWidth = 5;
      ctx.stroke();

      setXCoord(startX);
      setYCoord(startY);

      setWidth(width);
      setHeight(height);
    }
  }

  canvasOfDoc?.addEventListener("mousedown", function (e) {
    handleMouseIn(e);
  });
  canvasOfDoc?.addEventListener("mousemove", function (e) {
    handleMouseMove(e);
  });
  canvasOfDoc?.addEventListener("mouseup", function (e) {
    handleMouseUp(e);
  });
  canvasOfDoc?.addEventListener("mouseout", function (e) {
    handleMouseOut(e);
  });

  const handleCallback = (childData) => {
    // Update the name in the component's state

    const canvas = canvasRef.current;
    const canvasContext = canvas.getContext('2d');

    var canvasPic = new Image();
    canvasPic.src = childData;
    pdf_image = canvasPic;

    pdf_image.onload = () => {
      if (squareHeight === 0 || squareHeight === 0 || squareHeight === null || squareWidth === null) {
        canvasContext.drawImage(pdf_image, 0, 0);
      } else {
        canvasContext.drawImage(pdf_image, squareX, squareY, squareWidth, squareHeight);
      }
    };
  }

  const handleClearClick = async () => {
     //Log user input
     const page = await pdf.getPage(currentPage);
     const viewport = page.getViewport({ scale: 2 });

     // Prepare canvas using PDF page dimensions.
     const canvas = canvasRef.current;
     const canvasContext = canvas.getContext('2d');

     canvas.height = viewport.height;
     canvas.width = viewport.width;

      // Render PDF page into canvas context.
     const renderContext = { canvasContext, viewport };
     page.render(renderContext);
      
     if (typeof pdf_image == "string") {
       saveInitialCanvas();
     }
  }

    return <div>
        <div id="toolbar" className='row toolbar'>
            {/* <div className='col col-md-1'>
                <button type="button" className="btn btn-outline-secondary">
                    <i className="bi bi-layout-sidebar"></i> 
                </button>
            </div> */}
            <div className='col'>
                <nav aria-label="Page navigation">
                    <Paginator items={pages} itemsPerPage={1} currentPage={currentPage} handlePageClick={setPage} />
                </nav>
            </div>
            <div className='col'>
                {/* <div className="btn-group">
                    <button type="button" className="btn btn-outline-secondary">
                        <i className="bi bi-zoom-out"></i> 
                        <span className="visually-hidden">Button</span>
                    </button>
                    <input type="text" className="form-control" placeholder="" aria-label="Input group example" aria-describedby="basic-addon1"/>
                    <button type="button" className="btn btn-outline-secondary">
                        <i className="bi bi-zoom-in"></i> 
                        <span className="visually-hidden">Button</span>
                    </button>
                </div> */}
            </div>
            <div className='col col-auto'>
              <button type="button" className="btn btn-outline-secondary" onClick={handleClearClick}>
                <i className="bi bi-eraser"></i>
              </button>
            </div>
            <div className='col col-auto'>
              <SignatureModal handleCallback={handleCallback}></SignatureModal>
            </div>
        </div>
        <div id="viewport" role="main"></div>
        <div className='pdf-container'>
            {/* <div className={isThumbnailsVisible ? "pdf-thumbnails pdf-thumbnails-active" : "pdf-thumbnails"}></div> */}
            <div className={isThumbnailsVisible ? "pdf-content pdf-content-active" : "pdf-content"}>
                <canvas ref={canvasRef} style={{ height: '100vh' }} />
            </div>
        </div>
    </div>;
}