/** Confirm Dialog Component */

import React from 'react';

interface ConfirmDialogProps {
  isOpen: boolean;
  title: string;
  message: string;
  confirmText: string;
  cancelText: string;
  onConfirm: () => void;
  onCancel: () => void;
  variant?: 'danger' | 'primary';
}

const ConfirmDialog: React.FC<ConfirmDialogProps> = ({
  isOpen,
  title,
  message,
  confirmText,
  cancelText,
  onConfirm,
  onCancel,
  variant = 'danger'
}) => {
  if (!isOpen) return null;

  const handleOverlayClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      onCancel();
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      onCancel();
    }
  };

  React.useEffect(() => {
    const handleGlobalKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onCancel();
      }
    };

    if (isOpen) {
      document.addEventListener('keydown', handleGlobalKeyDown);
      // Prevent body scroll when modal is open
      document.body.style.overflow = 'hidden';
    }

    return () => {
      document.removeEventListener('keydown', handleGlobalKeyDown);
      document.body.style.overflow = 'unset';
    };
  }, [isOpen, onCancel]);

  return (
    <div
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50"
      onClick={handleOverlayClick}
      onKeyDown={handleKeyDown}
      role="dialog"
      aria-modal="true"
      aria-labelledby="dialog-title"
      aria-describedby="dialog-message"
    >
      <div className="bg-gray-800 rounded-lg p-6 max-w-sm w-full shadow-xl">
        <h2
          id="dialog-title"
          className="text-lg font-semibold text-gray-100 mb-3"
        >
          {title}
        </h2>

        <p
          id="dialog-message"
          className="text-gray-400 mb-6"
        >
          {message}
        </p>

        <div className="flex gap-3">
          <button
            onClick={onCancel}
            className="flex-1 px-4 py-2 bg-gray-700 text-gray-200 rounded-lg hover:bg-gray-600 transition-colors focus:outline-none focus:ring-2 focus:ring-gray-500"
          >
            {cancelText}
          </button>

          <button
            onClick={onConfirm}
            className={`
              flex-1 px-4 py-2 rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-opacity-50
              ${variant === 'danger'
                ? 'bg-red-600 text-white hover:bg-red-700 focus:ring-red-500'
                : 'bg-primary-600 text-white hover:bg-primary-700 focus:ring-primary-500'
              }
            `}
          >
            {confirmText}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ConfirmDialog;