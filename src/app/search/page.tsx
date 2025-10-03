'use client';

import { useEffect, useState, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useQuery, useMutation } from '@tanstack/react-query';
import { SearchResults } from '@/components/SearchResults';
import { FollowUpInput } from '@/components/FollowUpInput';
import { RelatedQuestions } from '@/components/RelatedQuestions';
import { Loader2 } from 'lucide-react';
import { TooltipProvider } from '@/components/ui/tooltip';
import { useToast } from '@/hooks/use-toast';

function SearchContent() {
  const searchParams = useSearchParams();
  const { toast } = useToast();
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [threadId, setThreadId] = useState<string | null>(null);
  const [currentResults, setCurrentResults] = useState<{
    sessionId?: string;
    threadId?: string;
    summary: string;
    sources: Array<{ title: string; url: string; snippet: string }>;
    relatedQuestions?: string[];
    conversation?: Array<{
      id: string;
      role: string;
      content: string;
      sources: Array<{ title: string; url: string; snippet: string }>;
      created_at: string;
    }>;
  } | null>(null);
  const [originalQuery, setOriginalQuery] = useState<string | null>(null);
  const [isFollowUp, setIsFollowUp] = useState(false);
  const [followUpQuery, setFollowUpQuery] = useState<string | null>(null);

  const [searchQuery, setSearchQuery] = useState(searchParams.get('q') || '');
  const [refetchCounter, setRefetchCounter] = useState(0);
  const [allSources, setAllSources] = useState<Array<{ title: string; url: string; snippet: string }>>([]);

  const { data, isLoading, error } = useQuery({
    queryKey: ['search', searchQuery, refetchCounter],
    queryFn: async () => {
      if (!searchQuery) return null;
      const response = await fetch(`/api/search?q=${encodeURIComponent(searchQuery)}`);
      if (!response.ok) throw new Error('Search failed');
      const result = await response.json();
      if (result.sessionId) {
        setSessionId(result.sessionId);
        setThreadId(result.threadId || null);
        setCurrentResults(result);
        if (!originalQuery) {
          setOriginalQuery(searchQuery);
        }
        setIsFollowUp(false);

        // Accumulate sources from all messages in conversation
        if (result.conversation && result.conversation.length > 0) {
          const newSources = result.conversation.flatMap((msg: { sources?: unknown[] }) => msg.sources || []);
          setAllSources(newSources);
        } else if (result.sources) {
          setAllSources(result.sources);
        }
      }
      return result;
    },
    enabled: !!searchQuery,
  });

  const followUpMutation = useMutation({
    mutationFn: async (followUpQuery: string) => {
      if (!sessionId) {
        const response = await fetch(`/api/search?q=${encodeURIComponent(followUpQuery)}`);
        if (!response.ok) throw new Error('Search failed');
        const result = await response.json();
        if (result.sessionId) {
          setSessionId(result.sessionId);
          setOriginalQuery(searchQuery);
          setIsFollowUp(false);
        }
        return result;
      }

      const response = await fetch('/api/follow-up', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sessionId, threadId, query: followUpQuery }),
      });

      if (!response.ok) {
        if (response.status === 404) {
          const newResponse = await fetch(`/api/search?q=${encodeURIComponent(followUpQuery)}`);
          if (!newResponse.ok) throw new Error('Search failed');
          const result = await newResponse.json();
          if (result.sessionId) {
            setSessionId(result.sessionId);
            setOriginalQuery(searchQuery);
            setIsFollowUp(false);
          }
          return result;
        }
        throw new Error('Follow-up failed');
      }

      return await response.json();
    },
    onSuccess: (result) => {
      setCurrentResults(result);
      setIsFollowUp(true);

      // Accumulate sources from all messages in conversation (don't replace, add to existing)
      if (result.conversation && result.conversation.length > 0) {
        const newSources = result.conversation.flatMap((msg: { sources?: unknown[] }) => msg.sources || []);
        setAllSources(newSources);
      } else if (result.sources) {
        setAllSources(prev => [...prev, ...result.sources]);
      }
    },
    onError: (error: Error) => {
      toast({
        variant: "destructive",
        title: "Follow-up failed",
        description: error.message || "An error occurred while processing your follow-up question.",
      });
    },
  });

  const handleFollowUp = async (newFollowUpQuery: string) => {
    setFollowUpQuery(newFollowUpQuery);
    await followUpMutation.mutateAsync(newFollowUpQuery);
  };

  const handleRetry = () => {
    if (isFollowUp && followUpQuery) {
      followUpMutation.mutate(followUpQuery);
    } else {
      setRefetchCounter(c => c + 1);
    }
  };

  useEffect(() => {
    const query = searchParams.get('q') || '';
    if (query && query !== searchQuery) {
      // Clear all state when URL changes
      setSessionId(null);
      setThreadId(null);
      setCurrentResults(null);  // Clear old results
      setOriginalQuery(null);
      setIsFollowUp(false);
      setSearchQuery(query);
      setAllSources([]);  // Clear sources for new conversation
    }
  }, [searchParams, searchQuery]);

  const displayResults = currentResults || data;

  return (
    <TooltipProvider>
      <div className="flex flex-col h-screen bg-gradient-to-b from-gray-50 to-white">
        {/* Scrollable Results Area - Two Column Layout */}
        <div className="flex-1 overflow-y-auto">
          <div className="max-w-7xl mx-auto px-4 py-6">
            <div className="flex gap-6 justify-center">
              {/* Main Content Area (Center) */}
              <div className="space-y-6 max-w-3xl w-full">
                {/* Results */}
                <SearchResults
                  results={displayResults}
                  isLoading={isLoading || followUpMutation.isPending}
                  error={error || followUpMutation.error || undefined}
                  isFollowUp={isFollowUp}
                  originalQuery={originalQuery || ''}
                  onRetry={handleRetry}
                  allSources={allSources}
                />

                {/* Related Questions */}
                {displayResults && displayResults.relatedQuestions && !isLoading && !followUpMutation.isPending && (
                  <RelatedQuestions
                    questions={displayResults.relatedQuestions}
                    onQuestionClick={(question) => {
                      handleFollowUp(question);
                    }}
                    isLoading={isLoading || followUpMutation.isPending}
                  />
                )}

                {/* Spacer to prevent content from hiding behind sticky input */}
                <div className="h-32" />
              </div>
            </div>
          </div>
        </div>

        {/* Sticky Follow-up Input */}
        {displayResults && !isLoading && !followUpMutation.isPending && (
          <div className="flex-none border-t border-gray-200 bg-white/95 backdrop-blur-sm sticky bottom-0 z-10">
            <div className="max-w-3xl mx-auto px-4 py-4">
              <FollowUpInput
                onSubmit={handleFollowUp}
                isLoading={followUpMutation.isPending}
              />
            </div>
          </div>
        )}
      </div>
    </TooltipProvider>
  );
}

function SearchLoadingFallback() {
  return (
    <div className="flex flex-col h-screen bg-gradient-to-b from-gray-50 to-white">
      <div className="flex-none border-b border-gray-200 bg-white/80 backdrop-blur-sm sticky top-0 z-10">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <div className="flex items-center justify-center gap-2">
            <Loader2 className="h-5 w-5 animate-spin text-gray-400" />
            <span className="text-sm text-gray-500">Loading search...</span>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function Search() {
  return (
    <Suspense fallback={<SearchLoadingFallback />}>
      <SearchContent />
    </Suspense>
  );
}
