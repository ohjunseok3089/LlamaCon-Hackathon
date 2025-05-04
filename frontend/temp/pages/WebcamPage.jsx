import React, { useRef, useState } from 'react';
import Webcam from 'react-webcam';
import { useNavigate } from 'react-router-dom';

import { Button, Modal } from 'react-bootstrap';


const videoConstraints = {
  facingMode: 'user',
};

const MAX_DURATION_MS = 3 * 1000; // 10 minutes in milliseconds

const WebcamPage = () => {
  const navigate = useNavigate();

  const webcamRef = useRef(null); // Ref to the webcam component
  const mediaRecorderRef = useRef(null); // Ref to store media recorder instance
  const [isRecording, setIsRecording] = useState(false); // State to track if we're recording
  const [showRecorded, setShowRecorded] = useState(false); // State to track if warning should be shown
  const [showWarning, setShowWarning] = useState(false); // State to track if warning should be shown
  const [blob, setBlob] = useState(""); // State to track if we're recording

  const handleModalClose = () => {
    setShowRecorded(false);
    setShowWarning(false);
  }

  const handleButtonClick = async () => {
    if (isRecording) {
      // Stop recording if already recording
      mediaRecorderRef.current.stop();
    } else {
      // Start recording
      const recordedChunks = [];
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'user' },
        audio: true,
      });

      if (webcamRef.current) {
        webcamRef.current.srcObject = stream; // Show webcam feed
      }

      // Initialize MediaRecorder to record both video and audio
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'video/webm',
      });

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          recordedChunks.push(event.data);
        }
      };

      mediaRecorder.onstop = () => {
        // Combine all recorded chunks into one blob
        setIsRecording(false);
        stream.getTracks().forEach((track) => track.stop()); // cleanup

        const blobCreated = new Blob(recordedChunks, { type: 'video/webm' });
        setBlob(blobCreated);

        setShowRecorded(true);
      };

      mediaRecorder.start();
      mediaRecorderRef.current = mediaRecorder; // Store the recorder instance
      setIsRecording(true); // Update the state to indicate recording has started

      // Set a timeout to stop recording after 10 minutes
      setTimeout(() => {
        if (mediaRecorder.state !== 'inactive') {
          setShowWarning(true); // Show warning popup when recording is automatically stopped

          mediaRecorder.stop();
        }
      }, MAX_DURATION_MS);
    }
  };

  return (
    <div>
    <div style={{ width: '100vw', height: '100vh', position: 'relative', overflow: 'hidden' }}>
      <Webcam
        ref={webcamRef}
        audio={false} // We are handling audio via the MediaRecorder API
        screenshotFormat="image/jpeg"
        videoConstraints={videoConstraints}
        style={{
          width: '100%',
          height: '100%',
          objectFit: 'cover',
        }}
      />
    </div>
    <button
        onClick={handleButtonClick}
        style={{
          position: 'absolute',
          bottom: '10%',
          left: '50%',
          transform: 'translateX(-50%)',
          padding: '10px 20px',
          fontSize: '16px',
          zIndex: 10,
        }}
      >
        {isRecording ? 'Stop Recording' : 'Start Recording'}
      </button>
      <Modal show={showRecorded} centered>
        <Modal.Header>
          <Modal.Title>Video Recorded</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <p>{showWarning ? 'Your recording was automatically stopped after 10 minutes.' : ''}</p>
          <p>Your video is recorded successfully!</p>
        </Modal.Body>
        <Modal.Footer>
        <Button
            variant="primary"
            onClick={() => navigate('/review', { state: { videoBlob: blob } })}
          >
            Continue
          </Button>
          <Button variant="secondary" onClick={handleModalClose}>
            Retry
          </Button>
        </Modal.Footer>
      </Modal>
    </div>
  );
};

export default WebcamPage;
