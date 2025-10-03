'use client';

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useState } from 'react';

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(() => new QueryClient({
    defaultOptions: {
      queries: {
        // Cache search results for 5 minutes
        staleTime: 5 * 60 * 1000,
        // Keep cached data for 10 minutes
        gcTime: 10 * 60 * 1000,
        // Retry failed requests once
        retry: 1,
        // Disable refetch on window focus to prevent auto-refresh and duplicate threads
        refetchOnWindowFocus: false,
        // Don't refetch on mount if data is fresh
        refetchOnMount: false,
      },
    },
  }));

  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
}
