"""
Focus Modes - Specialized search modes for different content types
Academic, Code, Writing, etc.
"""

from typing import Dict, List, Optional


class FocusMode:
    """Base class for focus modes"""

    def __init__(self, name: str):
        self.name = name

    def get_search_filters(self) -> Dict[str, any]:
        """Get search filters for this mode"""
        return {}

    def get_prompt_modifier(self) -> str:
        """Get prompt modifications for this mode"""
        return ""

    def get_source_preferences(self) -> List[str]:
        """Get preferred source domains for this mode"""
        return []

    def get_ranking_weights(self) -> Dict[str, float]:
        """Get custom ranking weights for this mode"""
        return {
            'title_relevance': 0.35,
            'snippet_relevance': 0.40,
            'freshness': 0.15,
            'domain_authority': 0.10
        }


class AcademicMode(FocusMode):
    """Academic research mode - prioritizes scholarly sources"""

    def __init__(self):
        super().__init__("academic")

    def get_search_filters(self) -> Dict[str, any]:
        return {
            'prefer_domains': [
                '.edu', '.gov', 'scholar.google.com', 'arxiv.org',
                'pubmed.ncbi.nlm.nih.gov', 'jstor.org', 'springer.com',
                'sciencedirect.com', 'nature.com', 'science.org',
                'ieee.org', 'acm.org', 'researchgate.net'
            ],
            'min_quality_score': 0.4,  # Higher threshold for academic
            'prefer_fresh': False  # Academic work can be older
        }

    def get_prompt_modifier(self) -> str:
        return """
You are providing an academic, scholarly response.

Requirements:
1. Use formal, academic language
2. Cite sources using [1], [2] format consistently
3. Include methodology details when relevant
4. Acknowledge limitations and alternative viewpoints
5. Prioritize peer-reviewed sources
6. Provide context and background information
7. Use precise, technical terminology

Format your response as a scholarly summary with proper citations.
"""

    def get_source_preferences(self) -> List[str]:
        return [
            'scholar.google.com',
            'arxiv.org',
            'pubmed',
            '.edu',
            '.gov',
            'nature.com',
            'science.org'
        ]

    def get_ranking_weights(self) -> Dict[str, float]:
        return {
            'title_relevance': 0.30,
            'snippet_relevance': 0.35,
            'freshness': 0.05,  # Less important for academic
            'domain_authority': 0.30  # More important for academic
        }


class CodeMode(FocusMode):
    """Code/Programming mode - prioritizes technical documentation and code examples"""

    def __init__(self):
        super().__init__("code")

    def get_search_filters(self) -> Dict[str, any]:
        return {
            'prefer_domains': [
                'stackoverflow.com', 'github.com', 'docs.python.org',
                'developer.mozilla.org', 'docs.microsoft.com',
                'dev.to', 'medium.com/tag/programming',
                'reddit.com/r/programming', 'hackernews',
                'geeksforgeeks.org', 'tutorialspoint.com'
            ],
            'min_quality_score': 0.3,
            'prefer_fresh': True  # Code/tech changes frequently
        }

    def get_prompt_modifier(self) -> str:
        return """
You are providing a technical, code-focused response.

Requirements:
1. Include code examples when relevant (use ```language syntax)
2. Explain technical concepts clearly
3. Mention version compatibility and dependencies
4. Include best practices and common pitfalls
5. Provide working code snippets when possible
6. Explain time/space complexity for algorithms
7. Link to official documentation

Format your response with:
- Clear explanations
- Well-commented code examples
- Step-by-step implementation details
"""

    def get_source_preferences(self) -> List[str]:
        return [
            'stackoverflow.com',
            'github.com',
            'docs.',  # Official docs
            'developer.mozilla.org',
            'dev.to'
        ]

    def get_ranking_weights(self) -> Dict[str, float]:
        return {
            'title_relevance': 0.35,
            'snippet_relevance': 0.40,
            'freshness': 0.20,  # More important for code
            'domain_authority': 0.05  # Less strict for code (community sources)
        }


