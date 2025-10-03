'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { AlertCircle } from 'lucide-react';
import { Button } from './ui/button';

interface DeleteConfirmDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title?: string;
  description?: string;
}

export function DeleteConfirmDialog({
  isOpen,
  onClose,
  onConfirm,
  title = 'Delete this conversation?',
  description = "You won't be able to return to this response"
}: DeleteConfirmDialogProps) {
  const handleConfirm = () => {
    onConfirm();
    onClose();
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
              <div className="w-12 h-12 rounded-full bg-gray-100 flex items-center justify-center">
                <AlertCircle className="h-6 w-6 text-gray-600" />
              </div>
            </div>

            {/* Title */}
            <h2 className="text-xl font-semibold text-gray-900 text-center mb-2">
              {title}
            </h2>

            {/* Description */}
            <p className="text-sm text-gray-600 text-center mb-6">
              {description}
            </p>

            {/* Buttons */}
            <div className="space-y-3">
              {/* Delete Button */}
              <Button
                onClick={handleConfirm}
                className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-3 rounded-full"
              >
                Delete
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
