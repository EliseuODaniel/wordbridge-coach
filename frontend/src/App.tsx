/** Main App Component */

import React from 'react';
import StudySession from './components/StudySession';
import { healthApi } from './services/api';
import './App.css';

function App() {
  // Optional: Add API health check
  React.useEffect(() => {
    const checkHealth = async () => {
      try {
        const health = await healthApi.checkHealth();
        console.log('API Health:', health);
      } catch (error) {
        console.error('API health check failed:', error);
      }
    };
    
    checkHealth();
  }, []);

  return (
    <div className="App">
      <StudySession />
    </div>
  );
}

export default App;
