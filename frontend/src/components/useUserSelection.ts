import type React from 'react';
import { useCallback, useEffect, useState } from 'react';

import { usersApi, type CreateUserRequest, type UpdateUserRequest } from '../services/apiUsers';
import { statsService } from '../services/stats';
import type { Profile, ProfileStats } from './ProfileCard';
import { buildProfileStats } from './userSelectionConfig';

type TrainingMode = 'spec4' | 'lingvist' | 'chat';

interface UseUserSelectionResult {
  deleteConfirm: string | null;
  editLoading: boolean;
  editNativeLanguage: string;
  editTargetLanguage: string;
  editUsername: string;
  editWordGoalRank: number;
  editingUser: string | null;
  focusedIndex: number | null;
  loading: boolean;
  nativeLanguage: string;
  newUsername: string;
  targetLanguage: string;
  userToDelete?: Profile;
  users: Profile[];
  wordGoalRank: number;
  handleConfirmDelete: (userId: string) => Promise<void>;
  handleCreateUser: (event: React.FormEvent) => Promise<void>;
  handleDeleteProfile: (userId: string) => void;
  handleEditProfile: (userId: string) => void;
  handleKeyDown: (event: React.KeyboardEvent) => void;
  handleSaveEdit: (userId: string) => Promise<void>;
  handleStartLearning: (userId: string, mode: TrainingMode) => void;
  setDeleteConfirm: (userId: string | null) => void;
  setEditNativeLanguage: (value: string) => void;
  setEditTargetLanguage: (value: string) => void;
  setEditUsername: (value: string) => void;
  setEditWordGoalRank: (value: number) => void;
  setNativeLanguage: (value: string) => void;
  setNewUsername: (value: string) => void;
  setTargetLanguage: (value: string) => void;
  setWordGoalRank: (value: number) => void;
  handleCancelEdit: () => void;
}

