'use client';

import { useState } from 'react';
import { Keyboard, X } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export function KeyboardShortcutsHelp() {
  const [isOpen, setIsOpen] = useState(false);

  const shortcuts = [
    { keys: ['⌘', 'K'], description: 'New Chat' },
    { keys: ['⌘', '/'], description: 'Focus Search' },
    { keys: ['Esc'], description: 'Close Sidebar/Modal' },
  ];

  return (
    <>
      {/* Help Button */}
      <button
        onClick={() => setIsOpen(true)}
        className="fixed bottom-4 right-4 p-3 bg-white border border-gray-200 rounded-full shadow-lg hover:shadow-xl transition-shadow z-40"
        title="Keyboard Shortcuts"
      >
        <Keyboard className="h-5 w-5 text-gray-600" />
      </button>

      {/* Modal */}
      <AnimatePresence>
        {isOpen && (
          <>
            {/* Overlay */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setIsOpen(false)}
              className="fixed inset-0 bg-black/50 z-50"
            />

            {/* Modal Content */}
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              transition={{ duration: 0.2 }}
              className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-50 bg-white rounded-2xl shadow-2xl w-full max-w-md p-6"
            >
              {/* Header */}
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-2">
                  <Keyboard className="h-5 w-5 text-gray-700" />
                  <h2 className="text-xl font-semibold text-gray-900">
                    Keyboard Shortcuts
                  </h2>
                </div>
                <button
                  onClick={() => setIsOpen(false)}
                  className="p-1 hover:bg-gray-100 rounded transition-colors"
                >
                  <X className="h-5 w-5 text-gray-500" />
                </button>
              </div>

              {/* Shortcuts List */}
              <div className="space-y-3">
                {shortcuts.map((shortcut, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between py-3 border-b border-gray-100 last:border-0"
                  >
                    <span className="text-gray-700">{shortcut.description}</span>
                    <div className="flex items-center gap-1">
                      {shortcut.keys.map((key, keyIndex) => (
                        <span key={keyIndex} className="flex items-center gap-1">
                          <kbd className="px-2 py-1 text-xs font-semibold text-gray-800 bg-gray-100 border border-gray-300 rounded">
                            {key}
                          </kbd>
                          {keyIndex < shortcut.keys.length - 1 && (
                            <span className="text-gray-400">+</span>
                          )}
                        </span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>

              {/* Footer */}
              <div className="mt-6 text-center">
                <p className="text-xs text-gray-500">
                  Use <kbd className="px-1 py-0.5 text-xs bg-gray-100 border border-gray-300 rounded">⌘</kbd> on Mac or <kbd className="px-1 py-0.5 text-xs bg-gray-100 border border-gray-300 rounded">Ctrl</kbd> on Windows/Linux
                </p>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </>
  );
}
