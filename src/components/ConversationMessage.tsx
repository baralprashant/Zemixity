'use client';

import { ExternalLink, Globe, ChevronDown, ChevronUp } from 'lucide-react';
import { Card } from './ui/card';
import Image from 'next/image';
import { motion, AnimatePresence } from 'framer-motion';
import { useState } from 'react';

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
}

export function ConversationMessage({
  role,
  content,
  sources = [],
  isLast = false,
  index = 0,
  hideSources = false
}: ConversationMessageProps) {
  const isUser = role === 'user';
  const [isSourcesExpanded, setIsSourcesExpanded] = useState(false);

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
        <div className="flex justify-end mb-6">
          <div className="max-w-[85%]">
            <div className="bg-gray-100/70 rounded-2xl px-5 py-3.5 inline-block">
              <p className="text-gray-900 text-[15px] leading-relaxed">{content}</p>
            </div>
          </div>
        </div>
      )}

      {/* AI Response - No badge, just content */}
      {!isUser && (
        <div className="space-y-6">
          <div className="flex-1">
            {/* Response Content */}
            <div
              className="prose prose-sm max-w-none text-gray-700 leading-relaxed
                prose-headings:text-gray-900 prose-headings:font-semibold
                prose-p:my-2
                prose-a:text-blue-600 prose-a:no-underline hover:prose-a:underline
                prose-strong:text-gray-900 prose-strong:font-semibold
                prose-ul:my-2 prose-li:my-1
              "
              dangerouslySetInnerHTML={{ __html: content }}
            />
          </div>

          {/* Sources Section - Collapsible */}
          {!hideSources && sources && sources.length > 0 && (
            <div className="space-y-4">
              {/* Toggle Button */}
              <button
                onClick={() => setIsSourcesExpanded(!isSourcesExpanded)}
                className="flex items-center gap-2 px-3 py-2 rounded-full bg-gray-100 hover:bg-gray-200 transition-colors group"
              >
                <Globe className="h-4 w-4 text-gray-600" />
                <span className="text-sm font-medium text-gray-700">
                  {sources.length} {sources.length === 1 ? 'Source' : 'Sources'}
                </span>
                {isSourcesExpanded ? (
                  <ChevronUp className="h-4 w-4 text-gray-600 transition-transform" />
                ) : (
                  <ChevronDown className="h-4 w-4 text-gray-600 transition-transform" />
                )}
              </button>

              {/* Expandable Horizontal Scroll */}
              <AnimatePresence>
                {isSourcesExpanded && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                    transition={{ duration: 0.3 }}
                    className="overflow-hidden"
                  >
                    <div className="flex gap-3 overflow-x-auto pt-2 pb-2 scrollbar-thin scrollbar-thumb-gray-300 scrollbar-track-gray-100">
                      {sources.map((source, index) => (
                        <a
                          key={index}
                          href={source.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="group block flex-shrink-0 w-72"
                        >
                          <Card className="overflow-hidden h-full transition-all duration-200 hover:shadow-lg hover:scale-[1.02] hover:border-blue-400 border-gray-200">
                            {/* Thumbnail Image */}
                            {source.image && (
                              <div className="relative w-full h-32 bg-gray-100 overflow-hidden">
                                <Image
                                  src={source.image}
                                  alt={source.title}
                                  fill
                                  className="object-cover group-hover:scale-105 transition-transform duration-200"
                                  unoptimized
                                  onError={(e) => {
                                    // Hide image on error
                                    const target = e.target as HTMLElement;
                                    target.style.display = 'none';
                                  }}
                                />
                              </div>
                            )}

                            {/* Content */}
                            <div className="p-3 space-y-2">
                              {/* Favicon and Display URL */}
                              <div className="flex items-center gap-2">
                                {source.favicon && (
                                  <Image
                                    src={source.favicon}
                                    alt=""
                                    width={16}
                                    height={16}
                                    className="rounded"
                                    unoptimized
                                    onError={(e) => {
                                      // Fallback to Globe icon
                                      const target = e.target as HTMLElement;
                                      target.style.display = 'none';
                                    }}
                                  />
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
                                <p className="text-xs text-gray-600 line-clamp-2 leading-relaxed">
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
                              <div className="flex justify-end">
                                <ExternalLink className="h-3 w-3 text-gray-400 group-hover:text-blue-500 transition-colors" />
                              </div>
                            </div>
                          </Card>
                        </a>
                      ))}
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          )}
        </div>
      )}

      {/* Divider (except for last message) */}
      {!isLast && (
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
}
