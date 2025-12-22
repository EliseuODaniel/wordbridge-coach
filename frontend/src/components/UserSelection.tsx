/** User Selection Component */

import React, { useState, useEffect, useRef } from 'react';
import { usersApi, type CreateUserRequest, type UpdateUserRequest } from '../services/api';
import ProfileCard, { type ProfileStats, type Profile } from './ProfileCard';
import ConfirmDialog from './ConfirmDialog';

interface UserSelectionProps {
  onUserSelected: (userId: string) => void;
}

// Language options based on API specification
const TARGET_LANGUAGES = [
  { code: 'en', name: 'English', flag: '🇺🇸' },
  { code: 'fr', name: 'French', flag: '🇫🇷' }
];

const NATIVE_LANGUAGES = [
  { code: 'pt', name: 'Português', flag: '🇧🇷' },
  { code: 'es', name: 'Español', flag: '🇪🇸' },
  { code: 'fr', name: 'Français', flag: '🇫🇷' },
  { code: 'en', name: 'English', flag: '🇺🇸' }
];

const VOCABULARY_GOALS = [
  { rank: 100, label: '100 words', description: 'Basic conversations' },
  { rank: 500, label: '500 words', description: 'Elementary level' },
  { rank: 1500, label: '1500 words', description: 'Intermediate level' },
  { rank: 3000, label: '3000 words', description: 'Advanced level' },
  { rank: 5000, label: '5000 words', description: 'Fluent conversations' },
  { rank: 10000, label: '10000 words', description: 'Near-native vocabulary' }
];

