import React from 'react';
import { useLocation } from 'react-router-dom';

const HomePage = () => {
  const location = useLocation();
  const frames = location.state?.frames || [];

  return (
    <div>
      <h2>Captured Frames</h2>
      {frames.length === 0 && <p>No images received</p>}
      {frames.map((frame, index) => (
        <img
          key={index}
          src={frame.image}
          alt={`Frame ${index}`}
          width={320}
          style={{ margin: '10px' }}
        />
      ))}
    </div>
  );
};

export default HomePage;