class WritingMode(FocusMode):
    """Writing mode - focuses on style, grammar, and examples"""

    def __init__(self):
        super().__init__("writing")

    def get_search_filters(self) -> Dict[str, any]:
        return {
            'prefer_domains': [
                'grammarly.com', 'purdue.edu/owl',  # Purdue OWL
                'chicagomanualofstyle.org', 'apastyle.org',
                'merriam-webster.com', 'thesaurus.com',
                'writingexplained.org', 'literarydevices.net'
            ],
            'min_quality_score': 0.3,
            'prefer_fresh': False
        }

    def get_prompt_modifier(self) -> str:
        return """
You are providing writing guidance and style recommendations.

Requirements:
1. Focus on clarity, style, and proper grammar
2. Provide examples of good and bad usage
3. Explain the reasoning behind recommendations
4. Include style guide references when applicable
5. Suggest improvements and alternatives
6. Address both formal and informal contexts
7. Be prescriptive but acknowledge style variations

Format your response with:
- Clear examples
- Before/after comparisons when helpful
- Style tips and best practices
"""

    def get_source_preferences(self) -> List[str]:
        return [
            'grammarly',
            'purdue.edu',
            'chicagomanualofstyle',
            'apastyle',
            'merriam-webster'
        ]


class NewsMode(FocusMode):
    """News mode - prioritizes recent, reputable news sources"""

    def __init__(self):
        super().__init__("news")

    def get_search_filters(self) -> Dict[str, any]:
        return {
            'prefer_domains': [
                'reuters.com', 'apnews.com', 'bbc.com', 'nytimes.com',
                'theguardian.com', 'washingtonpost.com', 'cnn.com',
                'bloomberg.com', 'ft.com', 'economist.com', 'axios.com'
            ],
            'min_quality_score': 0.35,
            'prefer_fresh': True,  # Very important for news
            'max_age_days': 30  # Prefer sources from last 30 days
        }

    def get_prompt_modifier(self) -> str:
        return """
You are providing a news-focused response.

Requirements:
1. Prioritize recent, breaking information
2. Include publication dates and sources
3. Present multiple perspectives when applicable
4. Distinguish facts from opinions
5. Provide context and background
6. Note any developing/changing situations
7. Cite reputable news sources

Format your response with:
- Latest developments first
- Clear attribution of sources
- Balanced coverage
"""

    def get_source_preferences(self) -> List[str]:
        return [
            'reuters',
            'apnews',
            'bbc',
            'nytimes',
            'theguardian',
            'bloomberg'
        ]

    def get_ranking_weights(self) -> Dict[str, float]:
        return {
            'title_relevance': 0.30,
            'snippet_relevance': 0.35,
            'freshness': 0.30,  # Much more important for news
            'domain_authority': 0.05
        }


class FocusModeManager:
    """Manages different focus modes"""

    def __init__(self):
        self.modes = {
            'web': FocusMode('web'),  # Default web search
            'academic': AcademicMode(),
            'code': CodeMode(),
            'writing': WritingMode(),
            'news': NewsMode()
        }

    def get_mode(self, mode_name: str) -> FocusMode:
        """Get a focus mode by name"""
        return self.modes.get(mode_name.lower(), self.modes['web'])

    def get_available_modes(self) -> List[str]:
        """Get list of available focus mode names"""
        return list(self.modes.keys())

    def apply_mode(
        self,
        mode_name: str,
        base_prompt: str,
        sources: List[Dict]
    ) -> tuple[str, List[Dict]]:
        """
        Apply a focus mode to the search
        Returns: (modified_prompt, filtered_sources)
        """
        mode = self.get_mode(mode_name)

        # Modify prompt
        modified_prompt = base_prompt + "\n\n" + mode.get_prompt_modifier()

        # Filter sources based on preferences
        filtered_sources = self._filter_sources_by_mode(sources, mode)

        return modified_prompt, filtered_sources

    def _filter_sources_by_mode(
        self,
        sources: List[Dict],
        mode: FocusMode
    ) -> List[Dict]:
        """Filter sources based on mode preferences"""
        filters = mode.get_search_filters()
        preferred_domains = filters.get('prefer_domains', [])

        if not preferred_domains:
            return sources

        # Score sources based on domain preference
        scored_sources = []
        for source in sources:
            url = source.get('url', '').lower()
            score = source.get('relevance_score', 0.5)

            # Boost score if domain matches preferences
            for domain in preferred_domains:
                if domain in url:
                    score += 0.2  # Boost preferred domains
                    break

            scored_sources.append({
                **source,
                'relevance_score': min(score, 1.0)  # Cap at 1.0
            })

        # Re-sort by new scores
        scored_sources.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)

        return scored_sources