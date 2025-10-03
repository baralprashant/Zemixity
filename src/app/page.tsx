'use client';

import { useRouter } from 'next/navigation';
import { Logo } from '@/components/Logo';
import { SearchInput } from '@/components/SearchInput';

export default function Home() {
  const router = useRouter();

  const handleSearch = (query: string) => {
    router.push(`/search?q=${encodeURIComponent(query)}`);
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-4 bg-gradient-to-b from-gray-50 to-white">
      <div className="w-full max-w-3xl space-y-8 animate-fade-in">
        {/* Logo and Title */}
        <div className="flex flex-col items-center space-y-6">
          <Logo size={80} />
          <div className="text-center space-y-2">
            <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold bg-gradient-to-r from-gray-900 via-gray-700 to-gray-900 bg-clip-text text-transparent">
              How can I help you today?
            </h1>
          </div>
        </div>

        {/* Search Input */}
        <SearchInput
          onSearch={handleSearch}
          placeholder="Ask me anything..."
          autoFocus={true}
          large={true}
        />

      </div>
    </div>
  );
}
