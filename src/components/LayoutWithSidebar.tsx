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
    try {
      const response = await fetch(`/api/threads/${selectedThreadId}`);
      if (!response.ok) throw new Error('Failed to load thread');
      const thread = await response.json();

      setCurrentThreadId(thread.id);

      // Find the first user message to set as search query
      const firstUserMessage = thread.messages.find((m: { role: string; content: string }) => m.role === 'user');

      if (firstUserMessage) {
        // Navigate to search page with the query
        router.push(`/search?q=${encodeURIComponent(firstUserMessage.content)}`);
      }
    } catch (error) {
      console.error('Error loading thread:', error);
      toast({
        title: 'Error',
        description: 'Failed to load conversation',
        variant: 'destructive',
      });
    }
  }, [router, toast]);

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
