'use client';

import { ExternalLink, Globe, ChevronDown, ChevronUp } from 'lucide-react';
import { Card } from './ui/card';
import Image from 'next/image';
import { motion, AnimatePresence } from 'framer-motion';
import { useState, useMemo, memo, useEffect, useRef } from 'react';
import { TypingAnimation } from './TypingAnimation';
import DOMPurify from 'dompurify';

interface Source {
  title: string;
  url: string;
  snippet: string;
  image?: string;
  favicon?: string;
  displayUrl?: string;
  publishDate?: string;
}

interface ConversationMessageProps {
  role: 'user' | 'assistant';
  content: string;
  sources?: Source[];
  isLast?: boolean;
  index?: number;
  hideSources?: boolean;
  isStreaming?: boolean;
}

export const ConversationMessage = memo(function ConversationMessage({
  role,
  content,
  sources = [],
  isLast = false,
  index = 0,
  hideSources = false,
  isStreaming = false
}: ConversationMessageProps) {
  const isUser = role === 'user';
  const [isSourcesExpanded, setIsSourcesExpanded] = useState(false);
  const [imageErrors, setImageErrors] = useState<Set<number>>(new Set());
  const [faviconErrors, setFaviconErrors] = useState<Set<number>>(new Set());
  const contentRef = useRef<HTMLDivElement>(null);

  const handleImageError = (index: number) => {
    setImageErrors(prev => new Set(prev).add(index));
  };

  const handleFaviconError = (index: number) => {
    setFaviconErrors(prev => new Set(prev).add(index));
  };

  // Handle citation clicks with event delegation (safer than inline onclick)
  useEffect(() => {
    const contentElement = contentRef.current;
    if (!contentElement || isStreaming) return;

    const handleCitationClick = (e: MouseEvent) => {
      const target = e.target as HTMLElement;

      // Check if the clicked element is a citation
      if (target.classList.contains('citation')) {
        const url = target.getAttribute('data-url');
        if (url) {
          // Validate URL before opening
          try {
            const validUrl = new URL(url);
            // Only allow http and https protocols
            if (validUrl.protocol === 'http:' || validUrl.protocol === 'https:') {
              window.open(url, '_blank', 'noopener,noreferrer');
            } else {
              console.warn('Blocked invalid URL protocol:', validUrl.protocol);
            }
          } catch {
            console.error('Invalid URL in citation:', url);
          }
        }
        e.preventDefault();
        e.stopPropagation();
      }
    };

    contentElement.addEventListener('click', handleCitationClick);

    return () => {
      contentElement.removeEventListener('click', handleCitationClick);
    };
  }, [isStreaming]);

  const renderedContent = useMemo(() => {
    if (isStreaming) {
      return <TypingAnimation content={content} />;
    }

    // Sanitize content before rendering
    const sanitizedContent = DOMPurify.sanitize(content, {
      ALLOWED_TAGS: ['p', 'br', 'strong', 'em', 'ul', 'ol', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'a', 'code', 'pre', 'blockquote', 'sup'],
      ALLOWED_ATTR: ['href', 'target', 'rel', 'class', 'data-source-index', 'data-url', 'data-title', 'title'],
      ALLOW_DATA_ATTR: true
    });

    return (
      <div
        ref={contentRef}
        className="prose prose-xs max-w-none text-gray-700 leading-relaxed
          prose-headings:text-gray-900 prose-headings:font-semibold prose-headings:mt-4 prose-headings:mb-2
          prose-p:my-2
          prose-a:text-blue-600 prose-a:no-underline hover:prose-a:underline
          prose-strong:text-gray-900 prose-strong:font-semibold
          prose-ul:my-2 prose-ul:space-y-1 prose-li:my-0.5
          prose-h3:text-base prose-h3:mt-4 prose-h3:mb-2
        "
        dangerouslySetInnerHTML={{ __html: sanitizedContent }}
      />
    );
  }, [content, isStreaming]);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{
        duration: 0.4,
        delay: index * 0.05,
        ease: [0.25, 0.1, 0.25, 1]
      }}
      className="space-y-6"
    >
      {/* User Question - Soft bubble */}
      {isUser && (
        <div className="flex justify-start mb-3">
          <div className="max-w-[85%]">
            <div className="bg-gray-100/70 rounded-2xl px-5 py-3.5 inline-block">
              <p className="text-gray-900 text-base leading-relaxed">{content}</p>
            </div>
          </div>
        </div>
      )}

      {/* AI Response - No badge, just content */}
      {!isUser && (
        <div className="space-y-6">
          <div className="flex-1">
            {renderedContent}
          </div>

          {/* Sources Section - Collapsible Pill */}
          {!hideSources && sources && sources.length > 0 && (
            <div className="mt-4 space-y-3">
              {/* Collapsible Pill Button */}
              <button
                onClick={() => setIsSourcesExpanded(!isSourcesExpanded)}
                className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-gray-100 hover:bg-gray-200 transition-all duration-200 group"
              >
                <Globe className="h-4 w-4 text-gray-600" />
                <span className="text-sm font-medium text-gray-700">
                  Sources
                </span>
                <span className="text-xs text-gray-500 bg-white rounded-full px-2 py-0.5">
                  {sources.length}
                </span>
                {isSourcesExpanded ? (
                  <ChevronUp className="h-4 w-4 text-gray-600 transition-transform" />
                ) : (
                  <ChevronDown className="h-4 w-4 text-gray-600 transition-transform" />
                )}
              </button>

              {/* Expandable Horizontal Scroll - Show 3 cards initially */}
              <AnimatePresence>
                {isSourcesExpanded && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                    transition={{ duration: 0.3 }}
                    className="overflow-hidden"
                  >
                    <div className="relative">
                      <div className="flex gap-4 overflow-x-auto pb-4 snap-x snap-mandatory scrollbar-hide">
                        {sources.map((source, index) => (
                          <a
                            key={index}
                            href={source.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="group block flex-shrink-0 w-80 snap-start"
                          >
                            <Card className="overflow-hidden h-full transition-all duration-200 hover:shadow-xl hover:scale-[1.02] hover:border-blue-400 border-gray-200">
                              {/* Thumbnail Image */}
                              {source.image && !imageErrors.has(index) && (
                                <div className="relative w-full h-40 bg-gray-100 overflow-hidden">
                                  <Image
                                    src={source.image}
                                    alt={source.title}
                                    fill
                                    className="object-cover group-hover:scale-105 transition-transform duration-200"
                                    loading="lazy"
                                    unoptimized
                                    onError={() => handleImageError(index)}
                                  />
                                </div>
                              )}

                              {/* Content */}
                              <div className="p-4 space-y-2">
                                {/* Favicon and Display URL */}
                                <div className="flex items-center gap-2">
                                  {source.favicon && !faviconErrors.has(index) ? (
                                    <Image
                                      src={source.favicon}
                                      alt=""
                                      width={16}
                                      height={16}
                                      className="rounded"
                                      loading="lazy"
                                      unoptimized
                                      onError={() => handleFaviconError(index)}
                                    />
                                  ) : (
                                    <Globe className="w-4 h-4 text-gray-400 flex-shrink-0" />
                                  )}
                                  <span className="text-xs text-gray-500 truncate">
                                    {source.displayUrl || new URL(source.url).hostname.replace('www.', '')}
                                  </span>
                                </div>

                                {/* Title */}
                                <h5 className="font-medium text-sm text-gray-900 line-clamp-2 group-hover:text-blue-600 transition-colors leading-snug">
                                  {source.title}
                                </h5>

                                {/* Snippet */}
                                {source.snippet && (
                                  <p className="text-xs text-gray-600 line-clamp-3 leading-relaxed">
                                    {source.snippet}
                                  </p>
                                )}

                                {/* Publish Date */}
                                {source.publishDate && (
                                  <p className="text-xs text-gray-400">
                                    {new Date(source.publishDate).toLocaleDateString('en-US', {
                                      month: 'short',
                                      day: 'numeric',
                                      year: 'numeric'
                                    })}
                                  </p>
                                )}

                                {/* External Link Icon */}
                                <div className="flex justify-end pt-1">
                                  <ExternalLink className="h-3.5 w-3.5 text-gray-400 group-hover:text-blue-500 transition-colors" />
                                </div>
                              </div>
                            </Card>
                          </a>
                        ))}
                      </div>
                      {/* Scroll Indicator */}
                      {sources.length > 3 && (
                        <div className="absolute right-0 top-0 bottom-4 w-12 bg-gradient-to-l from-gray-50 to-transparent pointer-events-none" />
                      )}
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          )}
        </div>
      )}

      {/* Divider (only after AI responses, not after user queries) */}
      {!isLast && !isUser && (
        <div className="my-12 py-4">
          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-gray-200"></div>
            </div>
          </div>
        </div>
      )}
    </motion.div>
  );
});
