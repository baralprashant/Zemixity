'use client';

import { useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { AlertCircle, RefreshCw, Home } from 'lucide-react';

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Log error to console in development
    console.error('Application error:', error);
  }, [error]);

  return (
    <div className="min-h-screen flex items-center justify-center px-4 bg-gradient-to-b from-gray-50 to-white">
      <div className="max-w-md w-full space-y-6 text-center">
        {/* Error Icon */}
        <div className="flex justify-center">
          <div className="rounded-full bg-red-100 p-4">
            <AlertCircle className="h-12 w-12 text-red-600" />
          </div>
        </div>

        {/* Error Message */}
        <div className="space-y-2">
          <h1 className="text-2xl font-bold text-gray-900">
            Something went wrong
          </h1>
          <p className="text-gray-600">
            {error.message || "We encountered an unexpected error. Please try again."}
          </p>
          {error.digest && (
            <p className="text-sm text-gray-400 font-mono">
              Error ID: {error.digest}
            </p>
          )}
        </div>

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <Button
            onClick={reset}
            className="flex items-center gap-2 bg-[#93C572] hover:bg-[#82B461]"
          >
            <RefreshCw className="h-4 w-4" />
            Try Again
          </Button>
          <Button
            onClick={() => window.location.href = '/'}
            variant="outline"
            className="flex items-center gap-2"
          >
            <Home className="h-4 w-4" />
            Go Home
          </Button>
        </div>

        {/* Additional Help */}
        <div className="pt-4 text-sm text-gray-500">
          <p>
            If this problem persists, try refreshing the page or clearing your browser cache.
          </p>
        </div>
      </div>
    </div>
  );
}
