"""
Pro Search - Multi-step reasoning for complex queries
Breaks down complex questions into sub-queries and synthesizes comprehensive answers
"""

from typing import Dict, List, Optional, Tuple
import re


class QueryDecomposer:
    """Breaks down complex queries into simpler sub-queries"""

    def __init__(self):
        self.complex_indicators = [
            'compare', 'difference between', 'vs', 'versus',
            'pros and cons', 'advantages and disadvantages',
            'how and why', 'what and how', 'when and where',
            'multiple', 'several', 'various', 'different',
            'comprehensive', 'detailed', 'in-depth', 'thorough'
        ]

    def is_complex_query(self, query: str) -> bool:
        """
        Determine if a query is complex enough to benefit from Pro Search

        Args:
            query: User's search query

        Returns:
            True if query is complex, False otherwise
        """
        query_lower = query.lower()

        # Check for complex indicators
        has_complex_indicators = any(indicator in query_lower for indicator in self.complex_indicators)

        # Check for multiple questions
        has_multiple_questions = query.count('?') > 1

        # Check for conjunctions that indicate multiple topics
        complex_conjunctions = [' and ', ' or ', ' as well as ', ' along with ']
        has_complex_conjunctions = sum(1 for conj in complex_conjunctions if conj in query_lower) >= 2

        # Check for long queries (likely complex)
        is_long = len(query.split()) > 15

        return (has_complex_indicators or
                has_multiple_questions or
                has_complex_conjunctions or
                is_long)

    def decompose_query(self, query: str, max_sub_queries: int = 3) -> List[str]:
        """
        Break down a complex query into simpler sub-queries

        Args:
            query: Complex query to decompose
            max_sub_queries: Maximum number of sub-queries to generate

        Returns:
            List of sub-queries
        """
        sub_queries = []

        # Handle comparison queries
        if any(word in query.lower() for word in ['compare', 'difference', 'vs', 'versus']):
            # Extract entities being compared
            entities = self._extract_comparison_entities(query)
            if len(entities) >= 2:
                for entity in entities[:max_sub_queries]:
                    sub_queries.append(f"What is {entity}? Key features and characteristics")

        # Handle pros/cons queries
        elif 'pros and cons' in query.lower() or 'advantages and disadvantages' in query.lower():
            topic = self._extract_main_topic(query)
            sub_queries.append(f"What are the advantages and benefits of {topic}?")
            sub_queries.append(f"What are the disadvantages and drawbacks of {topic}?")

        # Handle multi-part questions (multiple question marks)
        elif query.count('?') > 1:
            # Split by question marks and clean
            parts = [q.strip() + '?' for q in query.split('?') if q.strip()]
            sub_queries.extend(parts[:max_sub_queries])

        # Handle "how and why" type queries
        elif any(combo in query.lower() for combo in ['how and why', 'what and how', 'when and where']):
            topic = self._extract_main_topic(query)

            if 'how and why' in query.lower():
                sub_queries.append(f"How does {topic} work?")
                sub_queries.append(f"Why is {topic} important or necessary?")
            elif 'what and how' in query.lower():
                sub_queries.append(f"What is {topic}?")
                sub_queries.append(f"How does {topic} work or function?")

        # Handle comprehensive queries
        elif any(word in query.lower() for word in ['comprehensive', 'detailed', 'in-depth', 'thorough']):
            topic = self._extract_main_topic(query)
            sub_queries.append(f"What is {topic}? Basic overview and definition")
            sub_queries.append(f"{topic}: Key features, characteristics, and details")
            sub_queries.append(f"{topic}: Current trends, applications, and implications")

        # Fallback: if we couldn't decompose, return original query
        if not sub_queries:
            sub_queries.append(query)

        # Limit to max_sub_queries
        return sub_queries[:max_sub_queries]

    def _extract_comparison_entities(self, query: str) -> List[str]:
        """Extract entities being compared from query"""
        entities = []

        # Remove common comparison words
        cleaned = query.lower()
        for word in ['compare', 'comparison', 'between', 'difference', 'vs', 'versus', 'and']:
            cleaned = cleaned.replace(word, ' ')

        # Split and clean
        parts = [p.strip() for p in cleaned.split() if len(p.strip()) > 2]

        # Take first few meaningful parts
        if len(parts) >= 2:
            # Often comparison is "X vs Y" or "X and Y"
            entities = parts[:3]

        return entities

    def _extract_main_topic(self, query: str) -> str:
        """Extract the main topic from a query"""
        # Remove question words and common phrases
        topic = query.lower()

        remove_phrases = [
            'what is', 'what are', 'how does', 'how do', 'why is', 'why are',
            'when is', 'when are', 'where is', 'where are',
            'tell me about', 'explain', 'describe',
            'comprehensive guide to', 'detailed overview of',
            'pros and cons of', 'advantages and disadvantages of',
            'in-depth', 'thorough', 'detailed'
        ]

        for phrase in remove_phrases:
            topic = topic.replace(phrase, '')

        # Remove question marks and extra spaces
        topic = topic.replace('?', '').strip()

        # If topic is too short, return original query
        if len(topic) < 3:
            return query

        return topic


