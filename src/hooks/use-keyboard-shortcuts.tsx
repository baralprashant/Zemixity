import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

interface KeyboardShortcut {
  key: string;
  metaKey?: boolean;
  ctrlKey?: boolean;
  shiftKey?: boolean;
  action: () => void;
  description: string;
}

export interface UseKeyboardShortcutsOptions {
  onNewChat?: () => void;
}

export function useKeyboardShortcuts(options: UseKeyboardShortcutsOptions = {}) {
  const router = useRouter();

  useEffect(() => {
    const shortcuts: KeyboardShortcut[] = [
      {
        key: 'k',
        metaKey: true,
        description: 'New Chat',
        action: () => {
          if (options?.onNewChat) {
            options.onNewChat();
          } else {
            router.push('/');
          }
        },
      },
      {
        key: '/',
        metaKey: true,
        description: 'Focus Search',
        action: () => {
          const searchInput = document.querySelector('input[type="text"]') as HTMLInputElement;
          searchInput?.focus();
        },
      },
      {
        key: 'Escape',
        description: 'Close Modal/Sidebar',
        action: () => {
          // Trigger escape event for any open modals
          document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }));
        },
      },
    ];

    function handleKeyDown(event: KeyboardEvent) {
      // Don't trigger shortcuts when typing in input fields
      if (
        event.target instanceof HTMLInputElement ||
        event.target instanceof HTMLTextAreaElement
      ) {
        // Except for Escape key
        if (event.key !== 'Escape') {
          return;
        }
      }

      shortcuts.forEach((shortcut) => {
        const metaKey = shortcut.metaKey ? (event.metaKey || event.ctrlKey) : true;
        const ctrlKey = shortcut.ctrlKey ? event.ctrlKey : true;
        const shiftKey = shortcut.shiftKey ? event.shiftKey : true;

        if (
          event.key.toLowerCase() === shortcut.key.toLowerCase() &&
          metaKey &&
          ctrlKey &&
          shiftKey
        ) {
          event.preventDefault();
          shortcut.action();
        }
      });
    }

    document.addEventListener('keydown', handleKeyDown);

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [router, options]);
}

/**
 * Get all available keyboard shortcuts
 */
export function getKeyboardShortcuts() {
  const isMac = typeof window !== 'undefined' && navigator.platform.toUpperCase().indexOf('MAC') >= 0;
  const modifierKey = isMac ? '⌘' : 'Ctrl';

  return [
    { keys: [modifierKey, 'K'], description: 'New Chat' },
    { keys: [modifierKey, '/'], description: 'Focus Search' },
    { keys: ['Esc'], description: 'Close Sidebar/Modal' },
  ];
}
