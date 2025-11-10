'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { ConversationMessage } from '@/components/ConversationMessage';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert, AlertTitle, AlertDescription } from '@/components/ui/alert';
import { Logo } from '@/components/Logo';
import { ExternalLink } from 'lucide-react';
import Link from 'next/link';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  sources: Array<{
    title: string;
    url: string;
    snippet: string;
    image?: string;
    favicon?: string;
    displayUrl?: string;
    publishDate?: string;
  }>;
  created_at: string;
}

interface SharedThread {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  messages: Message[];
}

export default function SharedConversationPage() {
  const params = useParams();
  const shareId = params?.shareId as string;
  const [thread, setThread] = useState<SharedThread | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!shareId) return;

    const fetchSharedThread = async () => {
      try {
        setLoading(true);
        const response = await fetch(`/api/shared/${shareId}`);

        if (!response.ok) {
          if (response.status === 404) {
            throw new Error('This shared conversation was not found. It may have been deleted.');
          }
          throw new Error('Failed to load shared conversation');
        }

        const data = await response.json();
        setThread(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'An error occurred');
      } finally {
        setLoading(false);
      }
    };

    fetchSharedThread();
  }, [shareId]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white">
        <div className="max-w-5xl mx-auto px-4 py-8">
          {/* Header Skeleton */}
          <div className="mb-8">
            <Skeleton className="h-8 w-64 mb-2" />
            <Skeleton className="h-4 w-48" />
          </div>

          {/* Content Skeleton */}
          <div className="bg-white border border-gray-200 rounded-2xl p-6 md:p-8">
            <div className="space-y-8">
              <div className="space-y-3">
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-3/4" />
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error || !thread) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white flex items-center justify-center px-4">
        <div className="max-w-md w-full space-y-6">
          <div className="flex justify-center">
            <Logo size={64} />
          </div>
          <Alert variant="destructive">
            <AlertTitle>Unable to Load Conversation</AlertTitle>
            <AlertDescription>
              {error || 'This shared conversation could not be found.'}
            </AlertDescription>
          </Alert>
          <div className="flex justify-center">
            <Link
              href="/"
              className="inline-flex items-center gap-2 text-blue-600 hover:text-blue-700 font-medium"
            >
              <ExternalLink className="w-4 h-4" />
              Go to Zemixity Home
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white">
      <div className="max-w-5xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-4">
            <Logo size={40} />
            <h1 className="text-2xl md:text-3xl font-bold text-gray-900">
              {thread.title}
            </h1>
          </div>
          <div className="flex items-center gap-4 text-sm text-gray-500">
            <span>
              Shared conversation
            </span>
            <span>•</span>
            <span>
              {new Date(thread.created_at).toLocaleDateString('en-US', {
                year: 'numeric',
                month: 'long',
                day: 'numeric',
              })}
            </span>
          </div>
        </div>

        {/* Conversation */}
        <div className="bg-white border border-gray-200 rounded-2xl p-6 md:p-8">
          <div className="space-y-8">
            {thread.messages.map((message, index) => (
              <ConversationMessage
                key={message.id}
                role={message.role}
                content={message.content}
                sources={message.sources}
                isLast={index === thread.messages.length - 1}
                index={index}
                hideSources={false}
              />
            ))}
          </div>
        </div>

        {/* Footer */}
        <div className="mt-8 text-center">
          <Link
            href="/"
            className="inline-flex items-center gap-2 text-blue-600 hover:text-blue-700 font-medium"
          >
            <ExternalLink className="w-4 h-4" />
            Try Zemixity for yourself
          </Link>
        </div>
      </div>
    </div>
  );
}
