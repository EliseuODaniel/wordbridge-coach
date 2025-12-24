/** Main App Component */

import { useState, useEffect } from 'react';
import StudySession from './components/StudySession';
import LingvistSession from './components/LingvistSession';
import UserSelection from './components/UserSelection';
import { healthApi } from './services/api';
import './App.css';

type TrainingMode = 'spec4' | 'lingvist';

function App() {
  const [selectedUserId, setSelectedUserId] = useState<string | null>(null);
  const [trainingMode, setTrainingMode] = useState<TrainingMode>('spec4');

  // Read mode from URL query param (for E2E testing)
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const modeParam = params.get('mode');
    if (modeParam === 'lingvist' || modeParam === 'spec4') {
      setTrainingMode(modeParam);
    }
  }, []);

  // Optional: Add API health check
  useEffect(() => {
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

  const handleExit = () => {
    setSelectedUserId(null);
    setTrainingMode('spec4'); // Reset to default
  };

  const handleModeSelect = (mode: TrainingMode) => {
    setTrainingMode(mode);
  };

  return (
    <div className="App">
      {!selectedUserId ? (
        <UserSelection
          onUserSelected={handleUserSelected}
          onModeSelect={handleModeSelect}
          selectedMode={trainingMode}
        />
      ) : trainingMode === 'lingvist' ? (
        <LingvistSession userId={selectedUserId} onExit={handleExit} />
      ) : (
        <StudySession userId={selectedUserId} />
      )}
    </div>
  );
}

export default App;
