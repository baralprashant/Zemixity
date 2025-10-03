'use client';

import { useState } from 'react';
import { MessageSquare, Search, Trash2, Edit2, Pin, X, Menu } from 'lucide-react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { ScrollArea } from './ui/scroll-area';
import { cn } from '@/lib/utils';

interface Thread {
  id: string;
  title: string;
  session_id: string;
  created_at: string;
  updated_at: string;
  is_pinned: boolean;
  message_count: number;
}

interface ThreadSidebarProps {
  threads: Thread[];
  currentThreadId?: string | null;
  onThreadSelect: (threadId: string) => void;
  onThreadDelete: (threadId: string) => void;
  onThreadRename?: (threadId: string, newTitle: string) => void;
  onThreadPin?: (threadId: string, pinned: boolean) => void;
  isOpen?: boolean;
  onToggle?: () => void;
}

export function ThreadSidebar({
  threads,
  currentThreadId,
  onThreadSelect,
  onThreadDelete,
  onThreadRename,
  onThreadPin,
  isOpen = true,
  onToggle
}: ThreadSidebarProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState('');

  // Filter threads by search query
  const filteredThreads = threads.filter(thread =>
    thread.title.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // Group threads by date
  const groupThreadsByDate = (threads: Thread[]) => {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);
    const lastWeek = new Date(today);
    lastWeek.setDate(lastWeek.getDate() - 7);

    const groups: { [key: string]: Thread[] } = {
      Pinned: [],
      Today: [],
      Yesterday: [],
      'Last 7 Days': [],
      Older: []
    };

    threads.forEach(thread => {
      const threadDate = new Date(thread.created_at);
      threadDate.setHours(0, 0, 0, 0);

      if (thread.is_pinned) {
        groups.Pinned.push(thread);
      } else if (threadDate.getTime() === today.getTime()) {
        groups.Today.push(thread);
      } else if (threadDate.getTime() === yesterday.getTime()) {
        groups.Yesterday.push(thread);
      } else if (threadDate >= lastWeek) {
        groups['Last 7 Days'].push(thread);
      } else {
        groups.Older.push(thread);
      }
    });

    return groups;
  };

  const groupedThreads = groupThreadsByDate(filteredThreads);

  const handleStartEdit = (thread: Thread) => {
    setEditingId(thread.id);
    setEditTitle(thread.title);
  };

  const handleSaveEdit = (threadId: string) => {
    if (editTitle.trim() && onThreadRename) {
      onThreadRename(threadId, editTitle.trim());
    }
    setEditingId(null);
  };

  const handleCancelEdit = () => {
    setEditingId(null);
    setEditTitle('');
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  if (!isOpen) {
    return (
      <button
        onClick={onToggle}
        className="fixed left-4 top-4 z-50 p-2 rounded-lg bg-white border border-gray-200 hover:bg-gray-50 transition-colors"
      >
        <Menu className="h-5 w-5" />
      </button>
    );
  }

  return (
    <div className="w-80 h-screen bg-white border-r border-gray-200 flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-gray-200 space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
            <MessageSquare className="h-5 w-5 text-[#93C572]" />
            Threads
          </h2>
          {onToggle && (
            <Button
              variant="ghost"
              size="icon"
              onClick={onToggle}
              className="h-8 w-8"
            >
              <X className="h-4 w-4" />
            </Button>
          )}
        </div>

        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
          <Input
            type="text"
            placeholder="Search threads..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9 h-9 text-sm"
          />
        </div>
      </div>

      {/* Thread List */}
      <ScrollArea className="flex-1">
        <div className="p-2">
          {Object.entries(groupedThreads).map(([group, groupThreads]) => {
            if (groupThreads.length === 0) return null;

            return (
              <div key={group} className="mb-4">
                <h3 className="px-3 py-2 text-xs font-semibold text-gray-500 uppercase">
                  {group}
                </h3>
                <div className="space-y-1">
                  {groupThreads.map((thread) => (
                    <div
                      key={thread.id}
                      className={cn(
                        "group relative rounded-lg transition-all",
                        currentThreadId === thread.id
                          ? "bg-[#93C572]/10 border border-[#93C572]/30"
                          : "hover:bg-gray-50 border border-transparent"
                      )}
                    >
                      {editingId === thread.id ? (
                        <div className="p-2 space-y-2">
                          <Input
                            value={editTitle}
                            onChange={(e) => setEditTitle(e.target.value)}
                            onKeyDown={(e) => {
                              if (e.key === 'Enter') handleSaveEdit(thread.id);
                              if (e.key === 'Escape') handleCancelEdit();
                            }}
                            className="h-8 text-sm"
                            autoFocus
                          />
                          <div className="flex gap-1">
                            <Button
                              size="sm"
                              onClick={() => handleSaveEdit(thread.id)}
                              className="h-7 text-xs flex-1"
                            >
                              Save
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={handleCancelEdit}
                              className="h-7 text-xs flex-1"
                            >
                              Cancel
                            </Button>
                          </div>
                        </div>
                      ) : (
                        <button
                          onClick={() => onThreadSelect(thread.id)}
                          className="w-full text-left p-3 rounded-lg"
                        >
                          <div className="flex items-start justify-between gap-2">
                            <div className="flex-1 min-w-0">
                              <p className="text-sm font-medium text-gray-900 line-clamp-2 mb-1">
                                {thread.title}
                              </p>
                              <div className="flex items-center gap-2 text-xs text-gray-500">
                                <span>{thread.message_count} messages</span>
                                <span>•</span>
                                <span>{formatDate(thread.created_at)}</span>
                              </div>
                            </div>

                            {thread.is_pinned && (
                              <Pin className="h-3 w-3 text-[#93C572] flex-shrink-0" />
                            )}
                          </div>

                          {/* Actions (show on hover) */}
                          <div className="flex items-center gap-1 mt-2 opacity-0 group-hover:opacity-100 transition-opacity">
                            {onThreadPin && (
                              <Button
                                size="sm"
                                variant="ghost"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  onThreadPin(thread.id, !thread.is_pinned);
                                }}
                                className="h-7 px-2 text-xs"
                              >
                                <Pin className="h-3 w-3 mr-1" />
                                {thread.is_pinned ? 'Unpin' : 'Pin'}
                              </Button>
                            )}
                            {onThreadRename && (
                              <Button
                                size="sm"
                                variant="ghost"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleStartEdit(thread);
                                }}
                                className="h-7 px-2 text-xs"
                              >
                                <Edit2 className="h-3 w-3 mr-1" />
                                Rename
                              </Button>
                            )}
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={(e) => {
                                e.stopPropagation();
                                if (confirm(`Delete "${thread.title}"?`)) {
                                  onThreadDelete(thread.id);
                                }
                              }}
                              className="h-7 px-2 text-xs text-red-600 hover:text-red-700 hover:bg-red-50"
                            >
                              <Trash2 className="h-3 w-3 mr-1" />
                              Delete
                            </Button>
                          </div>
                        </button>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            );
          })}

          {filteredThreads.length === 0 && (
            <div className="text-center py-8 text-gray-500 text-sm">
              {searchQuery ? 'No threads found' : 'No threads yet'}
            </div>
          )}
        </div>
      </ScrollArea>
    </div>
  );
}
