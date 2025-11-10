"""
RAG (Retrieval-Augmented Generation) Pipeline
Implements multi-stage retrieval, ranking, and response generation
"""

from typing import List, Dict, Optional, Tuple
import re
from difflib import SequenceMatcher


class SourceRanker:
    """Ranks sources by relevance to the query"""

    def __init__(self):
        self.weights = {
            'title_relevance': 0.35,
            'snippet_relevance': 0.40,
            'freshness': 0.15,
            'domain_authority': 0.10
        }

    def rank_sources(
        self,
        sources: List[Dict],
        query: str,
        max_results: int = 10
    ) -> List[Dict]:
        """
        Rank sources by relevance to query
        Returns top N sources sorted by score
        """
        scored_sources = []

        query_terms = self._extract_key_terms(query)

        for source in sources:
            score = self._calculate_relevance_score(source, query, query_terms)
            scored_sources.append({
                **source,
                'relevance_score': score
            })

        # Sort by relevance score descending
        scored_sources.sort(key=lambda x: x['relevance_score'], reverse=True)

        return scored_sources[:max_results]

    def _extract_key_terms(self, text: str) -> List[str]:
        """Extract meaningful terms from query"""
        # Remove common words
        stop_words = {
            'what', 'when', 'where', 'who', 'why', 'how', 'is', 'are', 'was',
            'were', 'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at',
            'to', 'for', 'of', 'with', 'by', 'from', 'as', 'this', 'that',
            'these', 'those', 'can', 'could', 'would', 'should', 'may', 'might',
            'will', 'shall', 'do', 'does', 'did', 'have', 'has', 'had'
        }

        # Extract words (4+ characters)
        words = re.findall(r'\b\w{4,}\b', text.lower())

        # Filter stop words
        key_terms = [w for w in words if w not in stop_words]

        return key_terms

    def _calculate_relevance_score(
        self,
        source: Dict,
        query: str,
        query_terms: List[str]
    ) -> float:
        """Calculate overall relevance score for a source"""
        title = source.get('title', '').lower()
        snippet = source.get('snippet', '').lower()
        url = source.get('url', '').lower()

        # 1. Title relevance
        title_score = 0.0
        for term in query_terms:
            if term in title:
                title_score += 1.0
        title_score = min(title_score / max(len(query_terms), 1), 1.0)

        # 2. Snippet relevance
        snippet_score = 0.0
        for term in query_terms:
            if term in snippet:
                snippet_score += 1.0
        snippet_score = min(snippet_score / max(len(query_terms), 1), 1.0)

        # Boost if query appears as exact phrase
        if query.lower() in snippet:
            snippet_score = min(snippet_score + 0.3, 1.0)

        # 3. Freshness score (if publishDate available)
        freshness_score = 0.5  # Default neutral score
        publish_date = source.get('publishDate')
        if publish_date:
            # Simple freshness: articles from 2024+ get higher scores
            try:
                year = int(publish_date[:4])
                if year >= 2024:
                    freshness_score = 1.0
                elif year >= 2023:
                    freshness_score = 0.8
                elif year >= 2022:
                    freshness_score = 0.6
                else:
                    freshness_score = 0.4
            except:
                pass

        # 4. Domain authority (simple heuristic)
        domain_score = self._calculate_domain_authority(url)

        # Weighted final score
        final_score = (
            self.weights['title_relevance'] * title_score +
            self.weights['snippet_relevance'] * snippet_score +
            self.weights['freshness'] * freshness_score +
            self.weights['domain_authority'] * domain_score
        )

        return final_score

    def _calculate_domain_authority(self, url: str) -> float:
        """Simple domain authority scoring"""
        # High authority domains
        high_authority = [
            'wikipedia.org', 'github.com', 'stackoverflow.com',
            '.gov', '.edu', 'arxiv.org', 'nature.com', 'science.org',
            'nytimes.com', 'bbc.com', 'reuters.com', 'theguardian.com'
        ]

        # Medium authority
        medium_authority = [
            'medium.com', 'techcrunch.com', 'wired.com', 'forbes.com',
            '.org', 'cnn.com', 'bloomberg.com'
        ]

        url_lower = url.lower()

        for domain in high_authority:
            if domain in url_lower:
                return 1.0

        for domain in medium_authority:
            if domain in url_lower:
                return 0.7

        # Default score for other domains
        return 0.5


