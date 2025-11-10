import { useState, useCallback, useRef, useEffect } from 'react';

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

interface UseStreamingSearchResult {
  search: (query: string, file?: File) => Promise<void>;
  followUp: (query: string) => Promise<void>;
  loadThread: (threadData: { id: string; session_id: string; messages: Message[] }) => void;
  content: string;
  sources: Source[];
  relatedQuestions: string[];
  status: string;
  isLoading: boolean;
  sessionId: string | null;
  threadId: string | null;
  error: string | null;
  reset: () => void;
  conversation: Message[];
  currentQuery: string;
}

export function useStreamingSearch(): UseStreamingSearchResult {
  const [content, setContent] = useState('');
  const [sources, setSources] = useState<Source[]>([]);
  const [relatedQuestions, setRelatedQuestions] = useState<string[]>([]);
  const [status, setStatus] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [threadId, setThreadId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [conversation, setConversation] = useState<Message[]>([]);
  const [currentQuery, setCurrentQuery] = useState('');
  const abortControllerRef = useRef<AbortController | null>(null);
  const throttleTimerRef = useRef<NodeJS.Timeout | null>(null);
  const pendingContentRef = useRef<string>('');

  const throttledSetContent = useCallback((newContent: string) => {
    pendingContentRef.current = newContent;

    if (throttleTimerRef.current) {
      return;
    }

    throttleTimerRef.current = setTimeout(() => {
      setContent(pendingContentRef.current);
      throttleTimerRef.current = null;
    }, 33);
  }, []);

  const reset = useCallback(() => {
    setContent('');
    setSources([]);
    setRelatedQuestions([]);
    setStatus('');
    setIsLoading(false);
    setError(null);
    setConversation([]);
    setCurrentQuery('');
    pendingContentRef.current = '';
    if (throttleTimerRef.current) {
      clearTimeout(throttleTimerRef.current);
      throttleTimerRef.current = null;
    }
  }, []);

  const loadThread = useCallback((threadData: { id: string; session_id: string; messages: Message[] }) => {
    // Load existing conversation without triggering a new search
    setSessionId(threadData.session_id);
    setThreadId(threadData.id);
    setConversation(threadData.messages);

    // Set the last assistant message as current content and sources
    const lastAssistantMessage = [...threadData.messages].reverse().find(m => m.role === 'assistant');
    if (lastAssistantMessage) {
      setContent(lastAssistantMessage.content);
      setSources(lastAssistantMessage.sources || []);
    }

    // Get the last user query for display
    const lastUserMessage = [...threadData.messages].reverse().find(m => m.role === 'user');
    if (lastUserMessage) {
      setCurrentQuery(lastUserMessage.content);
    }

    setIsLoading(false);
    setStatus('');
    setError(null);
  }, []);

  // Cleanup on unmount to prevent memory leaks
  useEffect(() => {
    return () => {
      // Clear any pending throttle timers
      if (throttleTimerRef.current) {
        clearTimeout(throttleTimerRef.current);
        throttleTimerRef.current = null;
      }

      // Abort any ongoing requests
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
        abortControllerRef.current = null;
      }
    };
  }, []);

  const search = useCallback(async (query: string, file?: File) => {
    // Abort any ongoing request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    // Store the current query
    setCurrentQuery(query);

    // Reset streaming state but keep conversation
    setContent('');
    setSources([]);
    setRelatedQuestions([]);
    setError(null);
    setIsLoading(true);
    setStatus('Connecting...');

    // Add user message to conversation
    setConversation(prev => [...prev, { role: 'user', content: query }]);

    const controller = new AbortController();
    abortControllerRef.current = controller;

    let currentContent = '';
    let currentSources: Source[] = [];

    try {
      let response: Response;

      if (file) {
        // Multimodal search with file
        const formData = new FormData();
        formData.append('q', query || 'Analyze this file');
        formData.append('file', file);

        response = await fetch('/api/search/multimodal/stream', {
          method: 'POST',
          body: formData,
          signal: controller.signal,
        });
      } else {
        // Regular text search
        response = await fetch(`/api/search/stream?q=${encodeURIComponent(query)}`, {
          signal: controller.signal,
        });
      }

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body!.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');

        // Keep the last incomplete line in the buffer
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));

              switch (data.type) {
                case 'session_id':
                  setSessionId(data.sessionId);
                  break;

                case 'thread_id':
                  setThreadId(data.threadId);
                  break;

                case 'status':
                  setStatus(data.message);
                  break;

                case 'token':
                  currentContent += data.content;
                  throttledSetContent(currentContent);
                  break;

                case 'sources':
                  currentSources = data.sources;
                  setSources(currentSources);
                  setStatus('');
                  break;

                case 'related_questions':
                  setRelatedQuestions(data.questions);
                  break;

                case 'done':
                  setIsLoading(false);
                  setStatus('');
                  // Add complete assistant response to conversation
                  setConversation(prev => [...prev, {
                    role: 'assistant',
                    content: currentContent,
                    sources: currentSources
                  }]);
                  break;

                case 'error':
                  setError(data.message);
                  setIsLoading(false);
                  setStatus('');
                  break;
              }
            } catch (e) {
              console.error('Error parsing SSE data:', e);
            }
          }
        }
      }
    } catch (err: unknown) {
      if (err instanceof Error && err.name === 'AbortError') {
        console.log('Request aborted');
      } else if (err instanceof Error) {
        console.error('Streaming error:', err);
        setError(err.message || 'An error occurred during search');
        setIsLoading(false);
        setStatus('');
      } else {
        console.error('Streaming error:', err);
        setError('An error occurred during search');
        setIsLoading(false);
        setStatus('');
      }
    }
  }, [throttledSetContent]);

  const followUp = useCallback(async (query: string) => {
    if (!sessionId) {
      console.error('No session ID available for follow-up');
      return;
    }

    // Abort any ongoing request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    // Store the current query
    setCurrentQuery(query);

    // Add user message to conversation
    setConversation(prev => [...prev, { role: 'user', content: query }]);

    // Reset streaming state (but keep previous content/sources visible)
    setContent('');
    setSources([]);
    setError(null);
    setIsLoading(true);
    setStatus('Thinking...');

    const controller = new AbortController();
    abortControllerRef.current = controller;

    let currentContent = '';
    let currentSources: Source[] = [];

    try {
      const response = await fetch('/api/follow-up/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          sessionId,
          threadId,
          query
        }),
        signal: controller.signal,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body!.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      // Clear content for new follow-up response
      setContent('');
      setSources([]);

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');

        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));

              switch (data.type) {
                case 'status':
                  setStatus(data.message);
                  break;

                case 'token':
                  currentContent += data.content;
                  throttledSetContent(currentContent);
                  break;

                case 'sources':
                  currentSources = data.sources;
                  setSources(currentSources);
                  setStatus('');
                  break;

                case 'related_questions':
                  setRelatedQuestions(data.questions);
                  break;

                case 'done':
                  setIsLoading(false);
                  setStatus('');
                  // Add complete assistant response to conversation
                  setConversation(prev => [...prev, {
                    role: 'assistant',
                    content: currentContent,
                    sources: currentSources
                  }]);
                  break;

                case 'error':
                  setError(data.message);
                  setIsLoading(false);
                  setStatus('');
                  break;
              }
            } catch (e) {
              console.error('Error parsing SSE data:', e);
            }
          }
        }
      }
    } catch (err: unknown) {
      if (err instanceof Error && err.name === 'AbortError') {
        console.log('Follow-up request aborted');
      } else if (err instanceof Error) {
        console.error('Follow-up streaming error:', err);
        setError(err.message || 'An error occurred during follow-up');
        setIsLoading(false);
        setStatus('');
      } else {
        console.error('Follow-up streaming error:', err);
        setError('An error occurred during follow-up');
        setIsLoading(false);
        setStatus('');
      }
    }
  }, [sessionId, threadId, throttledSetContent]);

  return {
    search,
    followUp,
    loadThread,
    content,
    sources,
    relatedQuestions,
    status,
    isLoading,
    sessionId,
    threadId,
    error,
    reset,
    conversation,
    currentQuery,
  };
}
