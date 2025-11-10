'use client';

import { useState, useCallback } from 'react';
import { PersistentSidebar } from './PersistentSidebar';
import { KeyboardShortcutsHelp } from './KeyboardShortcutsHelp';
import { useRouter } from 'next/navigation';
import { useToast } from '@/hooks/use-toast';
import { useKeyboardShortcuts } from '@/hooks/use-keyboard-shortcuts';

export function LayoutWithSidebar({ children }: { children: React.ReactNode }) {
  const [currentThreadId, setCurrentThreadId] = useState<string | null>(null);
  const [isSidebarExpanded, setIsSidebarExpanded] = useState(false);
  const router = useRouter();
  const { toast } = useToast();

  // Keyboard shortcuts (automatically handles Cmd+K, Cmd+/, Esc)
  useKeyboardShortcuts({});

  const handleThreadSelect = useCallback(async (selectedThreadId: string) => {
    setCurrentThreadId(selectedThreadId);

    // Navigate to search page with threadId to load full conversation history
    // This will load all messages and allow continuing the conversation
    router.push(`/search?threadId=${selectedThreadId}`);
  }, [router]);

  const handleThreadDelete = useCallback((deletedThreadId: string) => {
    // If we're viewing the deleted thread, clear state and go home
    if (currentThreadId === deletedThreadId) {
      setCurrentThreadId(null);
      router.push('/');
    }

    toast({
      title: 'Success',
      description: 'Conversation deleted',
    });
  }, [currentThreadId, router, toast]);

  const handleNewChat = useCallback(() => {
    setCurrentThreadId(null);
    router.push('/');
  }, [router]);

  return (
    <div className="flex min-h-screen">
      <PersistentSidebar
        currentThreadId={currentThreadId}
        onThreadSelect={handleThreadSelect}
        onThreadDelete={handleThreadDelete}
        onNewChat={handleNewChat}
        onExpandChange={setIsSidebarExpanded}
      />

      {/* Main content with dynamic margin based on sidebar state */}
      <main
        className={`flex-1 transition-all duration-300 ${
          isSidebarExpanded ? 'ml-80 md:ml-80' : 'ml-16'
        }`}
      >
        {children}
      </main>

      {/* Keyboard Shortcuts Help */}
      <KeyboardShortcutsHelp />
    </div>
  );
}
