'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { Search, FileText, Sparkles, CheckCircle, Loader2 } from 'lucide-react';
import { Logo } from './Logo';

interface FocusModeProps {
  status: string;
  sourceCount?: number;
}

interface Stage {
  id: string;
  label: string;
  icon: typeof Search;
  keywords: string[]; // Keywords to match against status
}

const stages: Stage[] = [
  {
    id: 'searching',
    label: 'Searching the web',
    icon: Search,
    keywords: ['searching', 'search', 'connecting'],
  },
  {
    id: 'reading',
    label: 'Reading sources',
    icon: FileText,
    keywords: ['reading', 'fetching', 'sources', 'analyzing'],
  },
  {
    id: 'generating',
    label: 'Generating answer',
    icon: Sparkles,
    keywords: ['generating', 'thinking', 'writing', 'suggestions'],
  },
];

function getStageFromStatus(status: string): number {
  if (!status) return -1;

  const statusLower = status.toLowerCase();

  // Check each stage's keywords
  for (let i = 0; i < stages.length; i++) {
    if (stages[i].keywords.some(keyword => statusLower.includes(keyword))) {
      return i;
    }
  }

  // Default to first stage if status exists but doesn't match
  return 0;
}

export function FocusMode({ status, sourceCount = 0 }: FocusModeProps) {
  const currentStageIndex = getStageFromStatus(status);
  const isComplete = !status;

  return (
    <div className="flex flex-col items-center justify-center py-12 px-4">
      {/* Logo with loading animation */}
      <motion.div
        initial={{ scale: 0.8, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ duration: 0.3 }}
        className="mb-8"
      >
        <Logo size={56} isLoading={!isComplete} />
      </motion.div>

      {/* Stage indicators */}
      <div className="flex items-center gap-3 mb-6">
        {stages.map((stage, index) => {
          const Icon = stage.icon;
          const isActive = index === currentStageIndex;
          const isDone = index < currentStageIndex || isComplete;

          return (
            <div key={stage.id} className="flex items-center gap-3">
              {/* Stage icon */}
              <motion.div
                initial={{ scale: 0.8, opacity: 0 }}
                animate={{
                  scale: isActive ? [1, 1.1, 1] : 1,
                  opacity: 1,
                }}
                transition={{
                  scale: {
                    duration: 1.5,
                    repeat: isActive ? Infinity : 0,
                    ease: 'easeInOut',
                  },
                  opacity: { duration: 0.3 },
                }}
                className="flex flex-col items-center gap-2"
              >
                {/* Icon container */}
                <div
                  className={`relative p-3 rounded-full transition-all duration-300 ${
                    isDone
                      ? 'bg-green-100 dark:bg-green-900/30'
                      : isActive
                      ? 'bg-blue-100 dark:bg-blue-900/30'
                      : 'bg-gray-100 dark:bg-gray-800'
                  }`}
                >
                  {isDone ? (
                    <CheckCircle className="w-6 h-6 text-green-600 dark:text-green-400" />
                  ) : isActive ? (
                    <Icon className="w-6 h-6 text-blue-600 dark:text-blue-400" />
                  ) : (
                    <Icon className="w-6 h-6 text-gray-400 dark:text-gray-600" />
                  )}

                  {/* Pulsing ring for active stage */}
                  {isActive && !isDone && (
                    <motion.div
                      className="absolute inset-0 rounded-full border-2 border-blue-400"
                      initial={{ scale: 1, opacity: 0.5 }}
                      animate={{ scale: 1.5, opacity: 0 }}
                      transition={{
                        duration: 1.5,
                        repeat: Infinity,
                        ease: 'easeOut',
                      }}
                    />
                  )}
                </div>

                {/* Stage label */}
                <motion.span
                  initial={{ opacity: 0, y: 5 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className={`text-xs sm:text-sm font-medium whitespace-nowrap transition-colors duration-300 ${
                    isDone
                      ? 'text-green-600 dark:text-green-400'
                      : isActive
                      ? 'text-blue-600 dark:text-blue-400'
                      : 'text-gray-500 dark:text-gray-400'
                  }`}
                >
                  {stage.label}
                </motion.span>
              </motion.div>

              {/* Connector line */}
              {index < stages.length - 1 && (
                <div className="relative h-0.5 w-12 sm:w-16 bg-gray-200 dark:bg-gray-700">
                  <motion.div
                    className={`absolute inset-0 ${
                      isDone
                        ? 'bg-green-400 dark:bg-green-500'
                        : 'bg-gray-300 dark:bg-gray-600'
                    }`}
                    initial={{ scaleX: 0 }}
                    animate={{ scaleX: isDone ? 1 : 0 }}
                    transition={{ duration: 0.5, delay: index * 0.2 }}
                    style={{ transformOrigin: 'left' }}
                  />
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Status text with animation */}
      <AnimatePresence mode="wait">
        {status && (
          <motion.div
            key={status}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.3 }}
            className="flex items-center gap-2 mt-4"
          >
            <Loader2 className="w-4 h-4 text-blue-600 dark:text-blue-400 animate-spin" />
            <p className="text-sm text-gray-600 dark:text-gray-300 font-medium">
              {status}
            </p>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Source count indicator */}
      <AnimatePresence>
        {sourceCount > 0 && currentStageIndex === 1 && (
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.8 }}
            transition={{ duration: 0.3 }}
            className="mt-4 px-4 py-2 bg-blue-50 dark:bg-blue-900/20 rounded-full border border-blue-200 dark:border-blue-800"
          >
            <p className="text-sm text-blue-700 dark:text-blue-300 font-medium">
              Found {sourceCount} {sourceCount === 1 ? 'source' : 'sources'}
            </p>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Progress dots (alternative visual) */}
      <div className="flex gap-2 mt-6">
        {stages.map((_, index) => (
          <motion.div
            key={index}
            className={`h-1.5 rounded-full transition-all duration-300 ${
              index === currentStageIndex
                ? 'w-8 bg-blue-500 dark:bg-blue-400'
                : index < currentStageIndex || isComplete
                ? 'w-1.5 bg-green-500 dark:bg-green-400'
                : 'w-1.5 bg-gray-300 dark:bg-gray-600'
            }`}
            initial={{ scaleX: 0 }}
            animate={{ scaleX: 1 }}
            transition={{ delay: index * 0.1 }}
          />
        ))}
      </div>
    </div>
  );
}
