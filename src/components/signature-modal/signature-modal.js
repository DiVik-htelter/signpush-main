import { useState, useRef } from 'react';
import Button from 'react-bootstrap/Button';
import Modal from 'react-bootstrap/Modal';
import SignatureCanvas from 'react-signature-canvas';
import './signature-modal.css';

// Детально изучи проект, мне нужно что бы ты модифицировал окно подписи таким образом, что бы можно было менять толщину подписи. Так же нужно что бы после начальной подписи документа (не нажимая кнопку подписать, на серввер еще не передались никакие данные) графический штамп не закреплялся намертво, а его можно было перемещать по странице пдф документа и даже менять масштаб подписи

function SignatureModal({handleCallback}) {
  const [show, setShow] = useState(false);
  const [penWidth, setPenWidth] = useState(2);
  let canvasRef = useRef(null);

  const handleAdd = async () => {
    setShow(false);
    handleCallback(canvasRef.toDataURL());
  };
  const handleClose = () => setShow(false);
  const handleShow = () => setShow(true);

  return (
    <>
      <button type="button" className="btn btn-outline-secondary" variant="primary" onClick={handleShow}>
          <i className="bi bi-pen"></i> 
      </button>

      <Modal show={show} fullscreen={true} onHide={handleClose}>
        <Modal.Header closeButton>
          <Modal.Title>Место для подписи</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <div style={{ marginBottom: '10px' }}>
            <label>Толщина подписи: {penWidth}</label>
            <input 
              type="range"
              min="0.5"
              max="10.0"
              value={penWidth}
              onChange={(e) => setPenWidth(e.target.value)}
            />
          </div>
          <div className={'sigContainer'}>
            <SignatureCanvas 
            minWidth={penWidth -(penWidth / 1.5)}
            maxWidth={penWidth}
            velocityFilterWeight={0.7} 
            //throttle={penWidth+14}
            canvasProps={{ className: 'sigPad'}} 
            ref={(ref) => { canvasRef = ref }}/>
          </div>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={handleClose}>
            Отменить
          </Button>
          <Button variant="primary" onClick={handleAdd}>
            Добавить
          </Button>
        </Modal.Footer>
      </Modal>
    </>
  );
}

export default SignatureModal;