class ProSearchEngine:
    """Manages multi-step Pro Search execution"""

    def __init__(self):
        self.decomposer = QueryDecomposer()

    def should_use_pro_search(self, query: str, user_requested: bool = False) -> bool:
        """
        Determine if Pro Search should be used

        Args:
            query: User's query
            user_requested: Whether user explicitly requested Pro Search

        Returns:
            True if Pro Search should be used
        """
        # Always use if user explicitly requested
        if user_requested:
            return True

        # Use for complex queries
        return self.decomposer.is_complex_query(query)

    def plan_search_strategy(self, query: str) -> Dict:
        """
        Create a search strategy for Pro Search

        Args:
            query: Original complex query

        Returns:
            Search strategy dictionary
        """
        sub_queries = self.decomposer.decompose_query(query, max_sub_queries=3)

        strategy = {
            'original_query': query,
            'sub_queries': sub_queries,
            'num_steps': len(sub_queries),
            'synthesis_required': len(sub_queries) > 1,
            'search_depth': 'deep' if len(sub_queries) > 2 else 'moderate'
        }

        return strategy

    def build_synthesis_prompt(
        self,
        original_query: str,
        sub_results: List[Dict],
        all_sources: List[Dict]
    ) -> str:
        """
        Build a prompt for synthesizing multi-step search results

        Args:
            original_query: Original user query
            sub_results: Results from each sub-query
            all_sources: All sources gathered

        Returns:
            Synthesis prompt for AI
        """
        # Format sub-results
        sub_results_text = ""
        for i, result in enumerate(sub_results, 1):
            sub_query = result.get('query', '')
            findings = result.get('summary', 'No findings')
            sub_results_text += f"\n\nSub-query {i}: {sub_query}\nFindings: {findings}"

        # Format sources
        sources_text = ""
        for idx, source in enumerate(all_sources[:15], 1):  # Top 15 sources
            title = source.get('title', 'Untitled')
            url = source.get('url', '')
            snippet = source.get('snippet', '')

            sources_text += f"\n\n[{idx}] {title}\nURL: {url}\nContent: {snippet}"

        prompt = f"""You are providing a comprehensive, well-researched answer using Pro Search.

ORIGINAL QUESTION: {original_query}

This question was broken down into {len(sub_results)} sub-queries for thorough research:
{sub_results_text}

ALL SOURCES (from multiple searches):
{sources_text}

Your task is to synthesize ALL the information from the sub-queries and sources into ONE comprehensive answer that:

1. Directly answers the original question
2. Integrates insights from all sub-queries
3. Provides depth and nuance from multiple angles
4. Uses evidence from the sources (cite with [1], [2], etc.)
5. Organizes information logically with clear sections
6. Highlights key findings and important details
7. Notes any conflicting information or different perspectives

Format your response with:
- Clear section headings (use ## for main sections)
- **Bold** for key terms and important points
- Bullet points (-) for lists and multiple items
- Citations [1][2][3] for all factual claims
- A brief conclusion summarizing the answer

Remember: This is Pro Search - provide a thorough, well-sourced, comprehensive answer that goes deeper than a standard search.
"""

        return prompt

    def merge_and_deduplicate_sources(
        self,
        source_lists: List[List[Dict]]
    ) -> List[Dict]:
        """
        Merge multiple source lists and remove duplicates

        Args:
            source_lists: List of source lists from different searches

        Returns:
            Merged and deduplicated source list
        """
        seen_urls = set()
        merged = []

        for source_list in source_lists:
            for source in source_list:
                url = source.get('url', '')
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    merged.append(source)

        return merged

    def estimate_search_time(self, num_sub_queries: int) -> int:
        """
        Estimate how long Pro Search will take

        Args:
            num_sub_queries: Number of sub-queries to execute

        Returns:
            Estimated time in seconds
        """
        # Each search takes roughly 2-3 seconds
        # Synthesis adds 3-5 seconds
        base_time = num_sub_queries * 2.5
        synthesis_time = 4

        return int(base_time + synthesis_time)

    def get_progress_messages(self, num_steps: int) -> List[str]:
        """
        Get progress messages for Pro Search steps

        Args:
            num_steps: Total number of steps

        Returns:
            List of progress messages
        """
        messages = [
            f"🔍 Pro Search activated - Breaking down query into {num_steps} sub-queries...",
            "📊 Executing comprehensive multi-step search...",
            "🔎 Gathering information from multiple angles...",
            "📚 Reviewing and ranking all sources...",
            "🧠 Synthesizing comprehensive answer..."
        ]

        return messages[:num_steps + 2]  # Adjust based on steps