export const useUserSelection = (
  selectedMode: TrainingMode,
  onModeSelect: (mode: TrainingMode) => void,
  onUserSelected: (userId: string) => void
): UseUserSelectionResult => {
  const [users, setUsers] = useState<Profile[]>([]);
  const [newUsername, setNewUsername] = useState('');
  const [targetLanguage, setTargetLanguage] = useState('en');
  const [nativeLanguage, setNativeLanguage] = useState('pt');
  const [wordGoalRank, setWordGoalRank] = useState(100);
  const [loading, setLoading] = useState(false);
  const [editingUser, setEditingUser] = useState<string | null>(null);
  const [editUsername, setEditUsername] = useState('');
  const [editTargetLanguage, setEditTargetLanguage] = useState('en');
  const [editNativeLanguage, setEditNativeLanguage] = useState('pt');
  const [editWordGoalRank, setEditWordGoalRank] = useState(100);
  const [editLoading, setEditLoading] = useState(false);
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null);
  const [focusedIndex, setFocusedIndex] = useState<number | null>(null);

  const loadUsers = useCallback(async () => {
    try {
      const usersFromApi = await usersApi.listUsers();
      const usersWithStats = await Promise.all(
        usersFromApi.map(async (user) => {
          try {
            const stats = await statsService.getBasicStats(user.id);
            return {
              ...user,
              stats: buildProfileStats(stats),
            } satisfies Profile;
          } catch (error) {
            console.warn(`Failed to load stats for user ${user.id}:`, error);
            return {
              ...user,
              stats: { mastered_words: 0, accuracy: 0 } satisfies ProfileStats,
            } satisfies Profile;
          }
        })
      );

      setUsers(usersWithStats);
    } catch (error) {
      console.error('Error loading users:', error);
    }
  }, []);

  useEffect(() => {
    loadUsers();
  }, [loadUsers]);

  const handleCreateUser = useCallback(async (event: React.FormEvent) => {
    event.preventDefault();
    if (!newUsername.trim() || loading) return;

    setLoading(true);
    try {
      const userData: CreateUserRequest = {
        username: newUsername.trim(),
        language_preference: nativeLanguage,
        target_language: targetLanguage,
        word_goal_rank: wordGoalRank,
      };

      const newUser = await usersApi.createUser(userData);
      const userWithStats = {
        ...newUser,
        stats: { mastered_words: 0, accuracy: 0 } as ProfileStats,
      };
      setUsers((prev) => [...prev, userWithStats]);
      setNewUsername('');

      localStorage.setItem('preferredTrainingMode', selectedMode);
      onUserSelected(newUser.id);
    } catch (error) {
      console.error('Error creating user:', error);
    } finally {
      setLoading(false);
    }
  }, [loading, nativeLanguage, newUsername, onUserSelected, selectedMode, targetLanguage, wordGoalRank]);

  const handleStartLearning = useCallback((userId: string, mode: TrainingMode) => {
    localStorage.setItem('preferredTrainingMode', mode);
    onModeSelect(mode);
    onUserSelected(userId);
  }, [onModeSelect, onUserSelected]);

  const handleEditProfile = useCallback((userId: string) => {
    const user = users.find((entry) => entry.id === userId);
    if (!user) {
      return;
    }

    setEditingUser(userId);
    setEditUsername(user.username);
    setEditTargetLanguage(user.target_language);
    setEditNativeLanguage(user.language_preference);
    setEditWordGoalRank(user.word_goal_rank);
  }, [users]);

  const handleDeleteProfile = useCallback((userId: string) => {
    setDeleteConfirm(userId);
  }, []);

  const handleCancelEdit = useCallback(() => {
    setEditingUser(null);
    setEditUsername('');
    setEditTargetLanguage('en');
    setEditNativeLanguage('pt');
    setEditWordGoalRank(100);
    setEditLoading(false);
  }, []);

  const handleSaveEdit = useCallback(async (userId: string) => {
    if (!editUsername.trim() || editLoading) return;

    setEditLoading(true);
    try {
      const updateData: UpdateUserRequest = {
        username: editUsername.trim(),
        language_preference: editNativeLanguage,
        target_language: editTargetLanguage,
        word_goal_rank: editWordGoalRank,
      };

      const updatedUser = await usersApi.updateUser(userId, updateData);
      setUsers((prev) => prev.map((user) => (
        user.id === userId
          ? {
              ...updatedUser,
              stats: user.stats,
            }
          : user
      )));
      handleCancelEdit();
    } catch (error) {
      console.error('Error updating user:', error);
    } finally {
      setEditLoading(false);
    }
  }, [editLoading, editNativeLanguage, editTargetLanguage, editUsername, editWordGoalRank, handleCancelEdit]);

  const handleConfirmDelete = useCallback(async (userId: string) => {
    try {
      await usersApi.deleteUser(userId);
      setUsers((prev) => prev.filter((user) => user.id !== userId));
      setDeleteConfirm(null);
    } catch (error) {
      console.error('Error deleting user:', error);
    }
  }, []);

  const handleKeyDown = useCallback((event: React.KeyboardEvent) => {
    if (users.length === 0) return;

    switch (event.key) {
      case 'ArrowDown':
        event.preventDefault();
        setFocusedIndex((prev) => prev === null ? 0 : Math.min(prev + 1, users.length - 1));
        break;
      case 'ArrowUp':
        event.preventDefault();
        setFocusedIndex((prev) => prev === null ? 0 : Math.max(prev - 1, 0));
        break;
      case 'Enter':
        if (focusedIndex !== null && users[focusedIndex]) {
          event.preventDefault();
          handleStartLearning(users[focusedIndex].id, selectedMode);
        }
        break;
      default:
        break;
    }
  }, [focusedIndex, handleStartLearning, selectedMode, users]);

  return {
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
    userToDelete: users.find((user) => user.id === deleteConfirm),
    users,
    wordGoalRank,
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
    handleCancelEdit,
  };
};
