'use client';

import { useState, useRef, useEffect } from 'react';
import { MoreVertical, Edit2, Trash2, Download, Share2 } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

interface ThreadMenuProps {
  onRename: () => void;
  onDelete: () => void;
  onExport?: () => void;
  onShare?: () => void;
}

export function ThreadMenu({ onRename, onDelete, onExport, onShare }: ThreadMenuProps) {
  const [isOpen, setIsOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  // Close menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen]);

  const handleRename = (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsOpen(false);
    onRename();
  };

  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsOpen(false);
    onDelete();
  };

  const handleExport = (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsOpen(false);
    onExport?.();
  };

  const handleShare = (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsOpen(false);
    onShare?.();
  };

  return (
    <div className="relative" ref={menuRef}>
      {/* Three-dot button */}
      <button
        onClick={(e) => {
          e.stopPropagation();
          setIsOpen(!isOpen);
        }}
        className="p-1.5 rounded hover:bg-gray-200 text-gray-600 transition-colors"
        title="More options"
      >
        <MoreVertical className="h-3.5 w-3.5" />
      </button>

      {/* Dropdown Menu */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: -10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: -10 }}
            transition={{ duration: 0.15 }}
            className="absolute right-0 top-8 z-50 w-48 bg-white rounded-lg shadow-lg border border-gray-200 py-1"
          >
            {/* Rename Option */}
            <button
              onClick={handleRename}
              className="w-full px-4 py-2.5 text-left text-sm text-gray-700 hover:bg-gray-100 flex items-center gap-3 transition-colors"
            >
              <Edit2 className="h-4 w-4 text-gray-600" />
              <span>Rename</span>
            </button>

            {/* Export Option */}
            {onExport && (
              <button
                onClick={handleExport}
                className="w-full px-4 py-2.5 text-left text-sm text-gray-700 hover:bg-gray-100 flex items-center gap-3 transition-colors"
              >
                <Download className="h-4 w-4 text-gray-600" />
                <span>Export</span>
              </button>
            )}

            {/* Share Option */}
            {onShare && (
              <button
                onClick={handleShare}
                className="w-full px-4 py-2.5 text-left text-sm text-gray-700 hover:bg-gray-100 flex items-center gap-3 transition-colors"
              >
                <Share2 className="h-4 w-4 text-gray-600" />
                <span>Share</span>
              </button>
            )}

            {/* Divider */}
            <div className="my-1 border-t border-gray-200"></div>

            {/* Delete Option */}
            <button
              onClick={handleDelete}
              className="w-full px-4 py-2.5 text-left text-sm text-red-600 hover:bg-red-50 flex items-center gap-3 transition-colors"
            >
              <Trash2 className="h-4 w-4 text-red-600" />
              <span>Delete</span>
            </button>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
