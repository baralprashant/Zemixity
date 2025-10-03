import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

interface KeyboardShortcutsOptions {
  onNewChat?: () => void;
  onToggleSidebar?: () => void;
  onEscape?: () => void;
}

export function useKeyboardShortcuts({
  onNewChat,
  onToggleSidebar,
  onEscape,
}: KeyboardShortcutsOptions) {
  const router = useRouter();

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      // Cmd/Ctrl + K: New Chat
      if ((event.metaKey || event.ctrlKey) && event.key === 'k') {
        event.preventDefault();
        if (onNewChat) {
          onNewChat();
        } else {
          router.push('/');
        }
      }

      // Cmd/Ctrl + B: Toggle Sidebar
      if ((event.metaKey || event.ctrlKey) && event.key === 'b') {
        event.preventDefault();
        if (onToggleSidebar) {
          onToggleSidebar();
        }
      }

      // Escape: Close modals/sidebar
      if (event.key === 'Escape') {
        event.preventDefault();
        if (onEscape) {
          onEscape();
        }
      }

      // Cmd/Ctrl + /: Focus search input
      if ((event.metaKey || event.ctrlKey) && event.key === '/') {
        event.preventDefault();
        const searchInput = document.querySelector('input[type="text"]') as HTMLInputElement;
        if (searchInput) {
          searchInput.focus();
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onNewChat, onToggleSidebar, onEscape, router]);
}
