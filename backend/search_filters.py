"""
Search Filters - Advanced filtering for search results
Supports date ranges, domain filtering, and file type filtering
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
from enum import Enum


class DateFilter(str, Enum):
    """Predefined date filter options"""
    ANY_TIME = "any"
    PAST_DAY = "d1"
    PAST_WEEK = "w1"
    PAST_MONTH = "m1"
    PAST_YEAR = "y1"


class FileType(str, Enum):
    """Supported file types for filtering"""
    PDF = "pdf"
    DOC = "doc"
    DOCX = "docx"
    XLS = "xls"
    XLSX = "xlsx"
    PPT = "ppt"
    PPTX = "pptx"
    TXT = "txt"


class SearchFilterManager:
    """Manages search filters for Google Custom Search API"""

    def __init__(self):
        self.supported_date_filters = {
            DateFilter.PAST_DAY: "d1",
            DateFilter.PAST_WEEK: "w1",
            DateFilter.PAST_MONTH: "m1",
            DateFilter.PAST_YEAR: "y1",
        }

    def build_filter_params(
        self,
        date_filter: Optional[str] = None,
        include_domains: Optional[List[str]] = None,
        exclude_domains: Optional[List[str]] = None,
        file_type: Optional[str] = None,
        exact_terms: Optional[str] = None,
        exclude_terms: Optional[str] = None,
    ) -> Dict[str, str]:
        """
        Build Google Custom Search API filter parameters

        Args:
            date_filter: Time range filter (d1, w1, m1, y1)
            include_domains: List of domains to search within
            exclude_domains: List of domains to exclude
            file_type: File type to filter (pdf, doc, etc.)
            exact_terms: Exact phrase that must appear
            exclude_terms: Terms to exclude from results

        Returns:
            Dictionary of API parameters
        """
        params = {}

        # Date restriction
        if date_filter and date_filter != DateFilter.ANY_TIME:
            if date_filter in self.supported_date_filters.values():
                params['dateRestrict'] = date_filter
                print(f"🗓️  Date filter: {date_filter}")

        # Domain inclusion (site search)
        if include_domains:
            # Google CSE supports OR for multiple domains
            # Format: site:domain1.com OR site:domain2.com
            domain_query = " OR ".join([f"site:{d}" for d in include_domains])
            params['q_append'] = domain_query
            print(f"🌐 Include domains: {', '.join(include_domains)}")

        # Domain exclusion
        if exclude_domains:
            # Format: -site:domain1.com -site:domain2.com
            exclude_query = " ".join([f"-site:{d}" for d in exclude_domains])
            if 'q_append' in params:
                params['q_append'] += f" {exclude_query}"
            else:
                params['q_append'] = exclude_query
            print(f"🚫 Exclude domains: {', '.join(exclude_domains)}")

        # File type filter
        if file_type:
            params['fileType'] = file_type
            print(f"📄 File type: {file_type}")

        # Exact terms filter
        if exact_terms:
            # Add quotes around exact phrase
            exact_query = f'"{exact_terms}"'
            if 'q_append' in params:
                params['q_append'] += f" {exact_query}"
            else:
                params['q_append'] = exact_query
            print(f"💬 Exact terms: {exact_terms}")

        # Exclude terms
        if exclude_terms:
            exclude_query = " ".join([f"-{term}" for term in exclude_terms.split()])
            if 'q_append' in params:
                params['q_append'] += f" {exclude_query}"
            else:
                params['q_append'] = exclude_query
            print(f" Exclude terms: {exclude_terms}")

        return params

    def apply_filters_to_query(self, base_query: str, filter_params: Dict[str, str]) -> str:
        """
        Apply filter parameters to search query

        Args:
            base_query: Original search query
            filter_params: Filter parameters from build_filter_params

        Returns:
            Enhanced query string with filters
        """
        if 'q_append' in filter_params:
            return f"{base_query} {filter_params['q_append']}"
        return base_query

    def get_date_filter_description(self, date_filter: str) -> str:
        """Get human-readable description of date filter"""
        descriptions = {
            DateFilter.PAST_DAY: "Past 24 hours",
            DateFilter.PAST_WEEK: "Past week",
            DateFilter.PAST_MONTH: "Past month",
            DateFilter.PAST_YEAR: "Past year",
            DateFilter.ANY_TIME: "Any time"
        }
        return descriptions.get(date_filter, "Any time")

    def validate_domains(self, domains: List[str]) -> List[str]:
        """
        Validate and clean domain list

        Args:
            domains: List of domain strings

        Returns:
            List of validated domains
        """
        validated = []
        for domain in domains:
            # Remove protocol if present
            domain = domain.replace('http://', '').replace('https://', '')
            # Remove trailing slash
            domain = domain.rstrip('/')
            # Remove www. prefix (optional)
            if domain.startswith('www.'):
                domain = domain[4:]

            if domain:
                validated.append(domain)

        return validated

    def post_filter_sources(
        self,
        sources: List[Dict],
        include_domains: Optional[List[str]] = None,
        exclude_domains: Optional[List[str]] = None,
        min_date: Optional[datetime] = None,
        max_date: Optional[datetime] = None
    ) -> List[Dict]:
        """
        Apply additional filtering to sources after retrieval
        Useful for more precise filtering than API supports

        Args:
            sources: List of source dictionaries
            include_domains: Only include these domains
            exclude_domains: Exclude these domains
            min_date: Minimum publish date
            max_date: Maximum publish date

        Returns:
            Filtered list of sources
        """
        filtered = []

        for source in sources:
            url = source.get('url', '').lower()

            # Domain inclusion filter
            if include_domains:
                if not any(domain.lower() in url for domain in include_domains):
                    continue

            # Domain exclusion filter
            if exclude_domains:
                if any(domain.lower() in url for domain in exclude_domains):
                    continue

            # Date range filter
            if min_date or max_date:
                publish_date = source.get('publishDate')
                if publish_date:
                    try:
                        # Parse ISO date or other formats
                        if isinstance(publish_date, str):
                            pub_dt = datetime.fromisoformat(publish_date.replace('Z', '+00:00'))
                        else:
                            pub_dt = publish_date

                        if min_date and pub_dt < min_date:
                            continue
                        if max_date and pub_dt > max_date:
                            continue
                    except (ValueError, TypeError):
                        # If date parsing fails, include the source
                        pass

            filtered.append(source)

        return filtered

    def get_available_filters(self) -> Dict[str, List[str]]:
        """
        Get list of available filters for frontend

        Returns:
            Dictionary of filter types and their options
        """
        return {
            'date_filters': [e.value for e in DateFilter],
            'file_types': [e.value for e in FileType],
            'custom_options': [
                'include_domains',
                'exclude_domains',
                'exact_terms',
                'exclude_terms'
            ]
        }

    def get_popular_domain_filters(self) -> Dict[str, List[str]]:
        """
        Get commonly used domain filter presets

        Returns:
            Dictionary of preset names and domain lists
        """
        return {
            'academic': [
                'edu', 'gov', 'scholar.google.com', 'arxiv.org',
                'pubmed.ncbi.nlm.nih.gov', 'jstor.org', 'nature.com'
            ],
            'news': [
                'reuters.com', 'apnews.com', 'bbc.com', 'nytimes.com',
                'theguardian.com', 'washingtonpost.com', 'bloomberg.com'
            ],
            'tech': [
                'techcrunch.com', 'theverge.com', 'wired.com', 'arstechnica.com',
                'hacker-news.com', 'thenextweb.com'
            ],
            'docs': [
                'docs.python.org', 'developer.mozilla.org', 'docs.microsoft.com',
                'docs.google.com', 'documentation'
            ],
            'forums': [
                'stackoverflow.com', 'reddit.com', 'stackexchange.com',
                'discourse', 'github.com/issues', 'github.com/discussions'
            ]
        }
