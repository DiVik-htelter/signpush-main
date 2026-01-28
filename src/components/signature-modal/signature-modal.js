import { useState, useRef } from 'react';
import Button from 'react-bootstrap/Button';
import Modal from 'react-bootstrap/Modal';
import SignatureCanvas from 'react-signature-canvas';
import './signature-modal.css';

function SignatureModal({handleCallback}) {
  const [show, setShow] = useState(false);
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
          <div className={'sigContainer'}>
            <SignatureCanvas canvasProps={{ className: 'sigPad'}} ref={(ref) => { canvasRef = ref }}/>
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