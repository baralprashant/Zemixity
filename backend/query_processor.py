"""
Query Processor - Understands and expands user queries for better search results
"""

import re
from typing import List, Dict, Tuple
from datetime import datetime


class QueryProcessor:
    """Processes and enhances user queries for better search results"""

    def __init__(self):
        # Query intent patterns
        self.intent_patterns = {
            'factual': [
                r'\b(what|who|when|where|which)\s+(is|are|was|were)\b',
                r'\b(define|definition of|meaning of)\b',
                r'\b(how many|how much)\b',
            ],
            'comparison': [
                r'\b(difference between|compare|vs|versus)\b',
                r'\b(better|worse|superior|inferior)\b',
                r'\b(advantages|disadvantages|pros|cons)\b',
            ],
            'how_to': [
                r'\b(how to|how do|how can)\b',
                r'\b(steps to|guide to|tutorial)\b',
                r'\b(learn|teach me)\b',
            ],
            'explanation': [
                r'\b(why|how does|explain|describe)\b',
                r'\b(what causes|what makes)\b',
                r'\b(reason for|purpose of)\b',
            ],
            'recommendation': [
                r'\b(best|top|recommend|suggest)\b',
                r'\b(should I|which one|what to choose)\b',
            ],
            'analysis': [
                r'\b(analyze|analysis|review|evaluate)\b',
                r'\b(impact of|effect of|consequence)\b',
            ],
            'current_events': [
                r'\b(latest|recent|news|current|today|now)\b',
                r'\b(2024|2025)\b',  # Recent years
            ],
        }

    def process_query(self, query: str) -> Dict[str, any]:
        """
        Process a query and return enhanced information
        Returns: {
            'original': original query,
            'intent': detected intent,
            'expanded_queries': list of query variations,
            'keywords': extracted keywords,
            'temporal_context': time-related context
        }
        """
        # Classify intent
        intent = self.classify_intent(query)

        # Extract keywords
        keywords = self.extract_keywords(query)

        # Expand query
        expanded_queries = self.expand_query(query, intent)

        # Detect temporal context
        temporal_context = self.detect_temporal_context(query)

        return {
            'original': query,
            'intent': intent,
            'expanded_queries': expanded_queries,
            'keywords': keywords,
            'temporal_context': temporal_context,
            'enhanced_query': self.build_enhanced_query(query, keywords, temporal_context)
        }

    def classify_intent(self, query: str) -> str:
        """Classify the intent of the query"""
        query_lower = query.lower()

        # Check each intent pattern
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, query_lower, re.IGNORECASE):
                    return intent

        # Default to factual
        return 'factual'

    def extract_keywords(self, query: str) -> List[str]:
        """Extract important keywords from query"""
        # Remove common stop words
        stop_words = {
            'a', 'an', 'the', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'can', 'of', 'at', 'by', 'for', 'with',
            'about', 'as', 'into', 'through', 'during', 'before', 'after',
            'above', 'below', 'to', 'from', 'up', 'down', 'in', 'out', 'on',
            'off', 'over', 'under', 'again', 'further', 'then', 'once'
        }

        # Extract words (preserve case for proper nouns)
        words = re.findall(r'\b[A-Za-z][a-z]*[A-Za-z0-9]*\b', query)

        # Filter stop words and short words
        keywords = []
        for word in words:
            if word.lower() not in stop_words and len(word) > 2:
                # Preserve if starts with capital (likely proper noun)
                if word[0].isupper():
                    keywords.append(word)
                else:
                    keywords.append(word.lower())

        return keywords

    def expand_query(self, query: str, intent: str) -> List[str]:
        """
        Generate query variations for better search coverage
        """
        expanded = []

        # Add original query
        expanded.append(query)

        keywords = self.extract_keywords(query)

        # Intent-specific expansions
        if intent == 'how_to':
            # Add tutorial/guide variations
            expanded.append(f"{query} tutorial")
            expanded.append(f"{query} guide")
            expanded.append(f"step by step {query}")

        elif intent == 'comparison':
            # Add versus variations
            for keyword in keywords:
                if len(keyword) > 3:
                    expanded.append(f"{keyword} comparison")
                    expanded.append(f"{keyword} review")

        elif intent == 'explanation':
            # Add explanatory variations
            expanded.append(f"understanding {query}")
            expanded.append(f"{query} explained")

        elif intent == 'recommendation':
            # Add recommendation variations
            expanded.append(f"best {' '.join(keywords)}")
            expanded.append(f"top {' '.join(keywords)}")

        elif intent == 'current_events':
            # Add temporal markers
            current_year = datetime.now().year
            expanded.append(f"{query} {current_year}")
            expanded.append(f"{query} latest")

        # Add keyword-based expansion
        if len(keywords) > 2:
            # Create query from main keywords only
            main_keywords = keywords[:3]
            expanded.append(" ".join(main_keywords))

        # Remove duplicates while preserving order
        seen = set()
        unique_expanded = []
        for q in expanded:
            if q.lower() not in seen:
                seen.add(q.lower())
                unique_expanded.append(q)

        # Limit to top 3 expansions
        return unique_expanded[:3]

    def detect_temporal_context(self, query: str) -> Dict[str, any]:
        """
        Detect time-related context in the query
        """
        query_lower = query.lower()

        temporal_markers = {
            'recent': ['recent', 'latest', 'current', 'now', 'today', 'this week', 'this month'],
            'historical': ['history', 'historical', 'origin', 'invented', 'founded', 'created'],
            'future': ['future', 'upcoming', 'will', 'prediction', 'forecast'],
            'specific_year': re.findall(r'\b(19\d{2}|20\d{2})\b', query)
        }

        context = {
            'time_relevance': 'any',  # any, recent, historical, future
            'specific_year': None,
            'requires_fresh_data': False
        }

        # Check for recent/current markers
        if any(marker in query_lower for marker in temporal_markers['recent']):
            context['time_relevance'] = 'recent'
            context['requires_fresh_data'] = True

        # Check for historical markers
        elif any(marker in query_lower for marker in temporal_markers['historical']):
            context['time_relevance'] = 'historical'

        # Check for future markers
        elif any(marker in query_lower for marker in temporal_markers['future']):
            context['time_relevance'] = 'future'

        # Check for specific year
        if temporal_markers['specific_year']:
            context['specific_year'] = temporal_markers['specific_year'][0]

        return context

    def build_enhanced_query(
        self,
        original_query: str,
        keywords: List[str],
        temporal_context: Dict
    ) -> str:
        """
        Build an enhanced query for search
        """
        enhanced = original_query

        # Add temporal markers if needed
        if temporal_context['requires_fresh_data']:
            current_year = datetime.now().year
            if str(current_year) not in enhanced:
                enhanced = f"{enhanced} {current_year}"

        # Add specificity if query is too short
        if len(keywords) < 2:
            enhanced = f"{enhanced} information details"

        return enhanced

    def should_use_multiple_searches(self, intent: str) -> bool:
        """Determine if query requires multiple search passes"""
        # Complex queries that benefit from multiple searches
        return intent in ['comparison', 'analysis', 'recommendation']

    def get_search_hints(self, intent: str, temporal_context: Dict) -> Dict[str, any]:
        """
        Get hints for search optimization
        """
        hints = {
            'prefer_fresh_sources': temporal_context['requires_fresh_data'],
            'expected_sources': 5,  # Default
            'domain_preferences': [],
        }

        # Intent-specific hints
        if intent == 'factual':
            hints['domain_preferences'] = ['wikipedia', 'encyclopedia', '.edu', '.gov']
            hints['expected_sources'] = 3

        elif intent == 'how_to':
            hints['domain_preferences'] = ['tutorial', 'guide', 'documentation']
            hints['expected_sources'] = 5

        elif intent == 'current_events':
            hints['domain_preferences'] = ['news', 'reuters', 'bbc', 'nytimes']
            hints['prefer_fresh_sources'] = True
            hints['expected_sources'] = 7

        elif intent == 'comparison':
            hints['expected_sources'] = 8

        return hints