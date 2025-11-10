'use client';

import { useState } from 'react';
import { ChevronLeft, MoreVertical, MessageSquare, Clock, Edit3 } from 'lucide-react';
import { ScrollArea } from './ui/scroll-area';
import { motion, AnimatePresence } from 'framer-motion';
import { cn } from '@/lib/utils';
import { useRouter } from 'next/navigation';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { PistachioStar } from './PistachioStar';
import { ThreadMenu } from './ThreadMenu';
import { DeleteConfirmDialog } from './DeleteConfirmDialog';
import { RenameDialog } from './RenameDialog';
import { exportConversationAsHTML, shareThread } from '@/lib/export';
import { useToast } from '@/hooks/use-toast';

interface Thread {
  id: string;
  title: string;
  session_id: string;
  created_at: string;
  updated_at: string;
  is_pinned: boolean;
  message_count: number;
}

interface PersistentSidebarProps {
  currentThreadId?: string | null;
  onThreadSelect?: (threadId: string) => void;
  onThreadDelete?: (threadId: string) => void;
  onNewChat?: () => void;
  onExpandChange?: (expanded: boolean) => void;
}

export function PersistentSidebar({
  currentThreadId,
  onThreadSelect,
  onThreadDelete,
  onNewChat,
  onExpandChange
}: PersistentSidebarProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  // Notify parent when sidebar expands/collapses
  const handleExpandChange = (expanded: boolean) => {
    setIsExpanded(expanded);
    if (onExpandChange) {
      onExpandChange(expanded);
    }
  };
  const [showAllThreads, setShowAllThreads] = useState(false);
  const [hoveredThreadId, setHoveredThreadId] = useState<string | null>(null);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [threadToDelete, setThreadToDelete] = useState<string | null>(null);
  const [renameDialogOpen, setRenameDialogOpen] = useState(false);
  const [threadToRename, setThreadToRename] = useState<{ id: string; title: string } | null>(null);
  const router = useRouter();
  const queryClient = useQueryClient();
  const { toast } = useToast();

  // Fetch threads
  const { data: threads = [] } = useQuery<Thread[]>({
    queryKey: ['threads'],
    queryFn: async () => {
      const response = await fetch('/api/threads');
      if (!response.ok) throw new Error('Failed to fetch threads');
      return response.json();
    },
  });

  const handleNewChat = () => {
    if (onNewChat) {
      onNewChat();
    }
    router.push('/');
  };

  const handleThreadClick = (threadId: string) => {
    if (onThreadSelect) {
      onThreadSelect(threadId);
    }
  };

  const handleDeleteClick = (threadId: string) => {
    setThreadToDelete(threadId);
    setDeleteDialogOpen(true);
  };

  const handleDeleteConfirm = async () => {
    if (!threadToDelete) return;

    try {
      const response = await fetch(`/api/threads/${threadToDelete}`, {
        method: 'DELETE',
      });
      if (!response.ok) throw new Error('Failed to delete thread');

      // Invalidate queries to refetch
      queryClient.invalidateQueries({ queryKey: ['threads'] });

      if (onThreadDelete) {
        onThreadDelete(threadToDelete);
      }

      setThreadToDelete(null);
    } catch (error) {
      if (process.env.NODE_ENV === 'development') {
        console.error('Error deleting thread:', error);
      }
      toast({
        variant: "destructive",
        title: "Failed to delete thread",
        description: "Please try again later.",
      });
    }
  };

  const handleRenameClick = (threadId: string) => {
    const thread = threads.find(t => t.id === threadId);
    if (thread) {
      setThreadToRename({ id: thread.id, title: thread.title });
      setRenameDialogOpen(true);
    }
  };

  const handleRenameConfirm = async (newTitle: string) => {
    if (!threadToRename) return;

    try {
      const response = await fetch(`/api/threads/${threadToRename.id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: newTitle }),
      });

      if (!response.ok) throw new Error('Failed to rename thread');

      // Invalidate queries to refetch
      queryClient.invalidateQueries({ queryKey: ['threads'] });

      setThreadToRename(null);
    } catch (error) {
      if (process.env.NODE_ENV === 'development') {
        console.error('Error renaming thread:', error);
      }
      toast({
        variant: "destructive",
        title: "Failed to rename thread",
        description: "Please try again later.",
      });
    }
  };

  const handleExportClick = async (threadId: string) => {
    const thread = threads.find(t => t.id === threadId);
    if (!thread) return;

    const success = await exportConversationAsHTML(threadId, thread.title);
    if (success) {
      toast({
        title: "Export successful",
        description: "Conversation downloaded as HTML",
      });
    } else {
      toast({
        title: "Export failed",
        description: "Could not export conversation",
        variant: "destructive",
      });
    }
  };

  const handleShareClick = async (threadId: string) => {
    const shareUrl = await shareThread(threadId);
    if (shareUrl) {
      navigator.clipboard.writeText(shareUrl);
      toast({
        title: "Link copied",
        description: "Share link copied to clipboard",
      });
    } else {
      toast({
        title: "Share failed",
        description: "Could not create share link",
        variant: "destructive",
      });
    }
  };

  // Show first 10 threads or all
  const visibleThreads = showAllThreads ? threads : threads.slice(0, 10);
  const hasMoreThreads = threads.length > 10;

  return (
    <>
      {/* Collapsed Sidebar - Icon Only */}
      <AnimatePresence>
        {!isExpanded && (
          <motion.div
            initial={{ x: -80 }}
            animate={{ x: 0 }}
            exit={{ x: -80 }}
            transition={{ type: 'spring', damping: 25, stiffness: 200 }}
            className="fixed left-0 top-0 bottom-0 z-40 w-16 bg-white border-r border-gray-200 flex flex-col items-center py-4 gap-4"
          >
            {/* Pistachio Star Icon */}
            <button
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              onClick={() => router.push('/')}
            >
              <PistachioStar size={32} />
            </button>

            {/* New Chat Icon */}
            <button
              onClick={handleNewChat}
              className="p-3 hover:bg-gray-100 rounded-lg transition-colors group relative"
              title="New Chat"
            >
              <Edit3 className="h-5 w-5 text-gray-700" />
            </button>

            {/* History Icon - Opens Sidebar */}
            <button
              onClick={() => handleExpandChange(true)}
              className="p-3 hover:bg-gray-100 rounded-lg transition-colors group relative"
              title="History"
            >
              <Clock className="h-5 w-5 text-gray-700" />
            </button>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Expanded Sidebar */}
      <AnimatePresence>
        {isExpanded && (
          <>
            {/* Overlay for mobile */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="fixed inset-0 bg-black/50 z-30 md:hidden"
              onClick={() => handleExpandChange(false)}
            />

            {/* Sidebar */}
            <motion.aside
              initial={{ x: -320 }}
              animate={{ x: 0 }}
              exit={{ x: -320 }}
              transition={{ type: 'spring', damping: 25, stiffness: 200 }}
              className={cn(
                'fixed left-0 top-0 bottom-0 z-40',
                'w-80 bg-white border-r border-gray-200',
                'flex flex-col shadow-xl'
              )}
            >
              {/* Header Row - Aligned with History Icon */}
              <div className="pt-4 px-3 pb-3 border-b border-gray-200">
                <div className="flex items-center justify-between mb-3">
                  {/* Back Button - Aligned with History Icon (py-4 + gap-4 + p-2 + p-3 = ~88px from top) */}
                  <button
                    onClick={() => handleExpandChange(false)}
                    className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                    title="Collapse sidebar"
                  >
                    <ChevronLeft className="h-5 w-5 text-gray-700" />
                  </button>

                  {/* New Chat Icon */}
                  <button
                    onClick={handleNewChat}
                    className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                    title="New Chat"
                  >
                    <Edit3 className="h-5 w-5 text-gray-700" />
                  </button>

                  {/* Three Dots Menu */}
                  <button
                    className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                    title="More options"
                  >
                    <MoreVertical className="h-5 w-5 text-gray-700" />
                  </button>
                </div>

                {/* Past conversations label */}
                <h2 className="text-sm font-semibold text-gray-900 px-2">
                  Past conversations
                </h2>
              </div>

              {/* Threads List */}
              <ScrollArea className="flex-1 px-2 py-2">
                <div className="space-y-0.5">
                  {threads.length === 0 ? (
                    <div className="text-center py-8 px-4">
                      <MessageSquare className="h-12 w-12 text-gray-300 mx-auto mb-3" />
                      <p className="text-sm text-gray-500">No conversations yet</p>
                      <p className="text-xs text-gray-400 mt-1">Start a new chat to begin</p>
                    </div>
                  ) : (
                    <>
                      {visibleThreads.map((thread) => (
                        <div
                          key={thread.id}
                          onClick={() => handleThreadClick(thread.id)}
                          onMouseEnter={() => setHoveredThreadId(thread.id)}
                          onMouseLeave={() => setHoveredThreadId(null)}
                          className={cn(
                            'group flex items-center gap-3 px-3 py-2.5 rounded-lg cursor-pointer transition-all relative',
                            currentThreadId === thread.id
                              ? 'bg-gray-100'
                              : hoveredThreadId === thread.id
                              ? 'bg-gray-100'
                              : 'bg-transparent'
                          )}
                        >
                          {/* Content */}
                          <div className="flex-1 min-w-0">
                            <p className={cn(
                              'text-sm font-normal truncate',
                              currentThreadId === thread.id ? 'text-gray-900' : 'text-gray-700'
                            )}>
                              {thread.title}
                            </p>
                          </div>

                          {/* Three-Dot Menu - Only show on hover */}
                          {hoveredThreadId === thread.id && (
                            <ThreadMenu
                              onRename={() => handleRenameClick(thread.id)}
                              onDelete={() => handleDeleteClick(thread.id)}
                              onExport={() => handleExportClick(thread.id)}
                              onShare={() => handleShareClick(thread.id)}
                            />
                          )}
                        </div>
                      ))}

                      {/* See More Button */}
                      {hasMoreThreads && !showAllThreads && (
                        <button
                          onClick={() => setShowAllThreads(true)}
                          className="w-full px-3 py-2.5 text-sm text-gray-600 hover:bg-gray-100 rounded-lg transition-colors text-left flex items-center gap-2"
                        >
                          <span>See more</span>
                          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                          </svg>
                        </button>
                      )}
                    </>
                  )}
                </div>
              </ScrollArea>
            </motion.aside>
          </>
        )}
      </AnimatePresence>

      {/* Delete Confirmation Dialog */}
      <DeleteConfirmDialog
        isOpen={deleteDialogOpen}
        onClose={() => {
          setDeleteDialogOpen(false);
          setThreadToDelete(null);
        }}
        onConfirm={handleDeleteConfirm}
      />

      {/* Rename Dialog */}
      <RenameDialog
        isOpen={renameDialogOpen}
        currentTitle={threadToRename?.title || ''}
        onClose={() => {
          setRenameDialogOpen(false);
          setThreadToRename(null);
        }}
        onConfirm={handleRenameConfirm}
      />
    </>
  );
}
