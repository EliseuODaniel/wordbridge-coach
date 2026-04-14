/** User Selection Component */

import React from 'react';
import ProfileCard from './ProfileCard';
import ConfirmDialog from './ConfirmDialog';
import UserProfileCreateForm from './UserProfileCreateForm';
import UserProfileEditModal from './UserProfileEditModal';
import { useUserSelection } from './useUserSelection';

type TrainingMode = 'spec4' | 'lingvist' | 'chat';

interface UserSelectionProps {
  onUserSelected: (userId: string) => void;
  onModeSelect: (mode: TrainingMode) => void;
  selectedMode: TrainingMode;
}

const UserSelection: React.FC<UserSelectionProps> = ({ onUserSelected, onModeSelect, selectedMode }) => {
  const {
    deleteConfirm,
    editLoading,
    editNativeLanguage,
    editTargetLanguage,
    editUsername,
    editWordGoalRank,
    editingUser,
    focusedIndex,
    loading,
    nativeLanguage,
    newUsername,
    targetLanguage,
    userToDelete,
    users,
    wordGoalRank,
    handleCancelEdit,
    handleConfirmDelete,
    handleCreateUser,
    handleDeleteProfile,
    handleEditProfile,
    handleKeyDown,
    handleSaveEdit,
    handleStartLearning,
    setDeleteConfirm,
    setEditNativeLanguage,
    setEditTargetLanguage,
    setEditUsername,
    setEditWordGoalRank,
    setNativeLanguage,
    setNewUsername,
    setTargetLanguage,
    setWordGoalRank,
  } = useUserSelection(selectedMode, onModeSelect, onUserSelected);

  return (
    <div className="min-h-screen bg-gray-900 flex items-center justify-center py-8" onKeyDown={handleKeyDown}>
      <div className="container mx-auto px-4 max-w-xl w-full">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-100 mb-2">
            FillTheWord
          </h1>
          <p className="text-gray-400">
            Learn vocabulary with smart spaced repetition
          </p>
        </div>

        {/* Hint about Lingvist mode */}
        <div className="bg-blue-900 bg-opacity-30 border border-blue-700 rounded-lg p-4 mb-6">
          <div className="flex items-start gap-3">
            <span className="text-2xl">✍️</span>
            <div>
              <div className="font-semibold text-blue-200 mb-1">Prefere treinar digitando?</div>
              <div className="text-sm text-blue-300">
                Escolha <strong>Lingvist</strong> ao iniciar um perfil para treinar com preenchimento de lacunas, hints progressivos e áudio pós-acerto.
              </div>
            </div>
          </div>
        </div>

        {/* Profiles Section */}
        <div className="bg-gray-800 rounded-lg p-6 shadow-xl">
          <h2 className="text-xl font-semibold text-gray-100 mb-6">
            Choose Your Profile
          </h2>

          {/* Existing Profiles */}
          {users.length > 0 && (
            <div className="mb-8">
              <p className="text-sm text-gray-400 mb-4">Select an existing profile:</p>

              {/* Scrollable profiles list */}
              <div
                className="max-h-96 overflow-y-auto space-y-3 pr-2"
                style={{ scrollbarWidth: 'thin', scrollbarColor: '#4B5563 #1F2937' }}
              >
                {users.map((user, index) => (
                  <ProfileCard
                    key={user.id}
                    profile={user}
                    onStart={handleStartLearning}
                    onEdit={handleEditProfile}
                    onDelete={handleDeleteProfile}
                    isFocused={focusedIndex === index}
                    selectedMode={selectedMode}
                  />
                ))}
              </div>
            </div>
          )}

          {/* Create New Profile Section */}
          <div className={`${users.length > 0 ? 'border-t border-gray-700 pt-6' : ''}`}>
            <p className="text-sm text-gray-400 mb-4">Or create a new profile:</p>

            <UserProfileCreateForm
              loading={loading}
              nativeLanguage={nativeLanguage}
              newUsername={newUsername}
              targetLanguage={targetLanguage}
              wordGoalRank={wordGoalRank}
              onNativeLanguageChange={setNativeLanguage}
              onSubmit={handleCreateUser}
              onTargetLanguageChange={setTargetLanguage}
              onUsernameChange={setNewUsername}
              onWordGoalRankChange={setWordGoalRank}
            />
          </div>

          {/* Demo Info */}
          <div className="mt-6 text-center">
            <p className="text-xs text-gray-500">
              Demo mode • Your progress is saved locally
            </p>
          </div>
        </div>

        <UserProfileEditModal
          editLoading={editLoading}
          editNativeLanguage={editNativeLanguage}
          editTargetLanguage={editTargetLanguage}
          editUsername={editUsername}
          editWordGoalRank={editWordGoalRank}
          isOpen={editingUser !== null}
          onCancel={handleCancelEdit}
          onNativeLanguageChange={setEditNativeLanguage}
          onSave={() => editingUser ? handleSaveEdit(editingUser) : Promise.resolve()}
          onTargetLanguageChange={setEditTargetLanguage}
          onUsernameChange={setEditUsername}
          onWordGoalRankChange={setEditWordGoalRank}
        />

        {/* Delete Confirmation Modal */}
        {deleteConfirm && userToDelete && (
          <ConfirmDialog
            isOpen={!!deleteConfirm}
            title="Delete this profile?"
            message={`This will remove all local progress for profile "${userToDelete.username}". This action cannot be undone.`}
            confirmText="Delete profile"
            cancelText="Cancel"
            onConfirm={() => handleConfirmDelete(deleteConfirm)}
            onCancel={() => setDeleteConfirm(null)}
            variant="danger"
          />
        )}
      </div>
    </div>
  );
};

export default UserSelection;
