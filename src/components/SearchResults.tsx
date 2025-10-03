'use client';

import { RefreshCw } from 'lucide-react';
import { Logo } from './Logo';
import { Skeleton } from './ui/skeleton';
import { Alert, AlertTitle, AlertDescription } from './ui/alert';
import { Button } from './ui/button';
import { ConversationMessage } from './ConversationMessage';
import { TypingIndicator } from './TypingIndicator';
import { useEffect, useRef } from 'react';

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
  id: string;
  role: 'user' | 'assistant';
  content: string;
  sources: Source[];
  created_at: string;
}

interface SearchResultsProps {
  results: {
    summary: string;
    sources: Source[];
    conversation?: Message[];
  } | null;
  isLoading: boolean;
  error?: Error | null;
  isFollowUp?: boolean;
  originalQuery?: string;
  onRetry?: () => void;
  allSources?: Source[];
}

export function SearchResults({
  results,
  isLoading,
  error,
  isFollowUp = false,
  originalQuery = '',
  onRetry,
  allSources = [],
}: SearchResultsProps) {
  const conversationEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (results?.conversation && results.conversation.length > 0) {
      conversationEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [results?.conversation]);

  if (isLoading) {
    return (
      <div className="space-y-8">
        {/* Skeleton for main answer */}
        <div className="bg-white border border-gray-200 rounded-2xl p-6 md:p-8">
          <Skeleton className="h-8 w-32 mb-4" />
          <div className="space-y-3">
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-3/4" />
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-5/6" />
          </div>
        </div>

        {/* Typing Indicator */}
        <div className="space-y-4">
          <TypingIndicator />
          <div className="flex flex-col items-center justify-center py-4">
            <Logo size={48} isLoading={true} />
            <p className="text-sm text-gray-500 mt-2">
              {isFollowUp ? 'Thinking...' : 'Searching...'}
            </p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-4">
        <Alert variant="destructive">
          <AlertTitle>Search failed</AlertTitle>
          <AlertDescription>
            {error.message || 'An error occurred while processing your search'}
          </AlertDescription>
        </Alert>
        {onRetry && (
          <div className="flex justify-center">
            <Button
              onClick={onRetry}
              variant="outline"
              className="gap-2"
            >
              <RefreshCw className="w-4 h-4" />
              Try Again
            </Button>
          </div>
        )}
      </div>
    );
  }

  if (!results) {
    return null;
  }

  // Use conversation array if available, otherwise fall back to single result
  const hasConversation = results.conversation && results.conversation.length > 0;

  return (
    <div className="flex gap-6">
      {/* Main Conversation Area */}
      <div className="flex-1 space-y-8">
        {hasConversation ? (
          // Display full conversation history
          <div className="bg-white border border-gray-200 rounded-2xl p-6 md:p-8">
            <div className="space-y-8">
              {results.conversation!.map((message, index) => (
                <ConversationMessage
                  key={message.id}
                  role={message.role}
                  content={message.content}
                  sources={[]}
                  isLast={index === results.conversation!.length - 1}
                  index={index}
                  hideSources={true}
                />
              ))}
            </div>
            {/* Invisible div for auto-scroll */}
            <div ref={conversationEndRef} />
          </div>
        ) : (
          // Fallback to old single-result display
          <div className="bg-white border border-gray-200 rounded-2xl p-6 md:p-8">
            <div className="mb-4">
              <h2 className="text-xl md:text-2xl font-semibold text-gray-900">
                {isFollowUp && originalQuery ? 'Follow-up' : 'Answer'}
              </h2>
            </div>

            {/* Response Content */}
            <div
              className="prose prose-gray max-w-none
                prose-headings:font-semibold
                prose-h2:text-xl prose-h2:mt-6 prose-h2:mb-3
                prose-h3:text-lg prose-h3:mt-4 prose-h3:mb-2
                prose-p:text-gray-700
                prose-p:leading-relaxed
                prose-a:text-blue-600
                prose-a:no-underline hover:prose-a:underline
                prose-ul:my-4 prose-li:my-1
              "
              dangerouslySetInnerHTML={{ __html: results.summary }}
            />
          </div>
        )}
      </div>

      {/* Sources Panel (Right) - Show only first 3-4 sources initially */}
      {allSources.length > 0 && (
        <div className="hidden lg:block w-80 flex-shrink-0">
          <div className="sticky top-6">
            <div className="bg-white border border-gray-200 rounded-2xl overflow-hidden shadow-sm">
              <div className="px-4 py-3 border-b border-gray-200 bg-gray-50/50">
                <h3 className="text-sm font-semibold text-gray-900">
                  {allSources.length} {allSources.length === 1 ? 'Source' : 'Sources'}
                </h3>
              </div>
              <div className="overflow-y-auto max-h-[calc(100vh-12rem)] p-3 space-y-3">
                {allSources.slice(0, 4).map((source, index) => (
                  <SourceCard key={index} source={source} index={index} />
                ))}
                {allSources.length > 4 && (
                  <div className="space-y-3 border-t border-gray-100 pt-3">
                    {allSources.slice(4).map((source, index) => (
                      <SourceCard key={index + 4} source={source} index={index + 4} />
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// Source Card Component
function SourceCard({ source, index }: { source: Source; index: number }) {
  return (
    <a
      href={source.url}
      target="_blank"
      rel="noopener noreferrer"
      className="block group"
    >
      <div className="border border-gray-200 rounded-lg overflow-hidden hover:border-[#93C572] hover:shadow-md transition-all duration-200">
        {/* Thumbnail Image */}
        {source.image && (
          <div className="relative w-full h-32 bg-gray-100 overflow-hidden">
            <img
              src={source.image}
              alt={source.title}
              className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-200"
              onError={(e) => {
                const target = e.target as HTMLElement;
                target.style.display = 'none';
              }}
            />
          </div>
        )}

        {/* Content */}
        <div className="p-3 space-y-2">
          {/* Number Badge and URL */}
          <div className="flex items-center gap-2">
            <div className="flex-shrink-0 w-5 h-5 bg-gray-100 rounded flex items-center justify-center text-xs font-medium text-gray-600 group-hover:bg-[#93C572] group-hover:text-white transition-colors">
              {index + 1}
            </div>
            <span className="text-xs text-gray-500 truncate">
              {source.displayUrl || new URL(source.url).hostname.replace('www.', '')}
            </span>
          </div>

          {/* Title */}
          <h4 className="font-medium text-sm text-gray-900 line-clamp-2 group-hover:text-[#93C572] transition-colors leading-snug">
            {source.title}
          </h4>

          {/* Snippet */}
          {source.snippet && (
            <p className="text-xs text-gray-600 line-clamp-2 leading-relaxed">
              {source.snippet}
            </p>
          )}
        </div>
      </div>
    </a>
  );
}