const UserSelection: React.FC<UserSelectionProps> = ({ onUserSelected }) => {
  const [users, setUsers] = useState<Profile[]>([]);
  const [newUsername, setNewUsername] = useState('');
  const [targetLanguage, setTargetLanguage] = useState('en');
  const [nativeLanguage, setNativeLanguage] = useState('pt');
  const [wordGoalRank, setWordGoalRank] = useState(100);
  const [loading, setLoading] = useState(false);

  // Edit mode states
  const [editingUser, setEditingUser] = useState<string | null>(null);
  const [editUsername, setEditUsername] = useState('');
  const [editTargetLanguage, setEditTargetLanguage] = useState('en');
  const [editNativeLanguage, setEditNativeLanguage] = useState('pt');
  const [editWordGoalRank, setEditWordGoalRank] = useState(100);  // Spec4: goal edition
  const [editLoading, setEditLoading] = useState(false);

  // Delete confirmation state
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null);

  // Focus management for keyboard navigation
  const [focusedIndex, setFocusedIndex] = useState<number | null>(null);
  const profilesListRef = useRef<HTMLDivElement>(null);

  // Load existing users
  useEffect(() => {
    loadUsers();
  }, []);

  const loadUsers = async () => {
    try {
      const usersFromApi = await usersApi.listUsers();
      // Add placeholder stats for now - in real app these would come from API
      const usersWithStats: Profile[] = usersFromApi.map(user => ({
        ...user,
        target_language: 'en', // Default target language since it's not returned by API
        stats: {
          mastered_words: Math.floor(Math.random() * 500), // Placeholder
          accuracy: 60 + Math.floor(Math.random() * 35) // Placeholder between 60-95%
        }
      }));
      setUsers(usersWithStats);
    } catch (error) {
      console.error('Error loading users:', error);
    }
  };

  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newUsername.trim() || loading) return;

    setLoading(true);
    try {
      const userData: CreateUserRequest = {
        username: newUsername.trim(),
        language_preference: nativeLanguage,
        target_language: targetLanguage,
        word_goal_rank: wordGoalRank
      };

      const newUser = await usersApi.createUser(userData);
      // Add placeholder stats for the new user
      const userWithStats = {
        ...newUser,
        stats: { mastered_words: 0, accuracy: 0 } as ProfileStats
      };
      setUsers([...users, userWithStats]);
      setNewUsername('');
      onUserSelected(newUser.id);
    } catch (error) {
      console.error('Error creating user:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleStartLearning = (userId: string) => {
    onUserSelected(userId);
  };

  const handleEditProfile = (userId: string) => {
    const user = users.find(u => u.id === userId);
    if (user) {
      setEditingUser(userId);
      setEditUsername(user.username);
      setEditTargetLanguage(user.target_language || 'en');
      setEditNativeLanguage(user.language_preference);
      setEditWordGoalRank(100);  // Default for now - backend doesn't return current goal
    }
  };

  const handleDeleteProfile = (userId: string) => {
    setDeleteConfirm(userId);
  };

  const handleCancelEdit = () => {
    setEditingUser(null);
    setEditUsername('');
    setEditTargetLanguage('en');
    setEditNativeLanguage('pt');
    setEditWordGoalRank(100);
    setEditLoading(false);
  };

  const handleSaveEdit = async (userId: string) => {
    if (!editUsername.trim() || editLoading) return;

    setEditLoading(true);
    try {
      const updateData: UpdateUserRequest = {
        username: editUsername.trim(),
        language_preference: editNativeLanguage,
        target_language: editTargetLanguage,
        word_goal_rank: editWordGoalRank  // Spec4: include goal in update
      };

      const updatedUser = await usersApi.updateUser(userId, updateData);
      setUsers(users.map(user =>
        user.id === userId ? updatedUser : user
      ));
      handleCancelEdit();
    } catch (error) {
      console.error('Error updating user:', error);
    } finally {
      setEditLoading(false);
    }
  };

  const handleConfirmDelete = async (userId: string) => {
    try {
      await usersApi.deleteUser(userId);
      setUsers(users.filter(user => user.id !== userId));
      setDeleteConfirm(null);
    } catch (error) {
      console.error('Error deleting user:', error);
    }
  };

  // Keyboard navigation handler
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (users.length === 0) return;

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setFocusedIndex(prev => prev === null ? 0 : Math.min(prev + 1, users.length - 1));
        break;
      case 'ArrowUp':
        e.preventDefault();
        setFocusedIndex(prev => prev === null ? 0 : Math.max(prev - 1, 0));
        break;
      case 'Enter':
        if (focusedIndex !== null && users[focusedIndex]) {
          e.preventDefault();
          handleStartLearning(users[focusedIndex].id);
        }
        break;
    }
  };

  const userToDelete = users.find(u => u.id === deleteConfirm);

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
                ref={profilesListRef}
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
                  />
                ))}
              </div>
            </div>
          )}

          {/* Create New Profile Section */}
          <div className={`${users.length > 0 ? 'border-t border-gray-700 pt-6' : ''}`}>
            <p className="text-sm text-gray-400 mb-4">Or create a new profile:</p>

            <form onSubmit={handleCreateUser} className="space-y-4">
              {/* Name Input */}
              <div>
                <input
                  type="text"
                  value={newUsername}
                  onChange={(e) => setNewUsername(e.target.value)}
                  placeholder="Enter your name"
                  className="w-full px-4 py-3 bg-gray-700 text-gray-100 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 placeholder-gray-500"
                  disabled={loading}
                  autoComplete="name"
                  data-testid="profile-create-name"
                />
              </div>

              {/* Target Language Toggle */}
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-2">
                  I want to learn:
                </label>
                <div className="flex gap-2 bg-gray-700 rounded-lg p-1">
                  {TARGET_LANGUAGES.map((lang) => (
                    <button
                      key={lang.code}
                      type="button"
                      onClick={() => setTargetLanguage(lang.code)}
                      className={`
                        flex-1 px-3 py-2 rounded-md font-medium transition-all duration-200 text-sm
                        ${targetLanguage === lang.code
                          ? 'bg-primary-600 text-white shadow-sm'
                          : 'text-gray-300 hover:text-white hover:bg-gray-600'
                        }
                      `}
                      data-testid={`profile-target-${lang.code}`}
                    >
                      <span className="mr-2">{lang.flag}</span>
                      {lang.name}
                    </button>
                  ))}
                </div>
              </div>

              {/* Native Language Dropdown */}
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-2">
                  My native language:
                </label>
                <select
                  value={nativeLanguage}
                  onChange={(e) => setNativeLanguage(e.target.value)}
                  className="w-full px-4 py-2 bg-gray-700 text-gray-100 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 border border-gray-600"
                  disabled={loading}
                  data-testid="profile-native-lang"
                >
                  {NATIVE_LANGUAGES.map((lang) => (
                    <option key={lang.code} value={lang.code}>
                      {lang.flag} {lang.name}
                    </option>
                  ))}
                </select>
              </div>

              {/* Vocabulary Goal Selector */}
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-3">
                  My vocabulary goal:
                </label>
                <div className="bg-gray-700 rounded-lg p-4 border border-gray-600">
                  <div className="flex justify-between text-xs text-gray-400 mb-2">
                    <span>Basic</span>
                    <span>Advanced</span>
                  </div>
                  <div className="space-y-2">
                    <input
                      type="range"
                      min="100"
                      max="10000"
                      step="100"
                      value={wordGoalRank}
                      onChange={(e) => setWordGoalRank(parseInt(e.target.value))}
                      className="w-full h-2 bg-gray-600 rounded-lg appearance-none cursor-pointer slider"
                      style={{
                        background: `linear-gradient(to right, #3b82f6 0%, #3b82f6 ${((wordGoalRank - 100) / (10000 - 100)) * 100}%, #4b5563 ${((wordGoalRank - 100) / (10000 - 100)) * 100}%, #4b5563 100%)`
                      }}
                      disabled={loading}
                      data-testid="profile-goal-slider"
                    />
                    <div className="text-center">
                      <span className="text-lg font-semibold text-blue-400">
                        {VOCABULARY_GOALS.find(g => g.rank === wordGoalRank)?.label || `${wordGoalRank} words`}
                      </span>
                    </div>
                    <div className="text-xs text-gray-500 text-center">
                      {VOCABULARY_GOALS.find(g => g.rank === wordGoalRank)?.description}
                    </div>
                  </div>
                </div>
              </div>

              {/* Create & Start Button */}
              <button
                type="submit"
                disabled={!newUsername.trim() || loading}
                className="w-full px-4 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 focus:ring-offset-gray-800 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
                data-testid="profile-create-start"
              >
                {loading ? (
                  <div className="flex items-center justify-center">
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                    Creating Profile...
                  </div>
                ) : (
                  'Create & Start Learning'
                )}
              </button>
            </form>
          </div>

          {/* Demo Info */}
          <div className="mt-6 text-center">
            <p className="text-xs text-gray-500">
              Demo mode • Your progress is saved locally
            </p>
          </div>
        </div>

        {/* Edit Profile Modal */}
        {editingUser && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <div className="bg-gray-800 rounded-lg p-6 max-w-md w-full">
              <h3 className="text-lg font-semibold text-gray-100 mb-4">
                Edit Profile
              </h3>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-400 mb-1">
                    Profile Name
                  </label>
                  <input
                    type="text"
                    value={editUsername}
                    onChange={(e) => setEditUsername(e.target.value)}
                    className="w-full px-3 py-2 bg-gray-700 text-gray-100 rounded focus:outline-none focus:ring-2 focus:ring-primary-500"
                    disabled={editLoading}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-400 mb-1">
                    Target Language:
                  </label>
                  <div className="grid grid-cols-2 gap-2">
                    {TARGET_LANGUAGES.map((lang) => (
                      <button
                        key={lang.code}
                        type="button"
                        onClick={() => setEditTargetLanguage(lang.code)}
                        className={`px-3 py-2 text-sm rounded font-medium transition-colors ${
                          editTargetLanguage === lang.code
                            ? 'bg-primary-600 text-white'
                            : 'bg-gray-600 text-gray-300 hover:bg-gray-500'
                        }`}
                      >
                        <span className="mr-1">{lang.flag}</span>
                        {lang.name}
                      </button>
                    ))}
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-400 mb-1">
                    Native Language:
                  </label>
                  <select
                    value={editNativeLanguage}
                    onChange={(e) => setEditNativeLanguage(e.target.value)}
                    className="w-full px-3 py-2 bg-gray-600 text-gray-100 rounded focus:outline-none focus:ring-2 focus:ring-primary-500"
                    disabled={editLoading}
                  >
                    {NATIVE_LANGUAGES.map((lang) => (
                      <option key={lang.code} value={lang.code}>
                        {lang.flag} {lang.name}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Spec4: Vocabulary Goal Selector in Edit Modal */}
                <div>
                  <label className="block text-sm font-medium text-gray-400 mb-1">
                    My vocabulary goal:
                  </label>
                  <input
                    type="range"
                    min="100"
                    max="10000"
                    step="100"
                    value={editWordGoalRank}
                    onChange={(e) => setEditWordGoalRank(parseInt(e.target.value))}
                    className="w-full h-2 bg-gray-600 rounded-lg appearance-none cursor-pointer"
                    style={{
                      background: `linear-gradient(to right, #3b82f6 0%, #3b82f6 ${((editWordGoalRank - 100) / (10000 - 100)) * 100}%, #4b5563 ${((editWordGoalRank - 100) / (10000 - 100)) * 100}%, #4b5563 100%)`
                    }}
                    disabled={editLoading}
                  />
                  <div className="flex justify-between items-center mt-2">
                    <span className="text-sm font-semibold text-gray-100">
                      {VOCABULARY_GOALS.find(g => g.rank === editWordGoalRank)?.label || `${editWordGoalRank} words`}
                    </span>
                    <span className="text-xs text-gray-400">
                      {VOCABULARY_GOALS.find(g => g.rank === editWordGoalRank)?.description}
                    </span>
                  </div>
                </div>
              </div>

              <div className="flex gap-3 mt-6">
                <button
                  onClick={() => handleSaveEdit(editingUser)}
                  disabled={!editUsername.trim() || editLoading}
                  className="flex-1 px-4 py-2 bg-primary-600 text-white rounded hover:bg-primary-700 disabled:opacity-50 transition-colors"
                >
                  {editLoading ? 'Saving...' : 'Save Changes'}
                </button>
                <button
                  onClick={handleCancelEdit}
                  disabled={editLoading}
                  className="flex-1 px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-500 disabled:opacity-50 transition-colors"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        )}

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