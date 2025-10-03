'use client';

import { useState, FormEvent } from 'react';
import { Send, Loader2 } from 'lucide-react';

interface FollowUpInputProps {
  onSubmit: (query: string) => void;
  isLoading?: boolean;
}

export function FollowUpInput({ onSubmit, isLoading = false }: FollowUpInputProps) {
  const [query, setQuery] = useState('');

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (query.trim() && !isLoading) {
      onSubmit(query.trim());
      setQuery('');
    }
  };

  return (
    <form onSubmit={handleSubmit} className="w-full">
      <div className="relative">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Ask a follow-up question..."
          disabled={isLoading}
          className="w-full px-5 py-3 pr-12
            bg-white
            border border-gray-200
            rounded-xl
            focus:outline-none focus:ring-2 focus:ring-[#93C572] focus:border-transparent
            transition-all duration-200
            placeholder:text-gray-400
            disabled:opacity-50 disabled:cursor-not-allowed
            text-base"
        />
        <button
          type="submit"
          disabled={!query.trim() || isLoading}
          className="absolute right-2 top-1/2 -translate-y-1/2
            p-2 rounded-lg
            bg-[#93C572] hover:bg-[#82B461]
            text-white
            transition-all duration-200
            shadow-md hover:shadow-lg
            disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-[#93C572] disabled:shadow-md
            focus:outline-none focus:ring-2 focus:ring-[#93C572] focus:ring-offset-2
            flex items-center justify-center"
        >
          {isLoading ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <Send className="w-4 h-4" />
          )}
        </button>
      </div>
    </form>
  );
}
