'use client';

import { useMemo } from 'react';
import DOMPurify from 'dompurify';
import { Alert, AlertTitle, AlertDescription } from './ui/alert';
import { FocusMode } from './FocusMode';
import { ConversationMessage } from './ConversationMessage';

interface Source {
  title: string;
  url: string;
  snippet: string;
  image?: string;
  favicon?: string;
  displayUrl?: string;
  publishDate?: string;
}

interface Message {
  role: 'user' | 'assistant';
  content: string;
  sources?: Source[];
}

interface SearchResultsProps {
  content: string;
  sources: Source[];
  status: string;
  isLoading: boolean;
  error: string | null;
  conversation: Message[];
  currentQuery: string;
}

export function SearchResults({
  content,
  sources,
  status,
  isLoading,
  error,
  conversation,
}: SearchResultsProps) {
  const conversationMessages = useMemo(() => {
    return conversation.map((message, index) => (
      <ConversationMessage
        key={`${index}-${message.content.substring(0, 20)}`}
        role={message.role}
        content={renderContentWithCitations(message.content, message.sources || [])}
        sources={message.sources}
        isLast={index === conversation.length - 1}
        index={index}
      />
    ));
  }, [conversation]);

  // Show Focus Mode when loading and no content yet
  if (isLoading && !content && conversation.length === 0) {
    return (
      <div className="space-y-8">
        <FocusMode status={status} sourceCount={sources?.length || 0} />
      </div>
    );
  }

  if (error && !content && conversation.length === 0) {
    return (
      <div className="space-y-4">
        <Alert variant="destructive">
          <AlertTitle>Search failed</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      </div>
    );
  }

  if (!content && conversation.length === 0) {
    return null;
  }

  return (
    <div className="space-y-6">
      {/* Show conversation history */}
      {conversation.length > 0 && (
        <div className="bg-white border border-gray-200 rounded-2xl p-6 md:p-8">
          <div className="space-y-8">
            {conversationMessages}
          </div>

          {/* Show streaming content if actively loading */}
          {isLoading && content && (
            <div className="mt-8 pt-6 border-t border-gray-200">
              <ConversationMessage
                role="assistant"
                content={renderContentWithCitations(content, sources)}
                sources={sources}
                isLast={true}
                hideSources={true}
                isStreaming={true}
              />
              {/* Status while streaming */}
              {status && (
                <div className="mt-4 flex items-center gap-2 text-sm text-gray-500">
                  <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" />
                  <span>{status}</span>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// Helper function to render content with inline citations
function renderContentWithCitations(htmlContent: string, sources: Source[]): string {
  if (!sources || sources.length === 0) {
    // Sanitize HTML even without citations
    return DOMPurify.sanitize(htmlContent, {
      ALLOWED_TAGS: ['p', 'br', 'strong', 'em', 'ul', 'ol', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'a', 'code', 'pre', 'blockquote', 'sup'],
      ALLOWED_ATTR: ['href', 'target', 'rel', 'class', 'data-source-index', 'data-url', 'data-title', 'title'],
      ALLOW_DATA_ATTR: true
    });
  }

  // Convert [1], [2] to clickable superscripts WITHOUT inline onclick
  const citationRegex = /\[(\d+)\]/g;

  const contentWithCitations = htmlContent.replace(citationRegex, (match, num) => {
    const index = parseInt(num) - 1;
    if (index >= 0 && index < sources.length) {
      const source = sources[index];
      // Escape HTML in attributes to prevent XSS
      const escapedUrl = source.url.replace(/"/g, '&quot;').replace(/'/g, '&#39;');
      const escapedTitle = source.title.replace(/"/g, '&quot;').replace(/'/g, '&#39;');

      // Use data attributes instead of onclick - we'll handle clicks with event delegation
      return `<sup class="citation inline-flex items-center justify-center min-w-[18px] h-5 px-1.5 mx-0.5 text-xs font-semibold text-blue-600 bg-blue-50 hover:bg-blue-100 rounded cursor-pointer transition-all border border-blue-200"
        data-source-index="${index}"
        data-url="${escapedUrl}"
        data-title="${escapedTitle}"
        title="${escapedTitle}"
      >${num}</sup>`;
    }
    return match;
  });

  // Sanitize the final HTML to prevent XSS attacks
  return DOMPurify.sanitize(contentWithCitations, {
    ALLOWED_TAGS: ['p', 'br', 'strong', 'em', 'ul', 'ol', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'a', 'code', 'pre', 'blockquote', 'sup'],
    ALLOWED_ATTR: ['href', 'target', 'rel', 'class', 'data-source-index', 'data-url', 'data-title', 'title'],
    ALLOW_DATA_ATTR: true
  });
}
