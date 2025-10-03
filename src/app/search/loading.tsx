import { Skeleton } from '@/components/ui/skeleton';
import { Loader2 } from 'lucide-react';

export default function SearchLoading() {
  return (
    <div className="flex flex-col h-screen bg-gradient-to-b from-gray-50 to-white">
      {/* Header Skeleton */}
      <div className="flex-none border-b border-gray-200 bg-white/80 backdrop-blur-sm sticky top-0 z-10">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <div className="flex items-center gap-4">
            <Skeleton className="h-10 w-10 rounded-full" />
            <Skeleton className="h-10 flex-1 rounded-2xl" />
            <Skeleton className="h-10 w-32 rounded-full" />
          </div>
        </div>
      </div>

      {/* Content Skeleton */}
      <div className="flex-1 overflow-y-auto">
        <div className="max-w-4xl mx-auto px-4 py-6 space-y-8">
          {/* Loading Indicator */}
          <div className="flex items-center justify-center gap-3 py-12">
            <Loader2 className="h-6 w-6 animate-spin text-[#93C572]" />
            <span className="text-lg text-gray-600">Searching...</span>
          </div>

          {/* Question Skeleton */}
          <div className="space-y-3">
            <div className="flex gap-3">
              <Skeleton className="h-8 w-8 rounded-full flex-shrink-0" />
              <div className="flex-1 space-y-2">
                <Skeleton className="h-5 w-3/4" />
                <Skeleton className="h-5 w-1/2" />
              </div>
            </div>
          </div>

          {/* Answer Skeleton */}
          <div className="space-y-4">
            <div className="flex gap-3">
              <Skeleton className="h-8 w-8 rounded-full flex-shrink-0" />
              <div className="flex-1 space-y-3">
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-5/6" />
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-4/5" />
              </div>
            </div>

            {/* Source Cards Skeleton */}
            <div className="ml-11 mt-6 space-y-3">
              <Skeleton className="h-8 w-32 rounded-full" />
              <div className="flex gap-3 overflow-x-auto">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="flex-shrink-0 w-72">
                    <div className="border rounded-lg overflow-hidden">
                      <Skeleton className="h-32 w-full" />
                      <div className="p-3 space-y-2">
                        <Skeleton className="h-3 w-24" />
                        <Skeleton className="h-4 w-full" />
                        <Skeleton className="h-3 w-full" />
                        <Skeleton className="h-3 w-2/3" />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Related Questions Skeleton */}
          <div className="space-y-3 pt-6">
            <Skeleton className="h-6 w-48" />
            <div className="grid gap-2">
              {[1, 2, 3].map((i) => (
                <Skeleton key={i} className="h-12 w-full rounded-lg" />
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
