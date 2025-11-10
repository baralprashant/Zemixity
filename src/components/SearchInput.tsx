'use client';

import { useState, FormEvent, useRef } from 'react';
import { Search, Loader2, Mic, MicOff, Paperclip, X, FileText, Image as ImageIcon } from 'lucide-react';

// Web Speech API type definitions
interface SpeechRecognitionEvent extends Event {
  results: SpeechRecognitionResultList;
}

interface SpeechRecognitionErrorEvent extends Event {
  error: string;
}

interface SpeechRecognition extends EventTarget {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  start: () => void;
  stop: () => void;
  onstart: (() => void) | null;
  onend: (() => void) | null;
  onresult: ((event: SpeechRecognitionEvent) => void) | null;
  onerror: ((event: SpeechRecognitionErrorEvent) => void) | null;
}

interface SpeechRecognitionConstructor {
  new(): SpeechRecognition;
}

declare global {
  interface Window {
    SpeechRecognition?: SpeechRecognitionConstructor;
    webkitSpeechRecognition?: SpeechRecognitionConstructor;
  }
}

interface SearchInputProps {
  onSearch: (query: string, file?: File) => void;
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
  const [isListening, setIsListening] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [recognition, setRecognition] = useState<SpeechRecognition | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if ((query.trim() || selectedFile) && !isLoading) {
      onSearch(query.trim(), selectedFile || undefined);
      setSelectedFile(null); // Clear file after submission
    }
  };

  const startListening = () => {
    // Check for Web Speech API support
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
      alert('Voice input is not supported in your browser. Please try Chrome or Edge.');
      return;
    }

    const SpeechRecognitionAPI = window.webkitSpeechRecognition || window.SpeechRecognition;
    if (!SpeechRecognitionAPI) return;

    const recognition = new SpeechRecognitionAPI();

    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = 'en-US';

    recognition.onstart = () => {
      setIsListening(true);
      console.log('Voice recognition started');
    };

    recognition.onend = () => {
      setIsListening(false);
      console.log('Voice recognition ended');
    };

    recognition.onresult = (event: SpeechRecognitionEvent) => {
      const transcript = event.results[0][0].transcript;
      setQuery(transcript);
      console.log('Voice transcript:', transcript);
    };

    recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
      console.error('Voice recognition error:', event.error);
      setIsListening(false);
      if (event.error === 'no-speech') {
        alert('No speech detected. Please try again.');
      } else if (event.error === 'not-allowed') {
        alert('Microphone access denied. Please allow microphone access in your browser settings.');
      }
    };

    recognition.start();
    setRecognition(recognition);
  };

  const stopListening = () => {
    if (recognition) {
      recognition.stop();
      setIsListening(false);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      // Check file type
      const validTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp', 'application/pdf'];
      if (!validTypes.includes(file.type)) {
        alert('Please select an image (JPG, PNG, GIF, WebP) or PDF file.');
        return;
      }

      // Check file size (max 10MB)
      const maxSize = 10 * 1024 * 1024; // 10MB
      if (file.size > maxSize) {
        alert('File size must be less than 10MB.');
        return;
      }

      setSelectedFile(file);
    }
  };

  const removeFile = () => {
    setSelectedFile(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const getFileIcon = (file: File) => {
    if (file.type.startsWith('image/')) {
      return <ImageIcon className="w-4 h-4" />;
    } else if (file.type === 'application/pdf') {
      return <FileText className="w-4 h-4" />;
    }
    return <Paperclip className="w-4 h-4" />;
  };

  return (
    <form onSubmit={handleSubmit} className="w-full space-y-2">
      {/* File preview */}
      {selectedFile && (
        <div className="flex items-center gap-2 px-4 py-2 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
          <div className="flex items-center gap-2 flex-1 min-w-0">
            <div className="text-blue-600 dark:text-blue-400">
              {getFileIcon(selectedFile)}
            </div>
            <span className="text-sm text-blue-700 dark:text-blue-300 font-medium truncate">
              {selectedFile.name}
            </span>
            <span className="text-xs text-blue-500 dark:text-blue-400 whitespace-nowrap">
              ({(selectedFile.size / 1024).toFixed(1)} KB)
            </span>
          </div>
          <button
            type="button"
            onClick={removeFile}
            className="p-1 hover:bg-blue-100 dark:hover:bg-blue-800 rounded transition-colors"
            title="Remove file"
          >
            <X className="w-4 h-4 text-blue-600 dark:text-blue-400" />
          </button>
        </div>
      )}

      <div className="relative group">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder={selectedFile ? 'Ask about this file...' : placeholder}
          disabled={isLoading}
          autoFocus={autoFocus}
          className={`
            w-full bg-white dark:bg-gray-800
            border border-gray-200 dark:border-gray-700
            ${large ? 'px-6 py-4 text-lg' : 'px-4 py-3 text-base'}
            rounded-2xl
            focus:outline-none focus:ring-2 focus:ring-[#93C572] focus:border-transparent
            transition-all duration-200
            placeholder:text-gray-400 dark:placeholder:text-gray-500
            text-gray-900 dark:text-gray-100
            disabled:opacity-50 disabled:cursor-not-allowed
            ${large ? 'pr-32' : 'pr-28'}
          `}
        />

        {/* File upload button */}
        <input
          ref={fileInputRef}
          type="file"
          onChange={handleFileSelect}
          accept="image/*,application/pdf"
          className="hidden"
          disabled={isLoading}
        />
        <button
          type="button"
          onClick={() => fileInputRef.current?.click()}
          disabled={isLoading}
          className={`
            absolute ${large ? 'right-24' : 'right-20'} top-1/2 -translate-y-1/2
            ${large ? 'p-2.5' : 'p-2'}
            rounded-lg
            text-gray-500 dark:text-gray-400
            hover:bg-gray-100 dark:hover:bg-gray-700
            hover:text-gray-700 dark:hover:text-gray-300
            transition-all duration-200
            disabled:opacity-50 disabled:cursor-not-allowed
            focus:outline-none focus:ring-2 focus:ring-[#93C572]
          `}
          title="Upload image or PDF"
        >
          <Paperclip className={`${large ? 'w-5 h-5' : 'w-4 h-4'}`} />
        </button>

        {/* Voice input button */}
        <button
          type="button"
          onClick={isListening ? stopListening : startListening}
          disabled={isLoading}
          className={`
            absolute ${large ? 'right-14' : 'right-12'} top-1/2 -translate-y-1/2
            ${large ? 'p-2.5' : 'p-2'}
            rounded-lg
            transition-all duration-200
            disabled:opacity-50 disabled:cursor-not-allowed
            focus:outline-none focus:ring-2 focus:ring-[#93C572]
            ${
              isListening
                ? 'bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400 animate-pulse'
                : 'text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 hover:text-gray-700 dark:hover:text-gray-300'
            }
          `}
          title={isListening ? 'Stop recording' : 'Voice input'}
        >
          {isListening ? (
            <MicOff className={`${large ? 'w-5 h-5' : 'w-4 h-4'}`} />
          ) : (
            <Mic className={`${large ? 'w-5 h-5' : 'w-4 h-4'}`} />
          )}
        </button>

        {/* Submit button */}
        <button
          type="submit"
          disabled={(!query.trim() && !selectedFile) || isLoading}
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

      {/* Disclaimer */}
      <p className="text-xs text-gray-500 dark:text-gray-400 text-center mt-2">
        Zemixity is not always right. Double check your responses.
      </p>
    </form>
  );
}
