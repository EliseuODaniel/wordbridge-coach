/** Main App Component */

import { useEffect, useState } from 'react';
import StudySession from './components/StudySession';
import LingvistSession from './components/LingvistSession';
import ChatCoachSession from './components/ChatCoachSession';
import UserSelection from './components/UserSelection';
import type { TrainingMode } from './components/trainingModes';
import { healthApi } from './services/apiHealth';
import './App.css';

function getInitialTrainingMode(): TrainingMode {
  const params = new URLSearchParams(window.location.search);
  const modeParam = params.get('mode');
  if (modeParam === 'lingvist' || modeParam === 'spec4' || modeParam === 'chat') {
    return modeParam;
  }

  const savedMode = localStorage.getItem('preferredTrainingMode');
  if (savedMode === 'lingvist' || savedMode === 'spec4' || savedMode === 'chat') {
    return savedMode;
  }

  return 'spec4';
}

function App() {
  const [selectedUserId, setSelectedUserId] = useState<string | null>(null);
  const [trainingMode, setTrainingMode] = useState<TrainingMode>(getInitialTrainingMode);

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
  };

  const handleModeSelect = (mode: TrainingMode) => {
    localStorage.setItem('preferredTrainingMode', mode);
    setTrainingMode(mode);
  };

  return (
    <div className="App app-frame">
      {!selectedUserId ? (
        <UserSelection
          onUserSelected={handleUserSelected}
          onModeSelect={handleModeSelect}
          selectedMode={trainingMode}
        />
      ) : trainingMode === 'lingvist' ? (
        <LingvistSession
          userId={selectedUserId}
          onExit={handleExit}
          onModeChange={handleModeSelect}
        />
      ) : trainingMode === 'chat' ? (
        <ChatCoachSession
          userId={selectedUserId}
          onExit={handleExit}
          onModeChange={handleModeSelect}
        />
      ) : (
        <StudySession
          userId={selectedUserId}
          onModeChange={handleModeSelect}
          onExit={handleExit}
        />
      )}
    </div>
  );
}

export default App;
