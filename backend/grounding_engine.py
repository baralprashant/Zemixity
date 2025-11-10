"""
Grounding Engine - Ensures AI responses are strictly based on retrieved sources
Prevents hallucinations by enforcing source-based answers
"""

from typing import List, Dict, Optional


class GroundingEngine:
    """Enforces strict grounding of AI responses to source material"""

    def __init__(self):
        self.strict_mode = True

    def build_grounded_prompt(
        self,
        query: str,
        sources: Optional[List[Dict]] = None,
        conversation_context: Optional[str] = None
    ) -> str:
        """
        Build a prompt that enforces grounding to sources
        """
        if not sources or len(sources) == 0:
            # No sources - allow conversational response
            return self._build_conversational_prompt(query)

        # Build grounded prompt with strict instructions
        return self._build_strict_grounded_prompt(query, sources, conversation_context)

    def _build_conversational_prompt(self, query: str) -> str:
        """Simple prompt for conversational queries without sources"""
        return f"""Please provide a clear, helpful response to this question: {query}

Format your response with:
- Clear paragraphs
- Use **bold** sparingly for emphasis
- Use bullet points (-) for lists when appropriate
- Keep it natural and concise"""

    def _build_strict_grounded_prompt(
        self,
        query: str,
        sources: List[Dict],
        conversation_context: Optional[str] = None
    ) -> str:
        """
        Build a strict grounded prompt that prevents hallucinations
        """
        # Format sources for the prompt
        sources_text = self._format_sources_for_prompt(sources)

        # Context prefix if this is a follow-up
        context_section = ""
        if conversation_context:
            context_section = f"""Previous conversation context:
{conversation_context}

"""

        prompt = f"""{context_section}You are a search assistant that provides accurate, well-sourced answers.

CRITICAL GROUNDING RULES:
1. ONLY use information from the sources provided below
2. Every factual claim must be based on the sources
3. If the sources don't contain enough information to answer the question, say "The available sources don't provide enough information about [specific aspect]"
4. Do not make assumptions or inferences beyond what the sources state
5. Do not use your general knowledge - rely exclusively on the provided sources
6. When you reference information, it must come directly from the sources

SOURCES:
{sources_text}

USER QUESTION: {query}

Provide a comprehensive answer using ONLY the information from the sources above. Format your response with:
- Clear paragraphs
- Use **bold** for key terms
- Use bullet points (-) for lists
- Keep it natural and well-organized

Remember: If information is not in the sources, acknowledge the limitation rather than guessing."""

        return prompt

    def _format_sources_for_prompt(self, sources: List[Dict]) -> str:
        """Format sources into a readable text block for the prompt"""
        formatted_sources = []

        for idx, source in enumerate(sources[:10], 1):  # Limit to top 10 sources
            title = source.get('title', 'Untitled')
            url = source.get('url', '')
            snippet = source.get('snippet', '')

            source_text = f"""[{idx}] {title}
URL: {url}
Content: {snippet}"""

            formatted_sources.append(source_text)

        return "\n\n".join(formatted_sources)

    def validate_response_grounding(
        self,
        response: str,
        sources: List[Dict]
    ) -> Dict[str, any]:
        """
        Validate if response appears to be properly grounded
        Returns validation results
        """
        # Extract key information from sources
        source_terms = set()
        for source in sources:
            # Extract meaningful words from snippets
            snippet = source.get('snippet', '').lower()
            words = snippet.split()
            # Add words longer than 5 characters (likely meaningful terms)
            source_terms.update([w for w in words if len(w) > 5 and w.isalpha()])

        # Analyze response
        response_lower = response.lower()
        response_words = response_lower.split()
        response_terms = set([w for w in response_words if len(w) > 5 and w.isalpha()])

        # Calculate grounding score
        if len(response_terms) == 0:
            grounding_score = 0.0
        else:
            matching_terms = response_terms.intersection(source_terms)
            grounding_score = len(matching_terms) / len(response_terms)

        # Check for warning phrases that might indicate hallucination
        warning_phrases = [
            "in general",
            "typically",
            "usually",
            "often",
            "commonly",
            "it is known that",
            "studies show",  # if not in sources
            "research indicates",  # if not in sources
        ]

        potential_hallucinations = []
        for phrase in warning_phrases:
            if phrase in response_lower:
                # Check if this phrase appears in sources
                phrase_in_sources = any(phrase in s.get('snippet', '').lower() for s in sources)
                if not phrase_in_sources:
                    potential_hallucinations.append(phrase)

        return {
            'grounding_score': grounding_score,
            'appears_grounded': grounding_score > 0.3,
            'potential_hallucinations': potential_hallucinations,
            'matching_terms_count': len(response_terms.intersection(source_terms)),
            'total_terms_count': len(response_terms)
        }

    def enhance_prompt_with_examples(self, base_prompt: str) -> str:
        """Add few-shot examples to improve grounding"""
        examples = """
EXAMPLES OF GOOD GROUNDED RESPONSES:

Example 1:
Question: "What is the capital of France?"
Sources: [1] "Paris is the capital and most populous city of France..."
Good Response: "Paris is the capital of France [1]."
Bad Response: "Paris is the capital of France. It's known for the Eiffel Tower and has a population of 2 million." (Extra info not in sources)

Example 2:
Question: "How does photosynthesis work?"
Sources: [Sources don't contain info about photosynthesis]
Good Response: "The available sources don't provide information about how photosynthesis works."
Bad Response: "Photosynthesis is the process where plants convert light to energy..." (Using general knowledge)

---

"""
        return examples + base_prompt