'use client';

import { useState, FormEvent } from 'react';
import { Search, Loader2 } from 'lucide-react';

interface SearchInputProps {
  onSearch: (query: string) => void;
  initialValue?: string;
  isLoading?: boolean;
  placeholder?: string;
  autoFocus?: boolean;
  large?: boolean;
}

export function SearchInput({
  onSearch,
  initialValue = '',
  isLoading = false,
  placeholder = 'Ask anything...',
  autoFocus = true,
  large = true,
}: SearchInputProps) {
  const [query, setQuery] = useState(initialValue);

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (query.trim() && !isLoading) {
      onSearch(query.trim());
    }
  };

  return (
    <form onSubmit={handleSubmit} className="w-full">
      <div className="relative group">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder={placeholder}
          disabled={isLoading}
          autoFocus={autoFocus}
          className={`
            w-full bg-white
            border border-gray-200
            ${large ? 'px-6 py-4 text-lg' : 'px-4 py-3 text-base'}
            rounded-2xl
            focus:outline-none focus:ring-2 focus:ring-[#93C572] focus:border-transparent
            transition-all duration-200
            placeholder:text-gray-400
            disabled:opacity-50 disabled:cursor-not-allowed
            pr-14
          `}
        />
        <button
          type="submit"
          disabled={!query.trim() || isLoading}
          className={`
            absolute right-3 top-1/2 -translate-y-1/2
            ${large ? 'p-3' : 'p-2'}
            rounded-xl
            bg-[#93C572] hover:bg-[#82B461]
            text-white
            transition-all duration-200
            shadow-md hover:shadow-lg
            disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-[#93C572] disabled:shadow-md
            focus:outline-none focus:ring-2 focus:ring-[#93C572] focus:ring-offset-2
            flex items-center justify-center
          `}
        >
          {isLoading ? (
            <Loader2 className={`${large ? 'w-5 h-5' : 'w-4 h-4'} animate-spin`} />
          ) : (
            <Search className={`${large ? 'w-5 h-5' : 'w-4 h-4'}`} />
          )}
        </button>
      </div>
    </form>
  );
}
