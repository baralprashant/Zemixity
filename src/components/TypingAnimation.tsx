'use client';

import { useState, useEffect, useRef } from 'react';

interface TypingAnimationProps {
  content: string;
}

export function TypingAnimation({ content }: TypingAnimationProps) {
  const [displayedContent, setDisplayedContent] = useState('');
  const lastContentRef = useRef('');

  useEffect(() => {
    if (content === lastContentRef.current) {
      return;
    }

    if (content.length < lastContentRef.current.length) {
      setDisplayedContent('');
      lastContentRef.current = '';
    }

    const newContent = content.slice(lastContentRef.current.length);
    lastContentRef.current = content;

    if (newContent) {
      setDisplayedContent(content);
    }
  }, [content]);

  return (
    <div
      className="prose prose-xs max-w-none text-gray-700 leading-relaxed
        prose-headings:text-gray-900 prose-headings:font-semibold prose-headings:mt-4 prose-headings:mb-2
        prose-p:my-2
        prose-a:text-blue-600 prose-a:no-underline hover:prose-a:underline
        prose-strong:text-gray-900 prose-strong:font-semibold
        prose-ul:my-2 prose-ul:space-y-1 prose-li:my-0.5
        prose-h3:text-base prose-h3:mt-4 prose-h3:mb-2
      "
      dangerouslySetInnerHTML={{ __html: displayedContent }}
    />
  );
}
