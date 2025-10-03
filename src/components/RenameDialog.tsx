'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Edit2 } from 'lucide-react';
import { Button } from './ui/button';

interface RenameDialogProps {
  isOpen: boolean;
  currentTitle: string;
  onClose: () => void;
  onConfirm: (newTitle: string) => void;
}

export function RenameDialog({
  isOpen,
  currentTitle,
  onClose,
  onConfirm
}: RenameDialogProps) {
  const [title, setTitle] = useState(currentTitle);

  // Update local state when currentTitle changes
  useEffect(() => {
    setTitle(currentTitle);
  }, [currentTitle]);

  const handleConfirm = () => {
    if (title.trim() && title !== currentTitle) {
      onConfirm(title.trim());
    }
    onClose();
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleConfirm();
    } else if (e.key === 'Escape') {
      onClose();
    }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/50 z-50"
          />

          {/* Dialog */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            transition={{ duration: 0.2 }}
            className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-50 bg-white rounded-2xl shadow-2xl w-full max-w-md p-6"
          >
            {/* Icon */}
            <div className="flex justify-center mb-4">
              <div className="w-12 h-12 rounded-full bg-blue-100 flex items-center justify-center">
                <Edit2 className="h-6 w-6 text-blue-600" />
              </div>
            </div>

            {/* Title */}
            <h2 className="text-xl font-semibold text-gray-900 text-center mb-2">
              Rename conversation
            </h2>

            {/* Input */}
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Enter new title..."
              autoFocus
              maxLength={100}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent mb-6"
            />

            {/* Buttons */}
            <div className="space-y-3">
              {/* Save Button */}
              <Button
                onClick={handleConfirm}
                disabled={!title.trim() || title === currentTitle}
                className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed text-white font-medium py-3 rounded-full"
              >
                Save
              </Button>

              {/* Cancel Button */}
              <Button
                onClick={onClose}
                variant="outline"
                className="w-full bg-gray-100 hover:bg-gray-200 text-gray-900 font-medium py-3 rounded-full border-0"
              >
                Cancel
              </Button>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
