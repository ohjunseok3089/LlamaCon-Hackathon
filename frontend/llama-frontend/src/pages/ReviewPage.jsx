import React, { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Button, Modal, Spinner } from 'react-bootstrap';

const ReviewPage = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const videoBlob = location.state?.videoBlob;

  const [showModal, setShowModal] = useState(false);
  const [statusMessage, setStatusMessage] = useState("Uploading video...");

  const handleSubmit = async () => {
    try {
      const formData = new FormData();
      formData.append('video', videoBlob, 'recorded-video.webm');

      const uploadResponse = await fetch('http://0.0.0.0:1234/ask_llama', {
        method: 'POST',
        body: formData,
      });

      if (!uploadResponse.ok) {
        throw new Error('Upload failed');
      }

      setShowModal(true);

      const data = await uploadResponse.json();
      const streamUrl = data.stream_url; // e.g., "/stream/a1b2c3d4-e5f6-7890-1234-567890abcdef"
      const streamId = streamUrl.split('/').pop();

      setStatusMessage("Waiting for analysis to begin...");

      navigate(`/result/${streamId}`);

    } catch (err) {
      console.error(err);
      alert('Failed to submit video.');
      setShowModal(false);
    }
  };

  if (!videoBlob) {
    return (
      <div style={{ padding: '2rem' }}>
        <h2>No video found</h2>
        <Button variant="secondary" onClick={() => navigate('/')}>
          Go Back
        </Button>
      </div>
    );
  }

  return (
    <div style={{ padding: '2rem', textAlign: 'center' }}>
      <h2>Review Your Recording</h2>
      <video controls width="80%" src={URL.createObjectURL(videoBlob)} style={{ margin: '2rem 0' }} />
      <div>
        <Button variant="primary" onClick={handleSubmit}>
          Submit
        </Button>
        <Button variant="secondary" onClick={() => navigate('/')}>
          Retry
        </Button>
      </div>

      <Modal show={showModal} centered>
        <Modal.Header>
          <Modal.Title>Processing</Modal.Title>
        </Modal.Header>
        <Modal.Body style={{ textAlign: 'center' }}>
          <Spinner animation="border" role="status" />
          <p style={{ marginTop: '1rem' }}>{statusMessage}</p>
        </Modal.Body>
      </Modal>
    </div>
  );
};

export default ReviewPage;