class SnippetExtractor:
    """Extracts relevant snippets from source content"""

    def __init__(self, max_snippet_length: int = 300):
        self.max_snippet_length = max_snippet_length

    def extract_relevant_snippets(
        self,
        source: Dict,
        query: str,
        num_snippets: int = 2
    ) -> List[str]:
        """
        Extract most relevant snippets from source content
        Returns list of snippet texts
        """
        content = source.get('snippet', '')
        if not content:
            return []

        # Split into sentences
        sentences = re.split(r'(?<=[.!?])\s+', content)

        # Score each sentence
        query_terms = self._extract_query_terms(query)
        scored_sentences = []

        for sentence in sentences:
            if len(sentence) > 20:  # Minimum sentence length
                score = self._score_sentence_relevance(sentence, query_terms)
                scored_sentences.append((sentence, score))

        # Sort by relevance
        scored_sentences.sort(key=lambda x: x[1], reverse=True)

        # Return top snippets
        snippets = []
        for sentence, score in scored_sentences[:num_snippets]:
            snippet = sentence[:self.max_snippet_length]
            if len(sentence) > self.max_snippet_length:
                snippet += '...'
            snippets.append(snippet)

        return snippets

    def _extract_query_terms(self, query: str) -> List[str]:
        """Extract key terms from query"""
        words = re.findall(r'\b\w{3,}\b', query.lower())
        stop_words = {'what', 'when', 'where', 'who', 'why', 'how', 'the', 'a', 'an'}
        return [w for w in words if w not in stop_words]

    def _score_sentence_relevance(self, sentence: str, query_terms: List[str]) -> float:
        """Score a sentence's relevance to query terms"""
        sentence_lower = sentence.lower()
        score = 0.0

        for term in query_terms:
            if term in sentence_lower:
                score += 1.0

        # Normalize by sentence length (prefer concise matches)
        word_count = len(sentence.split())
        if word_count > 0:
            score = score / (word_count ** 0.3)  # Slight penalty for length

        return score


class RAGPipeline:
    """Complete RAG pipeline for search and response generation"""

    def __init__(self):
        self.ranker = SourceRanker()
        self.snippet_extractor = SnippetExtractor()

    def process_sources(
        self,
        sources: List[Dict],
        query: str,
        max_sources: int = 10
    ) -> Tuple[List[Dict], int]:
        """
        Process and rank sources for RAG
        Returns: (ranked_sources, total_sources_reviewed)
        """
        total_reviewed = len(sources)

        # Rank sources by relevance
        ranked_sources = self.ranker.rank_sources(sources, query, max_sources)

        # Enhance with extracted snippets
        enhanced_sources = []
        for source in ranked_sources:
            # Extract additional relevant snippets if available
            snippets = self.snippet_extractor.extract_relevant_snippets(source, query)

            # Combine original snippet with extracted snippets
            all_snippets = [source.get('snippet', '')]
            all_snippets.extend(snippets)

            # Use best snippet (usually the original is already good from search API)
            enhanced_source = {
                **source,
                'enhanced_snippets': snippets,
                'best_snippet': all_snippets[0] if all_snippets else ''
            }

            enhanced_sources.append(enhanced_source)

        return enhanced_sources, total_reviewed

    def deduplicate_sources(self, sources: List[Dict]) -> List[Dict]:
        """Remove duplicate sources based on URL and content similarity"""
        seen_urls = set()
        unique_sources = []

        for source in sources:
            url = source.get('url', '')

            # Normalize URL (remove trailing slashes, www, etc.)
            normalized_url = url.lower().rstrip('/').replace('www.', '')

            if normalized_url not in seen_urls:
                seen_urls.add(normalized_url)
                unique_sources.append(source)

        return unique_sources

    def filter_low_quality_sources(
        self,
        sources: List[Dict],
        min_score: float = 0.2
    ) -> List[Dict]:
        """Filter out sources with very low relevance scores"""
        return [s for s in sources if s.get('relevance_score', 0) >= min_score]