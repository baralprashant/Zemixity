"""
Citation Engine for properly injecting citations into AI responses
Works with any source list, not dependent on Gemini grounding metadata
"""

import re
from typing import List, Dict, Tuple, Optional
from difflib import SequenceMatcher
import json


class CitationEngine:
    """Handles citation injection for AI responses regardless of source type"""

    def __init__(self, similarity_threshold: float = 0.3):
        self.similarity_threshold = similarity_threshold

    def extract_factual_claims(self, text: str) -> List[str]:
        """Extract sentences that likely contain factual claims needing citations"""
        # Split into sentences
        sentences = re.split(r'(?<=[.!?])\s+', text)

        factual_claims = []
        # Patterns that indicate factual claims
        fact_patterns = [
            r'\b\d+\.?\d*\s*(?:percent|%|million|billion|thousand)',  # Statistics
            r'\b(?:is|are|was|were|has|have|had)\s+(?:a|an|the)?',    # Definitions
            r'\b(?:according to|research shows|studies indicate)',       # Research claims
            r'\b(?:founded|created|launched|developed|invented)',        # Historical facts
            r'\b(?:located|situated|found in|based in)',                # Geographic facts
            r'\b(?:costs?|prices?|worth|valued)',                       # Financial facts
            r'\b(?:measures?|weighs?|spans?|reaches?)',                 # Measurements
            r'\b(?:consists of|contains?|includes?|comprises?)',        # Composition facts
            r'\b(?:used for|designed to|serves as|functions as)',       # Purpose/function
        ]

        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 20:  # Skip very short sentences
                continue

            # Check if sentence contains factual patterns
            for pattern in fact_patterns:
                if re.search(pattern, sentence, re.IGNORECASE):
                    factual_claims.append(sentence)
                    break

            # Also include sentences with specific data points
            if any(char.isdigit() for char in sentence):
                if sentence not in factual_claims:
                    factual_claims.append(sentence)

        return factual_claims

    def calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two text segments"""
        # Normalize texts
        text1 = text1.lower().strip()
        text2 = text2.lower().strip()

        # Use sequence matcher for similarity
        return SequenceMatcher(None, text1, text2).ratio()

    def find_supporting_sources(self, claim: str, sources: List[Dict]) -> List[int]:
        """Find sources that support a given claim"""
        supporting_indices = []
        claim_lower = claim.lower()

        # Extract key terms from claim
        key_terms = re.findall(r'\b\w{4,}\b', claim_lower)
        key_terms = [term for term in key_terms if term not in
                     ['that', 'this', 'with', 'from', 'have', 'been', 'were', 'what', 'when', 'where']]

        for idx, source in enumerate(sources):
            score = 0

            # Check title relevance
            if 'title' in source:
                title_lower = source['title'].lower()
                for term in key_terms:
                    if term in title_lower:
                        score += 0.3

            # Check snippet relevance
            if 'snippet' in source:
                snippet_lower = source['snippet'].lower()

                # Check for key terms
                for term in key_terms:
                    if term in snippet_lower:
                        score += 0.2

                # Check for similarity with the claim
                similarity = self.calculate_similarity(claim[:100], snippet_lower[:200])
                score += similarity

            # Check URL/domain relevance for specific topics
            if 'url' in source:
                url_lower = source['url'].lower()
                # Add small boost for relevant domains
                if any(term in url_lower for term in key_terms[:3]):
                    score += 0.1

            # If score is above threshold, consider it supporting
            if score >= self.similarity_threshold:
                supporting_indices.append(idx)

        return supporting_indices  # Return all supporting sources, no limit

    def inject_citations(self, text: str, sources: List[Dict]) -> Tuple[str, List[Dict]]:
        """
        Main method to inject citations into text
        Returns: (text_with_citations, used_sources)
        """
        if not sources or len(sources) == 0:
            return text, []

        # Track which sources are actually used
        used_source_indices = set()
        citations_map = {}

        # Extract factual claims
        claims = self.extract_factual_claims(text)

        # Find supporting sources for each claim
        for claim in claims:
            supporting_indices = self.find_supporting_sources(claim, sources)
            if supporting_indices:
                citations_map[claim] = supporting_indices
                used_source_indices.update(supporting_indices)

        # Sort claims by length (longest first) to avoid partial replacements
        sorted_claims = sorted(citations_map.keys(), key=len, reverse=True)

        # Inject citations into text
        modified_text = text
        for claim in sorted_claims:
            source_indices = citations_map[claim]
            # Convert to 1-based indices for display
            citation_nums = [str(i + 1) for i in source_indices]
            citation_str = '[' + ','.join(citation_nums) + ']'

            # Add citation at the end of the claim
            # Find the claim in the text and add citation after it
            if claim in modified_text:
                # Add citation before the period if it exists
                if claim.endswith('.'):
                    replacement = claim[:-1] + ' ' + citation_str + '.'
                else:
                    replacement = claim + ' ' + citation_str

                modified_text = modified_text.replace(claim, replacement, 1)

        # If no claims were found or cited, try a fallback approach
        if not citations_map and sources:
            # Add general citations for paragraphs that mention topics from sources
            paragraphs = modified_text.split('\n\n')
            modified_paragraphs = []

            for para in paragraphs:
                if len(para) > 50:  # Only for substantial paragraphs
                    para_sources = self.find_supporting_sources(para[:200], sources)
                    if para_sources:
                        used_source_indices.update(para_sources)
                        citation_nums = [str(i + 1) for i in para_sources]
                        citation_str = '[' + ','.join(citation_nums) + ']'

                        # Add citation at the end of paragraph
                        if para.rstrip().endswith('.'):
                            para = para.rstrip()[:-1] + ' ' + citation_str + '.'
                        else:
                            para = para.rstrip() + ' ' + citation_str

                modified_paragraphs.append(para)

            modified_text = '\n\n'.join(modified_paragraphs)

        # Always return ALL sources to show comprehensive search results
        # Citations in text point to specific sources that were referenced
        # This allows users to see all sources searched, not just cited ones
        return modified_text, sources

    def validate_citations(self, text: str) -> bool:
        """Check if text has adequate citations"""
        # Count citation patterns
        citations = re.findall(r'\[\d+(?:,\d+)*\]', text)

        # Count sentences that might need citations
        sentences = re.split(r'(?<=[.!?])\s+', text)
        factual_sentences = len([s for s in sentences if len(s) > 30])

        # Should have at least 1 citation per 3 factual sentences
        return len(citations) >= factual_sentences / 3