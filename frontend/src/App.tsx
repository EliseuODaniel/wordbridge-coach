/** Main App Component */

import React, { useState } from 'react';
import StudySession from './components/StudySession';
import UserSelection from './components/UserSelection';
import { healthApi } from './services/api';
import './App.css';

function App() {
  const [selectedUserId, setSelectedUserId] = useState<string | null>(null);

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

  const handleUserSelected = (userId: string) => {
    setSelectedUserId(userId);
  };

  return (
    <div className="App">
      {selectedUserId ? (
        <StudySession userId={selectedUserId} />
      ) : (
        <UserSelection onUserSelected={handleUserSelected} />
      )}
    </div>
  );
}

export default App;
