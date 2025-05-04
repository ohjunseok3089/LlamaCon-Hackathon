import React, { useEffect, useState } from 'react';
import { useLocation, useNavigate, useParams } from 'react-router-dom';
import { Spinner, Button } from 'react-bootstrap';

const ResultPage = () => {
const { streamId } = useParams();

  const navigate = useNavigate();

  const [messages, setMessages] = useState([]);
  const [isDone, setIsDone] = useState(false);

  useEffect(() => {
    if (!streamId) return;

    const streamUrl = `http://0.0.0.0:1234/stream/${streamId}`;

    const eventSource = new EventSource(streamUrl);

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.status === 'complete') {
          setIsDone(true);
          eventSource.close();
        } else {
          setMessages([...messages, data.message]);
        }
      } catch (err) {
        console.error("Failed to parse SSE message:", event.data);
      }
    };

    eventSource.onerror = (err) => {
      console.error("SSE error:", err);
      eventSource.close();
    };

    return () => {
      eventSource.close();
    };
  }, [streamId]);

  if (!streamId) {
    return (
      <div style={{ padding: '2rem' }}>
        <h2>No stream URL provided</h2>
        <Button onClick={() => navigate('/')}>Back to Start</Button>
      </div>
    );
  }

  return (
    <div style={{ padding: '2rem' }}>
      <h2>Analyzing Your Video</h2>
      <div style={{
        marginTop: '1.5rem',
        padding: '1rem',
        border: '1px solid #ccc',
        borderRadius: '8px',
        minHeight: '200px',
        background: '#f9f9f9',
        whiteSpace: 'pre-wrap',
      }}>
        {messages.length === 0 ? (
          <div style={{ textAlign: 'center' }}>
            <Spinner animation="border" role="status" />
            <p>Waiting for analysis results...</p>
          </div>
        ) : (
          messages.map((msg, idx) => <div key={idx}>{msg}</div>)
        )}
      </div>

      {isDone && (
        <div style={{ marginTop: '2rem', textAlign: 'center' }}>
          <Button onClick={() => navigate('/')}>Record Again</Button>
        </div>
      )}
    </div>
  );
};

export default ResultPage;
