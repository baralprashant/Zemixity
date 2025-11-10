'use client';

import { useEffect, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import { SearchResults } from '@/components/SearchResults';
import { FollowUpInput } from '@/components/FollowUpInput';
import { RelatedQuestions } from '@/components/RelatedQuestions';
import { Loader2 } from 'lucide-react';
import { TooltipProvider } from '@/components/ui/tooltip';
import { useToast } from '@/hooks/use-toast';
import { useStreamingSearch } from '@/hooks/useStreamingSearch';

function SearchContent() {
  const searchParams = useSearchParams();
  const { toast } = useToast();
  const {
    search,
    followUp,
    loadThread,
    content,
    sources,
    relatedQuestions,
    status,
    isLoading,
    error,
    reset,
    conversation,
    currentQuery
  } = useStreamingSearch();

  // Perform search when query param changes or load thread history
  useEffect(() => {
    const query = searchParams.get('q');
    const threadId = searchParams.get('threadId');
    const hasFile = searchParams.get('hasFile');

    // If threadId is provided, load the conversation history
    if (threadId) {
      // Load thread conversation from API
      fetch(`/api/threads/${threadId}`)
        .then(res => {
          if (!res.ok) throw new Error('Failed to load thread');
          return res.json();
        })
        .then(thread => {
          // Thread data contains: id, session_id, messages[]
          // Load the conversation into the streaming hook without triggering new search
          reset(); // Clear any previous state
          loadThread({
            id: thread.id,
            session_id: thread.session_id,
            messages: thread.messages
          });
        })
        .catch(error => {
          console.error('Error loading thread:', error);
          toast({
            variant: "destructive",
            title: "Failed to load conversation",
            description: "Please try again",
          });
        });
      return;
    }

    // Normal search flow
    if (query) {
      reset(); // Clear previous results

      // Check if there's a file upload
      if (hasFile === 'true') {
        const fileData = sessionStorage.getItem('uploadedFileData');
        const fileInfo = sessionStorage.getItem('uploadedFile');

        if (fileData && fileInfo) {
          // Convert data URL back to File
          const info = JSON.parse(fileInfo);
          fetch(fileData)
            .then(res => res.blob())
            .then(blob => {
              const file = new File([blob], info.name, { type: info.type });
              search(query, file);

              // Clean up sessionStorage
              sessionStorage.removeItem('uploadedFileData');
              sessionStorage.removeItem('uploadedFile');
            });
        } else {
          search(query);
        }
      } else {
        search(query);
      }
    }
  }, [searchParams, search, reset, loadThread, toast]);

  // Show error toast if search fails
  useEffect(() => {
    if (error) {
      toast({
        variant: "destructive",
        title: "Search failed",
        description: error,
      });
    }
  }, [error, toast]);

  const handleFollowUp = async (query: string) => {
    await followUp(query);
  };

  return (
    <TooltipProvider>
      <div className="flex flex-col h-screen bg-gradient-to-b from-gray-50 to-white">
        {/* Scrollable Results Area */}
        <div className="flex-1 overflow-y-auto">
          <div className="max-w-7xl mx-auto px-4 py-6">
            <div className="flex gap-6 justify-center">
              {/* Main Content Area */}
              <div className="space-y-6 max-w-5xl w-full">
                {/* Results */}
                <SearchResults
                  content={content}
                  sources={sources}
                  status={status}
                  isLoading={isLoading}
                  error={error}
                  conversation={conversation}
                  currentQuery={currentQuery}
                />

                {/* Related Questions */}
                {relatedQuestions && relatedQuestions.length > 0 && !isLoading && (
                  <RelatedQuestions
                    questions={relatedQuestions}
                    onQuestionClick={handleFollowUp}
                    isLoading={isLoading}
                  />
                )}

                {/* Spacer to prevent content from hiding behind sticky input */}
                <div className="h-32" />
              </div>
            </div>
          </div>
        </div>

        {/* Sticky Follow-up Input */}
        {content && !isLoading && (
          <div className="flex-none border-t border-gray-200 bg-white/95 backdrop-blur-sm sticky bottom-0 z-10">
            <div className="max-w-5xl mx-auto px-4 py-4">
              <FollowUpInput
                onSubmit={handleFollowUp}
                isLoading={isLoading}
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
