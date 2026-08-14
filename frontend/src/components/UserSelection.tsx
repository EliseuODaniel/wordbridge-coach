/** User Selection Component */

import React from 'react';
import ProfileCard from './ProfileCard';
import ConfirmDialog from './ConfirmDialog';
import UserProfileCreateForm from './UserProfileCreateForm';
import UserProfileEditModal from './UserProfileEditModal';
import { useUserSelection } from './useUserSelection';
import AppBrand from './AppBrand';
import ModePicker from './ModePicker';
import type { TrainingMode } from './trainingModes';
import InfoTooltip from './InfoTooltip';

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
    errorMessage,
    editingUser,
    focusedIndex,
    loading,
    profilesLoading,
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
    setErrorMessage,
    setNativeLanguage,
    setNewUsername,
    setTargetLanguage,
    setWordGoalRank,
  } = useUserSelection(selectedMode, onModeSelect, onUserSelected);

  return (
    <main className="app-frame" onKeyDown={handleKeyDown}>
      <div className="page-grid pointer-events-none fixed inset-0" aria-hidden="true" />
      <div className="relative mx-auto grid min-h-screen max-w-7xl items-start gap-8 px-4 py-6 sm:px-6 sm:py-10 lg:grid-cols-[0.86fr_1.14fr] lg:items-center lg:gap-14 lg:px-8">
        <section className="pt-2 lg:sticky lg:top-6 lg:py-6">
          <AppBrand compact />
          <p className="eyebrow mt-8">Aprendizado adaptativo</p>
          <h1 className="mt-3 max-w-xl font-display text-4xl font-semibold leading-[1.08] tracking-[-0.045em] text-white lg:text-5xl">
            Faça cada palavra encontrar o seu lugar.
          </h1>
          <p className="mt-4 max-w-lg text-sm leading-6 text-gray-300 sm:text-base">
            Vocabulário, contexto e conversação em uma experiência local que se adapta ao que você já sabe — e ao que precisa rever agora.
          </p>

          <div className="mt-6">
            <div className="mb-3 flex items-center justify-between gap-3">
              <span className="text-sm font-semibold text-gray-200">Como você quer praticar?</span>
              <span className="status-pill">modo atual</span>
            </div>
            <ModePicker selectedMode={selectedMode} onModeSelect={onModeSelect} />
          </div>

          <div className="mt-5 flex flex-wrap items-center gap-2 text-xs text-gray-400">
            <span className="status-pill">Local e privado</span>
            <span className="status-pill">Ritmo adaptativo</span>
            <span className="status-pill">Texto, voz e chat</span>
            <InfoTooltip label="Sobre a experiência local" align="left">
              O treino e o progresso ficam no ambiente local configurado. A prática de fala não envia nem persiste o áudio.
            </InfoTooltip>
          </div>
        </section>

        <section className="surface-panel overflow-hidden" aria-labelledby="profiles-heading">
          <div className="border-b border-white/[0.07] px-5 py-5 sm:px-7 sm:py-6">
            <p className="eyebrow">Seu espaço</p>
            <div className="mt-2 flex items-end justify-between gap-4">
              <div>
                <h2 id="profiles-heading" className="text-2xl font-semibold tracking-[-0.03em] text-white">
                  Escolha seu perfil
                </h2>
                <p className="mt-1 text-sm text-gray-400">Continue de onde parou ou comece uma nova jornada.</p>
              </div>
              {users.length > 0 && <span className="status-pill">{users.length} {users.length === 1 ? 'perfil' : 'perfis'}</span>}
            </div>
          </div>

          <div className="p-5 sm:p-7">
            {errorMessage && (
              <div className="mb-5 rounded-2xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-100" role="alert" data-testid="profile-create-error">
                {errorMessage}
              </div>
            )}

            {profilesLoading ? (
              <div className="mb-7 space-y-3" aria-label="Carregando perfis">
                {[0, 1].map((item) => <div key={item} className="h-28 animate-pulse rounded-2xl border border-white/[0.06] bg-white/[0.03]" />)}
              </div>
            ) : users.length > 0 ? (
              <div className="mb-8">
                <p className="mb-3 text-xs font-semibold uppercase tracking-[0.16em] text-gray-500">Continuar estudando</p>
                <div className="max-h-[23rem] space-y-3 overflow-y-auto pr-1">
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
            ) : null}

            <div className={users.length > 0 ? 'border-t border-white/[0.07] pt-7' : ''}>
              <div className="mb-5">
                <p className="eyebrow">Novo perfil</p>
                <h3 className="mt-1 text-lg font-semibold text-white">Prepare seu plano de estudo</h3>
              </div>
              <UserProfileCreateForm
                loading={loading}
                nativeLanguage={nativeLanguage}
                newUsername={newUsername}
                targetLanguage={targetLanguage}
                wordGoalRank={wordGoalRank}
                onNativeLanguageChange={setNativeLanguage}
                onSubmit={handleCreateUser}
                onTargetLanguageChange={setTargetLanguage}
                onUsernameChange={(value) => {
                  setErrorMessage(null);
                  setNewUsername(value);
                }}
                onWordGoalRankChange={setWordGoalRank}
              />
            </div>

            <p className="mt-6 text-center text-xs text-gray-500">
              Seu progresso permanece neste ambiente local.
            </p>
          </div>
        </section>

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

        {deleteConfirm && userToDelete && (
          <ConfirmDialog
            isOpen={!!deleteConfirm}
            title="Excluir este perfil?"
            message={`Todo o progresso local de “${userToDelete.username}” será removido. Esta ação não pode ser desfeita.`}
            confirmText="Excluir perfil"
            cancelText="Cancelar"
            onConfirm={() => handleConfirmDelete(deleteConfirm)}
            onCancel={() => setDeleteConfirm(null)}
            variant="danger"
          />
        )}
      </div>
    </main>
  );
};

export default UserSelection;
