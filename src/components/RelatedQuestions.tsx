'use client';

import { Lightbulb } from 'lucide-react';
import { Button } from './ui/button';

interface RelatedQuestionsProps {
  questions: string[];
  onQuestionClick: (question: string) => void;
  isLoading?: boolean;
}

export function RelatedQuestions({
  questions,
  onQuestionClick,
  isLoading = false
}: RelatedQuestionsProps) {
  if (questions.length === 0 || isLoading) {
    return null;
  }

  return (
    <div className="bg-white border border-gray-200 rounded-2xl p-6">
      <div className="flex items-center gap-2 mb-4">
        <Lightbulb className="h-5 w-5 text-[#93C572]" />
        <h3 className="text-lg font-semibold text-gray-900">
          Related Questions
        </h3>
      </div>

      <div className="grid gap-2 sm:grid-cols-2">
        {questions.map((question, index) => (
          <Button
            key={index}
            variant="outline"
            className="h-auto py-3 px-4 text-left justify-start hover:bg-[#93C572]/5 hover:border-[#93C572] hover:text-[#93C572] transition-all"
            onClick={() => onQuestionClick(question)}
          >
            <span className="line-clamp-2 text-sm">{question}</span>
          </Button>
        ))}
      </div>
    </div>
  );
}
