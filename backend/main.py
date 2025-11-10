import os
import random
import string
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException, Query, Request, Depends, File, UploadFile, Form, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from google import genai
from google.genai import types
from dotenv import load_dotenv
import markdown
import re
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import redis
from sqlalchemy.orm import Session
from database import engine, get_db, Base
from models import Thread, Message, RateLimit
import requests
from urllib.parse import urlparse
import json
import asyncio
import base64
import io
from typing import Union
import html
from bs4 import BeautifulSoup
from citation_engine import CitationEngine
from grounding_engine import GroundingEngine
from rag_pipeline import RAGPipeline
from query_processor import QueryProcessor
from focus_modes import FocusModeManager
from search_filters import SearchFilterManager
from pro_search import ProSearchEngine
from file_security import FileValidator
from logger import logger, log_search, log_file_upload, log_api_call, log_error, log_database_operation

# Load environment variables
load_dotenv()

def validate_environment():
    """Validate required environment variables on startup"""
    required_vars = {
        'GOOGLE_API_KEY': 'Google AI API key is required. Get one at https://aistudio.google.com/apikey'
    }

    optional_vars = {
        'GOOGLE_SEARCH_ENGINE_ID': 'Google Custom Search Engine ID (will fall back to Gemini grounding)',
        'DATABASE_URL': 'Database URL (will fall back to SQLite)',
        'REDIS_HOST': 'Redis host (will fall back to in-memory storage)',
    }

    missing_required = []
    missing_optional = []

    # Check required variables
    for var, message in required_vars.items():
        if not os.getenv(var):
            missing_required.append(f" {var}: {message}")

    # Check optional variables
    for var, message in optional_vars.items():
        if not os.getenv(var):
            missing_optional.append(f"⚠️  {var}: {message}")

    # Log results
    if missing_required:
        logger.critical("Missing Required Environment Variables:")
        for msg in missing_required:
            logger.critical(f"  {msg}")
        logger.critical("Please add these to your .env file and restart the server.")
        raise ValueError("Missing required environment variables")

    if missing_optional:
        logger.warning("Optional Environment Variables Not Set:")
        for msg in missing_optional:
            logger.warning(f"  {msg}")

    logger.info(" Environment validation passed")

# Validate environment
validate_environment()

# Create database tables
Base.metadata.create_all(bind=engine)
logger.info(" Database tables created")

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Initialize FastAPI app
app = FastAPI(title="Zemixity Search API")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configure CORS - Load from environment variable
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3005")
ALLOWED_ORIGINS = [origin.strip() for origin in CORS_ORIGINS.split(",") if origin.strip()]

# Get additional origins from environment variable (for backward compatibility)
EXTRA_ORIGINS = os.getenv("ALLOWED_ORIGINS", "")
if EXTRA_ORIGINS:
    ALLOWED_ORIGINS.extend([origin.strip() for origin in EXTRA_ORIGINS.split(",") if origin.strip()])

logger.info(f" CORS configured for origins: {ALLOWED_ORIGINS}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add caching headers middleware
@app.middleware("http")
async def add_cache_headers(request: Request, call_next):
    response = await call_next(request)

    # Add cache headers for static content and health checks
    if request.url.path.startswith("/health") or request.url.path == "/":
        response.headers["Cache-Control"] = "public, max-age=60"
    # Don't cache API responses (search, threads, etc.) as they're dynamic
    elif request.url.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"

    return response

# Configure Gemini AI
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in environment variables")

# Google Custom Search API configuration
GOOGLE_SEARCH_ENGINE_ID = os.getenv("GOOGLE_SEARCH_ENGINE_ID")
CUSTOM_SEARCH_API_URL = os.getenv("GOOGLE_CUSTOM_SEARCH_URL", "https://www.googleapis.com/customsearch/v1")
SEARCH_RESULTS_LIMIT = int(os.getenv("SEARCH_RESULTS_LIMIT", "10"))

client = genai.Client(api_key=GOOGLE_API_KEY)

# Configure Google Search grounding tool (used in both search and follow-up)
grounding_tool = types.Tool(google_search=types.GoogleSearch())

# AI Model Configuration
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp")
GEMINI_TEMPERATURE = float(os.getenv("GEMINI_TEMPERATURE", "0.9"))
GEMINI_TOP_P = float(os.getenv("GEMINI_TOP_P", "1.0"))
GEMINI_TOP_K = int(os.getenv("GEMINI_TOP_K", "1"))
GEMINI_MAX_OUTPUT_TOKENS = int(os.getenv("GEMINI_MAX_OUTPUT_TOKENS", "2048"))

# Authentication & Authorization Configuration
BROWSER_API_KEY = os.getenv("BROWSER_API_KEY")  # Secret key from your browser
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY")  # Secret key for admin access
FREE_TIER_DAILY_LIMIT = int(os.getenv("FREE_TIER_DAILY_LIMIT", "5"))  # Free searches per day

if not BROWSER_API_KEY:
    logger.warning("⚠️  BROWSER_API_KEY not set - browser users will be treated as free tier")
if not ADMIN_API_KEY:
    logger.warning("⚠️  ADMIN_API_KEY not set - admin endpoints will be disabled")

# AI Model Configuration for Related Questions
GEMINI_RELATED_QUESTIONS_TEMPERATURE = float(os.getenv("GEMINI_RELATED_QUESTIONS_TEMPERATURE", "0.7"))
GEMINI_RELATED_QUESTIONS_MAX_TOKENS = int(os.getenv("GEMINI_RELATED_QUESTIONS_MAX_TOKENS", "256"))

# Rate Limiting Configuration
RATE_LIMIT_SEARCH = os.getenv("RATE_LIMIT_SEARCH", "10/minute")
RATE_LIMIT_FOLLOWUP = os.getenv("RATE_LIMIT_FOLLOWUP", "20/minute")
RATE_LIMIT_MULTIMODAL = os.getenv("RATE_LIMIT_MULTIMODAL", "10/minute")

# File Upload Configuration
MAX_UPLOAD_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", "10"))
MAX_UPLOAD_SIZE_BYTES = MAX_UPLOAD_SIZE_MB * 1024 * 1024

# Timeout Configuration
API_REQUEST_TIMEOUT = int(os.getenv("API_REQUEST_TIMEOUT", "10"))

# Server Configuration
SERVER_HOST = os.getenv("SERVER_HOST", "0.0.0.0")
SERVER_PORT = int(os.getenv("SERVER_PORT", "8080"))

logger.info(f" AI Model: {GEMINI_MODEL}")
logger.info(f" Rate Limits - Search: {RATE_LIMIT_SEARCH}, Follow-up: {RATE_LIMIT_FOLLOWUP}")
logger.info(f" Max Upload Size: {MAX_UPLOAD_SIZE_MB}MB")
logger.info(f" Free Tier Limit: {FREE_TIER_DAILY_LIMIT} searches/day")
logger.info(f" Server will run on {SERVER_HOST}:{SERVER_PORT}")

# Note: Session storage has been simplified to use database only
# Redis is no longer needed for conversation history


# ============================================================
# AUTHENTICATION & RATE LIMITING HELPERS
# ============================================================

def get_user_identifier(
    request: Request,
    browser_auth: str = None,
    user_id: str = None
) -> tuple[str, bool]:
    """
    Determine user identifier and tier

    Returns:
        tuple: (user_identifier, is_browser_user)
    """
    # Check if request is from your browser with valid auth
    if browser_auth and browser_auth == BROWSER_API_KEY and user_id:
        # Pro tier: Browser user
        return (user_id, True)
    else:
        # Free tier: Use IP address as identifier
        ip = request.client.host
        return (ip, False)


def check_rate_limit(ip_address: str, db: Session) -> bool:
    """
    Check if free tier user exceeded daily limit

    Returns:
        True if exceeded, False if within limit
    """
    today = datetime.now(timezone.utc).date()

    # Find or create rate limit record for today
    rate_limit = db.query(RateLimit).filter(
        RateLimit.ip_address == ip_address,
        RateLimit.date == today
    ).first()

    if rate_limit:
        # Check if limit exceeded
        if rate_limit.search_count >= FREE_TIER_DAILY_LIMIT:
            logger.warning(f"⚠️  Rate limit exceeded for IP: {ip_address} ({rate_limit.search_count}/{FREE_TIER_DAILY_LIMIT})")
            return True

    return False


def track_search(ip_address: str, db: Session):
    """Increment search count for free tier user"""
    try:
        today = datetime.now(timezone.utc).date()

        rate_limit = db.query(RateLimit).filter(
            RateLimit.ip_address == ip_address,
            RateLimit.date == today
        ).first()

        if rate_limit:
            rate_limit.search_count += 1
            rate_limit.updated_at = datetime.now(timezone.utc)
        else:
            rate_limit = RateLimit(
                ip_address=ip_address,
                search_count=1,
                date=today
            )
            db.add(rate_limit)

        db.commit()
        logger.debug(f"Tracked search for IP {ip_address}: {rate_limit.search_count}/{FREE_TIER_DAILY_LIMIT}")
    except Exception as e:
        db.rollback()
        logger.error(f" Failed to track search for {ip_address}: {e}")
        # Don't raise - tracking failure shouldn't break the search


# Pydantic models
class FollowUpRequest(BaseModel):
    sessionId: str
    query: str
    threadId: Optional[str] = None  # Add thread ID for persistence
    mode: Optional[str] = "web"  # Focus mode: web, academic, code, writing, news
    date_filter: Optional[str] = None  # Date filter: d1, w1, m1, y1
    file_type: Optional[str] = None  # File type filter
    include_domains: Optional[str] = None  # Comma-separated domains to include
    exclude_domains: Optional[str] = None  # Comma-separated domains to exclude


class Source(BaseModel):
    title: str
    url: str
    snippet: str
    image: Optional[str] = None  # Thumbnail/preview image
    favicon: Optional[str] = None  # Site logo/favicon
    displayUrl: Optional[str] = None  # Clean display URL (e.g., "nytimes.com")
    publishDate: Optional[str] = None  # When the page was published


class MessageResponse(BaseModel):
    id: str
    role: str
    content: str
    sources: List[Source]
    created_at: str


class SearchResponse(BaseModel):
    sessionId: str
    threadId: str  # Add thread ID to response
    summary: str
    sources: List[Source]
    relatedQuestions: List[str] = []  # Related questions
    conversation: List[MessageResponse] = []  # Full conversation history


class FollowUpResponse(BaseModel):
    summary: str
    sources: List[Source]
    relatedQuestions: List[str] = []  # Related questions
    conversation: List[MessageResponse] = []  # Full conversation history


class ThreadListResponse(BaseModel):
    id: str
    title: str
    session_id: str
    created_at: str
    updated_at: str
    is_pinned: bool
    message_count: int


class ThreadDetailResponse(BaseModel):
    id: str
    title: str
    session_id: str
    created_at: str
    updated_at: str
    is_pinned: bool
    messages: List[dict]


class UpdateThreadRequest(BaseModel):
    title: Optional[str] = None
    is_pinned: Optional[bool] = None


def format_response_to_markdown(text: str) -> str:
    """Format raw text into proper markdown and convert to HTML"""
    # Ensure consistent newlines
    processed_text = text.replace('\r\n', '\n')

    # Remove excessive asterisks and clean formatting
    # Remove standalone asterisks at line starts
    processed_text = re.sub(r'^\s*\*\s+\*\*', '**', processed_text, flags=re.MULTILINE)
    processed_text = re.sub(r'^\s*\*\s+', '', processed_text, flags=re.MULTILINE)

    # Clean up multiple asterisks patterns
    processed_text = re.sub(r'\*\*\s*\*\*([^*]+?)\*\*\s*\*\*', r'**\1**', processed_text)
    processed_text = re.sub(r'\* \*\*', '**', processed_text)
    processed_text = re.sub(r'\*\*\s+:', '**:', processed_text)

    # Convert "**Section:**" patterns to headings
    processed_text = re.sub(r'\*\*([A-Z][^*\n]+?):\*\*\s*', r'\n### \1\n', processed_text)

    # Process bullet points - keep only genuine list items
    # Convert patterns like "* item" or "- item" but not "* **bold**"
    lines = processed_text.split('\n')
    processed_lines = []
    in_list = False

    for line in lines:
        stripped = line.strip()
        # Detect genuine bullet points (not just formatting asterisks)
        if re.match(r'^[•●○-]\s+\w', stripped) or (stripped.startswith('* ') and not stripped.startswith('* **')):
            processed_lines.append('- ' + re.sub(r'^[•●○*-]\s+', '', stripped))
            in_list = True
        elif stripped and not stripped.startswith('#'):
            # Add spacing after lists
            if in_list:
                processed_lines.append('')
                in_list = False
            processed_lines.append(line)
        else:
            processed_lines.append(line)
            in_list = False

    processed_text = '\n'.join(processed_lines)

    # Clean up excessive blank lines
    processed_text = re.sub(r'\n{3,}', '\n\n', processed_text)

    # Convert markdown to HTML with proper extensions
    html = markdown.markdown(
        processed_text.strip(),
        extensions=['extra', 'nl2br', 'sane_lists', 'fenced_code']
    )

    return html


class StreamingMarkdownBuffer:
    def __init__(self):
        self.buffer = ""
        self.bold_count = 0
        self.italic_count = 0
        self.in_code_block = False
        self.in_link_text = False
        self.in_link_url = False
        self.link_buffer = ""
        self.list_pattern = re.compile(r'^[\s]*[\*\-•●○]\s+')

    def process_chunk(self, chunk_text: str) -> str:
        self.buffer += chunk_text
        output = ""

        i = 0
        while i < len(self.buffer):
            if i + 2 < len(self.buffer) and self.buffer[i:i+3] == '```':
                self.in_code_block = not self.in_code_block
                output += self.buffer[i:i+3]
                i += 3
                continue

            if self.in_code_block:
                output += self.buffer[i]
                i += 1
                continue

            if i + 1 < len(self.buffer) and self.buffer[i:i+2] == '**':
                self.bold_count += 1
                if self.bold_count % 2 == 1:
                    output += '<strong>'
                else:
                    output += '</strong>'
                i += 2
                continue

            if self.buffer[i] == '*' and not (i + 1 < len(self.buffer) and self.buffer[i+1] == '*'):
                if i == 0 or self.buffer[i-1] in ' \n\t':
                    self.italic_count += 1
                    if self.italic_count % 2 == 1:
                        output += '<em>'
                    else:
                        output += '</em>'
                    i += 1
                    continue
                else:
                    output += self.buffer[i]
                    i += 1
                    continue

            if self.buffer[i] == '[' and not self.in_link_text:
                self.in_link_text = True
                self.link_buffer = '['
                i += 1
                continue

            if self.in_link_text:
                self.link_buffer += self.buffer[i]
                if self.buffer[i] == ']' and i + 1 < len(self.buffer) and self.buffer[i+1] == '(':
                    self.in_link_text = False
                    self.in_link_url = True
                    i += 2
                    self.link_buffer += '('
                    continue
                elif self.buffer[i] == ']':
                    self.in_link_text = False
                    output += self.link_buffer
                    self.link_buffer = ""
                i += 1
                continue

            if self.in_link_url:
                self.link_buffer += self.buffer[i]
                if self.buffer[i] == ')':
                    match = re.match(r'\[([^\]]+)\]\(([^\)]+)\)', self.link_buffer)
                    if match:
                        text, url = match.groups()
                        output += f'<a href="{html.escape(url)}" target="_blank" rel="noopener noreferrer">{html.escape(text)}</a>'
                    else:
                        output += self.link_buffer
                    self.link_buffer = ""
                    self.in_link_url = False
                i += 1
                continue

            if self.buffer[i] == '\n':
                line_start = output.rfind('\n') + 1
                current_line = output[line_start:]

                if current_line.strip() and not current_line.strip().startswith('<'):
                    if self.list_pattern.match(current_line):
                        cleaned = self.list_pattern.sub('', current_line)
                        output = output[:line_start] + '<li>' + cleaned + '</li>\n'
                    else:
                        output = output[:line_start] + '<p>' + current_line + '</p>\n'
                else:
                    output += '\n'
            else:
                output += self.buffer[i]

            i += 1

        self.buffer = ""

        if self.in_link_text or self.in_link_url:
            self.buffer = self.link_buffer
            return output

        return output

    def flush(self) -> str:
        remaining = self.buffer
        self.buffer = ""
        self.bold_count = 0
        self.italic_count = 0
        self.in_code_block = False
        self.in_link_text = False
        self.in_link_url = False
        self.link_buffer = ""

        if remaining:
            return html.escape(remaining)
        return ""


def extract_sources(response) -> List[Source]:
    """Extract sources from grounding metadata"""
    source_map = {}

    try:
        # Get grounding metadata from response
        if hasattr(response, 'candidates') and response.candidates:
            candidate = response.candidates[0]
            if hasattr(candidate, 'grounding_metadata') and candidate.grounding_metadata:
                metadata = candidate.grounding_metadata

                chunks = metadata.grounding_chunks if hasattr(metadata, 'grounding_chunks') and metadata.grounding_chunks else []
                supports = metadata.grounding_supports if hasattr(metadata, 'grounding_supports') and metadata.grounding_supports else []

                for index, chunk in enumerate(chunks):
                    if hasattr(chunk, 'web') and chunk.web:
                        uri = chunk.web.uri if hasattr(chunk.web, 'uri') else None
                        title = chunk.web.title if hasattr(chunk.web, 'title') else None

                        if uri and title and uri not in source_map:
                            # Find snippets that reference this chunk
                            snippets = []
                            for support in supports:
                                if hasattr(support, 'grounding_chunk_indices'):
                                    if index in support.grounding_chunk_indices:
                                        if hasattr(support, 'segment') and hasattr(support.segment, 'text'):
                                            snippets.append(support.segment.text)

                            source_map[uri] = Source(
                                title=title,
                                url=uri,
                                snippet=' '.join(snippets) if snippets else ''
                            )
    except Exception as e:
        logger.error(f"Error extracting sources: {e}")

    return list(source_map.values())


def extract_sources_with_citations(response) -> tuple[List[Source], Dict[str, List[int]]]:
    """Extract sources from grounding metadata AND create citation mapping"""
    source_list = []
    citation_map = {}  # {segment_text: [source_indices]}
    source_index_map = {}  # {uri: index} to track source positions

    try:
        # Get grounding metadata from response
        if hasattr(response, 'candidates') and response.candidates:
            candidate = response.candidates[0]
            if hasattr(candidate, 'grounding_metadata') and candidate.grounding_metadata:
                metadata = candidate.grounding_metadata

                chunks = metadata.grounding_chunks if hasattr(metadata, 'grounding_chunks') and metadata.grounding_chunks else []
                supports = metadata.grounding_supports if hasattr(metadata, 'grounding_supports') and metadata.grounding_supports else []

                # First pass: Build source list
                for chunk_index, chunk in enumerate(chunks):
                    if hasattr(chunk, 'web') and chunk.web:
                        uri = chunk.web.uri if hasattr(chunk.web, 'uri') else None
                        title = chunk.web.title if hasattr(chunk.web, 'title') else None

                        if uri and title and uri not in source_index_map:
                            source_index = len(source_list)
                            source_index_map[uri] = source_index
                            source_list.append(Source(
                                title=title,
                                url=uri,
                                snippet=''
                            ))

                # Second pass: Build citation map
                for support in supports:
                    if hasattr(support, 'segment') and hasattr(support.segment, 'text'):
                        segment_text = support.segment.text
                        if hasattr(support, 'grounding_chunk_indices') and support.grounding_chunk_indices:
                            # Map chunk indices to source indices
                            source_indices = []
                            for chunk_idx in support.grounding_chunk_indices:
                                if chunk_idx < len(chunks):
                                    chunk = chunks[chunk_idx]
                                    if hasattr(chunk, 'web') and chunk.web and hasattr(chunk.web, 'uri'):
                                        uri = chunk.web.uri
                                        if uri in source_index_map:
                                            source_idx = source_index_map[uri]
                                            if source_idx not in source_indices:
                                                source_indices.append(source_idx)

                            if source_indices:
                                # Store 1-indexed citations for display
                                citation_map[segment_text] = [idx + 1 for idx in sorted(source_indices)]

    except Exception as e:
        logger.error(f"Error extracting sources with citations: {e}")
        import traceback
        traceback.print_exc()

    return source_list, citation_map


def inject_inline_citations(text: str, citation_map: Dict[str, List[int]]) -> str:
    """Inject [1], [2] inline citations into text based on citation map"""
    if not citation_map:
        return text

    # Sort segments by length (longest first) to avoid partial replacements
    sorted_segments = sorted(citation_map.items(), key=lambda x: len(x[0]), reverse=True)

    for segment_text, source_indices in sorted_segments:
        if segment_text in text and source_indices:
            # Create citation string like [1] or [1,2,3]
            citations = ''.join(f'[{idx}]' for idx in source_indices)
            # Replace only first occurrence to avoid duplicates
            text = text.replace(segment_text, f"{segment_text}{citations}", 1)

    return text


def generate_session_id() -> str:
    """Generate a random session ID"""
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=7))


def generate_thread_title(query: str) -> str:
    """Generate a thread title from the first query"""
    # Truncate to 100 chars for readability
    if len(query) <= 100:
        return query
    return query[:97] + "..."


def generate_related_questions(query: str, summary: str) -> List[str]:
    """Generate AI-powered related questions based on the query and answer"""
    try:
        # Create a prompt for Gemini to generate contextual follow-up questions
        prompt = f"""Based on this question and answer, suggest 3-4 relevant follow-up questions that a user might want to ask next.

Original Question: {query}

Answer Summary: {summary[:500]}...

Generate ONLY follow-up questions that are:
1. Directly related to the topic
2. Natural next steps in the conversation
3. Not repetitive of the original question
4. Contextually relevant to the answer provided

If no good follow-up questions can be generated, return an empty list.

Format: Return ONLY the questions, one per line, without numbering or bullet points."""

        # Use Gemini for related questions
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=GEMINI_RELATED_QUESTIONS_TEMPERATURE,
                max_output_tokens=GEMINI_RELATED_QUESTIONS_MAX_TOKENS,
            )
        )

        # Parse the response
        questions_text = response.text.strip()

        # Split by newlines and clean up
        questions = [q.strip() for q in questions_text.split('\n') if q.strip()]

        # Remove numbering if present (1., 2., -, *, etc.)
        questions = [re.sub(r'^[\d\.\-\*\)\]\s]+', '', q).strip() for q in questions]

        # Filter out empty or very short questions
        questions = [q for q in questions if len(q) > 10]

        # Return top 4 questions
        return questions[:4]

    except Exception as e:
        logger.error(f"Error generating related questions: {e}")
        # Return empty list if AI generation fails
        return []


def is_conversational_query(query: str) -> bool:
    """
    Detect if a query is conversational (greetings, jokes, simple chat)
    that doesn't need web search sources
    """
    query_lower = query.lower().strip()

    # Conversational patterns
    conversational_patterns = [
        # Greetings
        r'^(hi|hello|hey|howdy|greetings|good morning|good afternoon|good evening)[\s,!.]*$',
        r'^(hi|hello|hey)\s+(there|friend|buddy)',
        r'^how\s+(are|r)\s+you',
        r'^what\'?s\s+up',
        r'^sup\b',

        # Jokes and fun
        r'tell\s+(me\s+)?a\s+joke',
        r'make\s+me\s+laugh',
        r'say\s+something\s+funny',

        # Simple questions about the AI
        r'^who\s+are\s+you',
        r'^what\s+are\s+you',
        r'^what\s+can\s+you\s+do',
        r'^help\s*$',

        # Thank you / goodbye
        r'^(thanks|thank\s+you|thx|ty)[\s!.]*$',
        r'^(bye|goodbye|see\s+you|later)[\s!.]*$',
    ]

    # Check if query matches any conversational pattern
    for pattern in conversational_patterns:
        if re.search(pattern, query_lower):
            return True

    # Very short queries (1-2 words) without question words might be conversational
    words = query_lower.split()
    if len(words) <= 2 and not any(qw in words for qw in ['what', 'when', 'where', 'who', 'why', 'how', 'which']):
        # Check if it's likely a casual greeting/chat
        casual_words = ['hi', 'hello', 'hey', 'yo', 'sup', 'hola', 'thanks', 'bye']
        if any(word in casual_words for word in words):
            return True

    return False


def fetch_google_custom_search(
    query: str,
    num_results: int = 10,
    date_filter: Optional[str] = None,
    file_type: Optional[str] = None,
    filter_params: Optional[Dict] = None
) -> List[Source]:
    """Fetch search results from Google Custom Search API with rich metadata and filters"""
    if not GOOGLE_SEARCH_ENGINE_ID:
        logger.warning("⚠️  Google Custom Search Engine ID not configured, falling back to Gemini grounding")
        return []

    try:
        params = {
            'key': GOOGLE_API_KEY,
            'cx': GOOGLE_SEARCH_ENGINE_ID,
            'q': query,
            'num': num_results,
        }

        # Apply date filter
        if date_filter:
            params['dateRestrict'] = date_filter

        # Apply file type filter
        if file_type:
            params['fileType'] = file_type

        # Apply additional filter params
        if filter_params:
            params.update(filter_params)

        response = requests.get(CUSTOM_SEARCH_API_URL, params=params, timeout=API_REQUEST_TIMEOUT)
        response.raise_for_status()
        data = response.json()

        sources = []
        items = data.get('items', [])

        for item in items:
            # Extract basic info
            title = item.get('title', '')
            url = item.get('link', '')
            snippet = item.get('snippet', '')

            # Extract image (from pagemap or og:image)
            image = None
            pagemap = item.get('pagemap', {})
            if 'cse_image' in pagemap and len(pagemap['cse_image']) > 0:
                image = pagemap['cse_image'][0].get('src')
            elif 'metatags' in pagemap and len(pagemap['metatags']) > 0:
                metatags = pagemap['metatags'][0]
                image = metatags.get('og:image') or metatags.get('twitter:image')

            # Extract favicon
            parsed_url = urlparse(url)
            domain = parsed_url.netloc
            favicon = f"https://www.google.com/s2/favicons?domain={domain}&sz=64"

            # Extract display URL (clean domain)
            display_url = domain.replace('www.', '')

            # Extract publish date (if available)
            publish_date = None
            if 'pagemap' in item and 'metatags' in item['pagemap']:
                for metatag in item['pagemap']['metatags']:
                    publish_date = (
                        metatag.get('article:published_time') or
                        metatag.get('datePublished') or
                        metatag.get('og:updated_time')
                    )
                    if publish_date:
                        break

            sources.append(Source(
                title=title,
                url=url,
                snippet=snippet,
                image=image,
                favicon=favicon,
                displayUrl=display_url,
                publishDate=publish_date
            ))

        logger.info(f" Fetched {len(sources)} sources from Google Custom Search API")
        return sources

    except requests.exceptions.RequestException as e:
        logger.error(f" Error fetching from Custom Search API: {e}")
        return []
    except Exception as e:
        logger.error(f" Unexpected error in Custom Search: {e}")
        return []


@app.get("/")
async def root():
    return {"message": "Gemini Search API is running"}


@app.get("/health")
@app.get("/api/health")
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint for monitoring"""
    from sqlalchemy import text
    health_status = {
        "status": "healthy",
        "version": "0.1.0",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    # Check database connection
    try:
        db.execute(text("SELECT 1"))
        health_status["database"] = "connected"
    except Exception as e:
        health_status["database"] = f"error: {str(e)}"
        health_status["status"] = "unhealthy"

    # Check AI API availability
    if GOOGLE_API_KEY:
        health_status["google_api"] = "configured"
    else:
        health_status["google_api"] = "missing"
        health_status["status"] = "unhealthy"

    # Check Custom Search API
    if GOOGLE_SEARCH_ENGINE_ID:
        health_status["custom_search"] = "configured"
    else:
        health_status["custom_search"] = "not configured (using Gemini grounding)"

    return health_status


@app.get("/api/filters")
async def get_available_filters():
    """Get available search filters and focus modes for frontend"""
    filter_manager = SearchFilterManager()
    focus_manager = FocusModeManager()

    return {
        "focus_modes": focus_manager.get_available_modes(),
        "filters": filter_manager.get_available_filters(),
        "domain_presets": filter_manager.get_popular_domain_filters(),
        "date_filters": {
            "any": "Any time",
            "d1": "Past 24 hours",
            "w1": "Past week",
            "m1": "Past month",
            "y1": "Past year"
        }
    }


# Non-streaming search endpoint has been removed - use /api/search/stream instead


@app.get("/api/search/stream")
@limiter.limit(RATE_LIMIT_SEARCH)
async def search_stream(
    request: Request,
    q: str = Query(..., description="Search query"),
    mode: str = Query("web", description="Focus mode: web, academic, code, writing, news"),
    pro_search: bool = Query(False, description="Enable Pro Search for deeper, multi-step research"),
    date_filter: Optional[str] = Query(None, description="Date filter: d1, w1, m1, y1, or any"),
    file_type: Optional[str] = Query(None, description="File type: pdf, doc, docx, etc."),
    include_domains: Optional[str] = Query(None, description="Comma-separated domains to include"),
    exclude_domains: Optional[str] = Query(None, description="Comma-separated domains to exclude"),
    browser_auth: Optional[str] = Header(None, alias="X-Browser-Auth", description="Browser authentication key"),
    user_id: Optional[str] = Header(None, alias="X-User-ID", description="Browser user ID for pro tier"),
    db: Session = Depends(get_db)
):
    """Streaming search endpoint with advanced filters and Pro Search - returns SSE events with progressive content"""

    async def generate():
        # Check authentication and rate limits
        user_identifier, is_browser_user = get_user_identifier(request, browser_auth, user_id)

        # Free tier: check rate limit
        if not is_browser_user:
            if check_rate_limit(user_identifier, db):
                error_msg = f"Daily search limit ({FREE_TIER_DAILY_LIMIT} searches) exceeded. Please try again tomorrow."
                yield f"data: {json.dumps({'type': 'error', 'message': error_msg})}\n\n"
                return

        logger.info(f"🔐 User: {'Browser Pro' if is_browser_user else 'Free tier'} | ID: {user_identifier}")
        try:
            # Initialize engines
            citation_engine = CitationEngine()
            grounding_engine = GroundingEngine()
            rag_pipeline = RAGPipeline()
            query_processor = QueryProcessor()
            focus_manager = FocusModeManager()
            filter_manager = SearchFilterManager()
            pro_engine = ProSearchEngine()

            # Get focus mode
            focus_mode = focus_manager.get_mode(mode)
            logger.info(f"🎯 Using focus mode: {mode}")

            # Check if Pro Search should be used
            use_pro_search = pro_search or pro_engine.should_use_pro_search(q, user_requested=pro_search)
            if use_pro_search:
                logger.info(f"🚀 Pro Search activated for complex query")
                yield f"data: {json.dumps({'type': 'status', 'message': '🚀 Pro Search activated - Deep research mode'})}\n\n"
                await asyncio.sleep(0.01)

            # Process search filters
            include_domains_list = [d.strip() for d in include_domains.split(',')] if include_domains else None
            exclude_domains_list = [d.strip() for d in exclude_domains.split(',')] if exclude_domains else None

            if include_domains_list:
                include_domains_list = filter_manager.validate_domains(include_domains_list)
            if exclude_domains_list:
                exclude_domains_list = filter_manager.validate_domains(exclude_domains_list)

            # Build filter parameters
            filter_params = filter_manager.build_filter_params(
                date_filter=date_filter,
                include_domains=include_domains_list,
                exclude_domains=exclude_domains_list,
                file_type=file_type
            )

            # Log active filters
            if date_filter:
                logger.info(f"🔍 Filter: {filter_manager.get_date_filter_description(date_filter)}")
            if file_type:
                logger.info(f"📄 Filter: File type = {file_type}")
            if include_domains_list:
                logger.info(f"🌐 Filter: Including domains = {include_domains_list}")
            if exclude_domains_list:
                logger.info(f"🚫 Filter: Excluding domains = {exclude_domains_list}")

            # Validate query
            if not q:
                yield f"data: {json.dumps({'type': 'error', 'message': 'Query parameter q is required'})}\n\n"
                return

            # Process query to understand intent and enhance
            query_analysis = query_processor.process_query(q)
            logger.info(f"📝 Query analysis: intent={query_analysis['intent']}, "
                  f"keywords={query_analysis['keywords'][:5]}")
            logger.info(f"🔍 Enhanced query: {query_analysis['enhanced_query']}")

            # Generate session and thread IDs
            session_id = generate_session_id()
            yield f"data: {json.dumps({'type': 'session_id', 'sessionId': session_id})}\n\n"
            await asyncio.sleep(0.01)

            # Check for existing thread (prevent duplicates on refresh)
            recent_time = datetime.now(timezone.utc) - timedelta(minutes=5)
            existing_thread = db.query(Thread).join(Message).filter(
                Message.role == 'user',
                Message.content == q,
                Thread.created_at >= recent_time,
                Thread.user_id == user_identifier  # CRITICAL: Ensure user can only reuse their own threads
            ).order_by(Thread.created_at.desc()).first()

            if existing_thread:
                new_thread = existing_thread
                logger.info(f"♻️  Reusing existing thread {existing_thread.id}")
                yield f"data: {json.dumps({'type': 'thread_id', 'threadId': new_thread.id})}\n\n"
            else:
                # Create new thread
                thread_title = generate_thread_title(q)
                new_thread = Thread(
                    title=thread_title,
                    session_id=session_id,
                    user_id=user_identifier,
                    is_browser_user=is_browser_user
                )
                db.add(new_thread)
                db.flush()
                logger.info(f" Created new thread {new_thread.id}")
                yield f"data: {json.dumps({'type': 'thread_id', 'threadId': new_thread.id})}\n\n"

            await asyncio.sleep(0.01)

            # STEP 1: Fetch sources FIRST (for proper grounding)
            yield f"data: {json.dumps({'type': 'status', 'message': 'Searching web...'})}\n\n"
            await asyncio.sleep(0.01)

            sources = []
            sources_dict = []
            total_reviewed = 0  # Initialize to handle API failures gracefully

            if not is_conversational_query(q):
                # Use enhanced query for better search results
                search_query = query_analysis['enhanced_query']

                # Apply filter modifications to query (domain filters, etc.)
                if 'q_append' in filter_params:
                    search_query = filter_manager.apply_filters_to_query(search_query, filter_params)

                # Get search hints based on query intent
                search_hints = query_processor.get_search_hints(
                    query_analysis['intent'],
                    query_analysis['temporal_context']
                )

                logger.debug(f"🎯 Search hints: {search_hints}")

                # Fetch sources before generating response with enhanced query and filters
                # Google API free tier allows max 10 results per query
                num_sources_to_fetch = 10
                raw_sources = fetch_google_custom_search(
                    search_query,
                    num_results=num_sources_to_fetch,
                    date_filter=filter_params.get('dateRestrict'),
                    file_type=filter_params.get('fileType')
                )

                if use_pro_search:
                    logger.info(f"📚 Pro Search: Fetching {num_sources_to_fetch} sources for comprehensive research")

                if raw_sources and len(raw_sources) > 0:
                    logger.info(f" Fetched {len(raw_sources)} raw sources from Custom Search API")

                    # Convert to dicts for processing
                    raw_sources_dict = []
                    for source in raw_sources:
                        if hasattr(source, 'model_dump'):
                            raw_sources_dict.append(source.model_dump())
                        else:
                            raw_sources_dict.append({
                                'title': source.title,
                                'url': source.url,
                                'snippet': source.snippet,
                                'image': source.image if hasattr(source, 'image') else None,
                                'favicon': source.favicon if hasattr(source, 'favicon') else None,
                                'displayUrl': source.displayUrl if hasattr(source, 'displayUrl') else None,
                                'publishDate': source.publishDate if hasattr(source, 'publishDate') else None,
                            })

                    # Apply RAG pipeline: deduplicate, rank, and filter
                    deduped_sources = rag_pipeline.deduplicate_sources(raw_sources_dict)
                    logger.info(f" Deduplicated to {len(deduped_sources)} unique sources")

                    # Pro Search uses more sources for comprehensive answers
                    max_sources_to_use = 15 if use_pro_search else 10

                    ranked_sources, total_reviewed = rag_pipeline.process_sources(
                        deduped_sources,
                        q,
                        max_sources=max_sources_to_use
                    )

                    # Filter out very low quality sources (lower threshold for Pro Search)
                    min_quality_score = 0.15 if use_pro_search else 0.2
                    filtered_sources = rag_pipeline.filter_low_quality_sources(ranked_sources, min_score=min_quality_score)

                    sources_dict = filtered_sources
                    sources = [Source(**src) for src in sources_dict]

                    logger.info(f" Ranked and filtered to {len(sources)} high-quality sources")
                    logger.info(f"📊 Total sources reviewed: {total_reviewed}")

                    if use_pro_search:
                        logger.info(f"📚 Pro Search: Using {len(sources)} sources for comprehensive synthesis")

                status_msg = f'🚀 Pro Search: Reviewed {total_reviewed} sources, selected {len(sources)} for deep analysis' if use_pro_search else f'Reviewed {total_reviewed} sources, selected {len(sources)} best matches'
                yield f"data: {json.dumps({'type': 'status', 'message': status_msg})}\n\n"
                await asyncio.sleep(0.01)

            # Apply focus mode to sources if not default web mode
            if mode != 'web' and sources_dict:
                logger.info(f"🎯 Applying {mode} focus mode to sources")
                sources_dict = focus_manager._filter_sources_by_mode(sources_dict, focus_mode)
                sources = [Source(**src) for src in sources_dict]
                logger.info(f" Focus mode applied, {len(sources_dict)} sources after filtering")

            # STEP 2: Build grounded prompt with sources
            base_prompt = grounding_engine.build_grounded_prompt(
                query=q,
                sources=sources_dict if sources_dict else None
            )

            # Apply focus mode prompt modifier
            if mode != 'web':
                formatted_query = base_prompt + "\n\n" + focus_mode.get_prompt_modifier()
                logger.info(f" Applied {mode} mode prompt modifier")
            else:
                formatted_query = base_prompt

            # Apply Pro Search enhancement to prompt
            if use_pro_search:
                pro_enhancement = """
\n\n🚀 PRO SEARCH MODE - Enhanced Requirements:
1. Provide a COMPREHENSIVE, in-depth answer that covers multiple angles
2. Organize your response with clear section headings (use ## for main sections)
3. Include MORE details and context than a standard search would
4. Address nuances, implications, and related considerations
5. Synthesize information from ALL available sources
6. Provide a brief conclusion or summary at the end
7. Use proper markdown formatting for better readability

Make this answer notably more thorough and insightful than a standard response.
"""
                formatted_query += pro_enhancement
                logger.info(f"🚀 Applied Pro Search enhancement to prompt")

            # Configure Gemini (without grounding tool since we're doing it manually)
            config = types.GenerateContentConfig(
                temperature=GEMINI_TEMPERATURE,
                top_p=GEMINI_TOP_P,
                top_k=GEMINI_TOP_K,
                max_output_tokens=GEMINI_MAX_OUTPUT_TOKENS,
            )

            # STEP 3: Stream the grounded response
            full_text = ""
            markdown_buffer = StreamingMarkdownBuffer()

            logger.info(f"🔄 Starting streaming for query: {q}")

            for chunk in client.models.generate_content_stream(
                model=GEMINI_MODEL,
                contents=formatted_query,
                config=config
            ):
                if hasattr(chunk, 'text') and chunk.text:
                    full_text += chunk.text
                    formatted_chunk = markdown_buffer.process_chunk(chunk.text)
                    if formatted_chunk:
                        yield f"data: {json.dumps({'type': 'token', 'content': formatted_chunk})}\n\n"
                    await asyncio.sleep(0.01)

                # Keep last chunk for metadata
                full_response = chunk

            remaining = markdown_buffer.flush()
            if remaining:
                yield f"data: {json.dumps({'type': 'token', 'content': remaining})}\n\n"

            logger.info(f" Streaming complete. Total length: {len(full_text)}")

            # STEP 4: Validate grounding and inject citations
            yield f"data: {json.dumps({'type': 'status', 'message': 'Processing citations...'})}\n\n"
            await asyncio.sleep(0.01)

            # Format initial text to markdown/HTML
            formatted_text_no_citations = format_response_to_markdown(full_text)

            # Validate response grounding if sources were used
            if sources_dict:
                validation = grounding_engine.validate_response_grounding(
                    full_text,
                    sources_dict
                )
                logger.info(f"🔍 Grounding validation: score={validation['grounding_score']:.2f}, "
                      f"appears_grounded={validation['appears_grounded']}")

                if not validation['appears_grounded']:
                    logger.warning(f"⚠️  Warning: Response may not be well-grounded (score: {validation['grounding_score']:.2f})")

                if validation['potential_hallucinations']:
                    logger.warning(f"⚠️  Potential hallucination phrases: {validation['potential_hallucinations']}")

            # Inject citations using our citation engine
            if sources:
                formatted_text, all_sources = citation_engine.inject_citations(
                    formatted_text_no_citations,
                    sources_dict
                )

                # Display all sources searched (not just cited ones) for transparency
                sources = [Source(**src) for src in all_sources]
                logger.info(f" Processed {len(all_sources)} sources with citations")
            else:
                formatted_text = formatted_text_no_citations
                logger.info("💬 No sources to cite (conversational query)")

            # Save to database (only if new thread)
            if not existing_thread:
                try:
                    user_message = Message(
                        thread_id=new_thread.id,
                        role='user',
                        content=q,
                        sources=None
                    )
                    db.add(user_message)

                    assistant_message = Message(
                        thread_id=new_thread.id,
                        role='assistant',
                        content=formatted_text,
                        sources=[s.model_dump() for s in sources] if sources else []
                    )
                    db.add(assistant_message)
                    db.commit()
                    logger.info(f" Saved messages to thread {new_thread.id}")
                except Exception as e:
                    db.rollback()
                    logger.error(f" Failed to save messages to database: {e}")
                    # Continue execution - the search already completed, just logging failed

            # Send sources
            yield f"data: {json.dumps({'type': 'sources', 'sources': [s.model_dump() for s in sources]})}\n\n"
            await asyncio.sleep(0.01)

            # Conversation history is now stored in database only
            # No need for separate session storage

            # Generate related questions
            yield f"data: {json.dumps({'type': 'status', 'message': 'Generating suggestions...'})}\n\n"
            related_questions = generate_related_questions(q, formatted_text)
            yield f"data: {json.dumps({'type': 'related_questions', 'questions': related_questions})}\n\n"
            await asyncio.sleep(0.01)

            # Track search for free tier users
            if not is_browser_user:
                track_search(user_identifier, db)
                logger.info(f"📊 Free tier search tracked for {user_identifier}")

            # Send completion
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
            logger.info(f" Streaming session {session_id} completed")

        except Exception as e:
            logger.error(f" Streaming error: {e}")
            import traceback
            traceback.print_exc()
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )


# Non-streaming follow-up endpoint has been removed - use /api/follow-up/stream instead


@app.post("/api/follow-up/stream")
@limiter.limit(RATE_LIMIT_FOLLOWUP)
async def follow_up_stream(
    request: Request,
    body: FollowUpRequest,
    browser_auth: Optional[str] = Header(None, alias="X-Browser-Auth"),
    user_id: Optional[str] = Header(None, alias="X-User-ID"),
    db: Session = Depends(get_db)
):
    """Streaming follow-up endpoint - continues existing chat session with streaming"""

    async def generate():
        # Check authentication and rate limits
        user_identifier, is_browser_user = get_user_identifier(request, browser_auth, user_id)

        # Free tier: check rate limit
        if not is_browser_user:
            if check_rate_limit(user_identifier, db):
                error_msg = f"Daily search limit ({FREE_TIER_DAILY_LIMIT} searches) exceeded. Please try again tomorrow."
                yield f"data: {json.dumps({'type': 'error', 'message': error_msg})}\n\n"
                return

        logger.info(f"🔐 Follow-up from: {'Browser Pro' if is_browser_user else 'Free tier'} | ID: {user_identifier}")

        try:
            # Initialize engines
            citation_engine = CitationEngine()
            grounding_engine = GroundingEngine()
            rag_pipeline = RAGPipeline()
            query_processor = QueryProcessor()
            focus_manager = FocusModeManager()

            # Get focus mode
            focus_mode = focus_manager.get_mode(body.mode)
            logger.info(f"🎯 Using focus mode for follow-up: {body.mode}")

            # Initialize filter manager and process filters
            filter_manager = SearchFilterManager()

            # Process search filters
            include_domains_list = [d.strip() for d in body.include_domains.split(',')] if body.include_domains else None
            exclude_domains_list = [d.strip() for d in body.exclude_domains.split(',')] if body.exclude_domains else None

            if include_domains_list:
                include_domains_list = filter_manager.validate_domains(include_domains_list)
            if exclude_domains_list:
                exclude_domains_list = filter_manager.validate_domains(exclude_domains_list)

            # Build filter parameters
            filter_params = filter_manager.build_filter_params(
                date_filter=body.date_filter,
                include_domains=include_domains_list,
                exclude_domains=exclude_domains_list,
                file_type=body.file_type
            )

            # Validate inputs
            if not body.sessionId or not body.query:
                yield f"data: {json.dumps({'type': 'error', 'message': 'Both sessionId and query are required'})}\n\n"
                return

            # Process query
            query_analysis = query_processor.process_query(body.query)
            logger.info(f"📝 Follow-up query analysis: intent={query_analysis['intent']}")

            # Get conversation history from database using session_id
            thread = None
            if body.threadId:
                # CRITICAL: Verify thread ownership
                thread = db.query(Thread).filter(
                    Thread.id == body.threadId,
                    Thread.user_id == user_identifier
                ).first()
            elif body.sessionId:
                # Try to find thread by session_id - CRITICAL: Verify ownership
                thread = db.query(Thread).filter(
                    Thread.session_id == body.sessionId,
                    Thread.user_id == user_identifier
                ).order_by(Thread.created_at.desc()).first()

            if not thread:
                yield f"data: {json.dumps({'type': 'error', 'message': 'Thread not found. Please start a new search.'})}\n\n"
                return

            # Build conversation history from database messages
            messages = db.query(Message).filter(Message.thread_id == thread.id).order_by(Message.created_at.asc()).all()

            if not messages:
                yield f"data: {json.dumps({'type': 'error', 'message': 'No conversation history found'})}\n\n"
                return

            # Convert to Gemini format for conversation history
            conversation_history = []
            context_summary = []

            for msg in messages:
                if msg.role == 'user':
                    conversation_history.append({"role": "user", "parts": [{"text": msg.content}]})
                    context_summary.append(f"User: {msg.content}")
                else:
                    # Extract plain text from HTML for assistant messages
                    plain_text = BeautifulSoup(msg.content, 'html.parser').get_text()
                    conversation_history.append({"role": "model", "parts": [{"text": plain_text}]})
                    context_summary.append(f"Assistant: {plain_text[:200]}...")  # Summary for context

            conversation_context = "\n".join(context_summary[-4:])  # Last 2 exchanges
            logger.info(f" Loaded {len(conversation_history)} messages from thread {thread.id}")

            # STEP 1: Fetch sources FIRST
            yield f"data: {json.dumps({'type': 'status', 'message': 'Searching for new information...'})}\n\n"
            await asyncio.sleep(0.01)

            sources = []
            sources_dict = []
            total_reviewed = 0  # Initialize to handle API failures gracefully

            if not is_conversational_query(body.query):
                # Use enhanced query for better search
                search_query = query_analysis['enhanced_query']

                # Apply filter modifications to query
                if 'q_append' in filter_params:
                    search_query = filter_manager.apply_filters_to_query(search_query, filter_params)

                # Fetch sources before generating response with filters
                # Google API free tier allows max 10 results per query
                raw_sources = fetch_google_custom_search(
                    search_query,
                    num_results=10,
                    date_filter=filter_params.get('dateRestrict'),
                    file_type=filter_params.get('fileType')
                )

                if raw_sources and len(raw_sources) > 0:
                    logger.info(f" Fetched {len(raw_sources)} raw sources for follow-up")

                    # Convert to dicts for processing
                    raw_sources_dict = []
                    for source in raw_sources:
                        if hasattr(source, 'model_dump'):
                            raw_sources_dict.append(source.model_dump())
                        else:
                            raw_sources_dict.append({
                                'title': source.title,
                                'url': source.url,
                                'snippet': source.snippet,
                                'image': source.image if hasattr(source, 'image') else None,
                                'favicon': source.favicon if hasattr(source, 'favicon') else None,
                                'displayUrl': source.displayUrl if hasattr(source, 'displayUrl') else None,
                                'publishDate': source.publishDate if hasattr(source, 'publishDate') else None,
                            })

                    # Apply RAG pipeline
                    deduped_sources = rag_pipeline.deduplicate_sources(raw_sources_dict)
                    ranked_sources, total_reviewed = rag_pipeline.process_sources(
                        deduped_sources,
                        body.query,
                        max_sources=10
                    )
                    filtered_sources = rag_pipeline.filter_low_quality_sources(ranked_sources, min_score=0.2)

                    sources_dict = filtered_sources
                    sources = [Source(**src) for src in sources_dict]

                    logger.info(f" Ranked and filtered to {len(sources)} high-quality sources")

                yield f"data: {json.dumps({'type': 'status', 'message': f'Reviewed {total_reviewed} sources, selected {len(sources)} best'})}\n\n"
                await asyncio.sleep(0.01)

            # Apply focus mode to sources if not default web mode
            if body.mode != 'web' and sources_dict:
                logger.info(f"🎯 Applying {body.mode} focus mode to follow-up sources")
                sources_dict = focus_manager._filter_sources_by_mode(sources_dict, focus_mode)
                sources = [Source(**src) for src in sources_dict]
                logger.info(f" Focus mode applied, {len(sources_dict)} sources after filtering")

            # STEP 2: Build grounded prompt with conversation context
            base_prompt = grounding_engine.build_grounded_prompt(
                query=body.query,
                sources=sources_dict if sources_dict else None,
                conversation_context=conversation_context
            )

            # Apply focus mode prompt modifier
            if body.mode != 'web':
                formatted_query = base_prompt + "\n\n" + focus_mode.get_prompt_modifier()
                logger.info(f" Applied {body.mode} mode prompt modifier to follow-up")
            else:
                formatted_query = base_prompt

            # Configure Gemini (without grounding tool)
            config = types.GenerateContentConfig(
                temperature=GEMINI_TEMPERATURE,
                top_p=GEMINI_TOP_P,
                top_k=GEMINI_TOP_K,
                max_output_tokens=GEMINI_MAX_OUTPUT_TOKENS,
            )

            # Create chat with history
            chat = client.chats.create(
                model=GEMINI_MODEL,
                config=config,
                history=conversation_history
            )

            # STEP 3: Stream the grounded response
            full_text = ""
            markdown_buffer = StreamingMarkdownBuffer()

            logger.info(f"🔄 Starting follow-up streaming for session: {body.sessionId}")

            for chunk in chat.send_message_stream(formatted_query):
                if hasattr(chunk, 'text') and chunk.text:
                    full_text += chunk.text
                    formatted_chunk = markdown_buffer.process_chunk(chunk.text)
                    if formatted_chunk:
                        yield f"data: {json.dumps({'type': 'token', 'content': formatted_chunk})}\n\n"
                    await asyncio.sleep(0.01)

                # Keep last chunk for metadata
                full_response = chunk

            remaining = markdown_buffer.flush()
            if remaining:
                yield f"data: {json.dumps({'type': 'token', 'content': remaining})}\n\n"

            logger.info(f" Follow-up streaming complete. Total length: {len(full_text)}")

            # STEP 4: Validate grounding and inject citations
            yield f"data: {json.dumps({'type': 'status', 'message': 'Processing citations...'})}\n\n"
            await asyncio.sleep(0.01)

            # Format initial text to markdown/HTML
            formatted_text_no_citations = format_response_to_markdown(full_text)

            # Validate response grounding if sources were used
            if sources_dict:
                validation = grounding_engine.validate_response_grounding(
                    full_text,
                    sources_dict
                )
                logger.info(f"🔍 Grounding validation: score={validation['grounding_score']:.2f}, "
                      f"appears_grounded={validation['appears_grounded']}")

                if not validation['appears_grounded']:
                    logger.warning(f"⚠️  Warning: Response may not be well-grounded (score: {validation['grounding_score']:.2f})")

                if validation['potential_hallucinations']:
                    logger.warning(f"⚠️  Potential hallucination phrases: {validation['potential_hallucinations']}")

            # Inject citations using our citation engine
            if sources:
                formatted_text, all_sources = citation_engine.inject_citations(
                    formatted_text_no_citations,
                    sources_dict
                )

                # Display all sources searched (not just cited ones) for transparency
                sources = [Source(**src) for src in all_sources]
                logger.info(f" Processed {len(all_sources)} sources with citations")
            else:
                formatted_text = formatted_text_no_citations
                logger.info("💬 No sources to cite (conversational query)")

            # Save to database if threadId provided
            if body.threadId:
                thread = db.query(Thread).filter(Thread.id == body.threadId).first()
                if thread:
                    try:
                        user_message = Message(
                            thread_id=thread.id,
                            role='user',
                            content=body.query,
                            sources=None
                        )
                        db.add(user_message)

                        assistant_message = Message(
                            thread_id=thread.id,
                            role='assistant',
                            content=formatted_text,
                            sources=[s.model_dump() for s in sources] if sources else []
                        )
                        db.add(assistant_message)

                        thread.updated_at = datetime.now(timezone.utc)
                        db.commit()
                        logger.info(f" Saved follow-up to thread {thread.id}")
                    except Exception as e:
                        db.rollback()
                        logger.error(f" Failed to save follow-up messages to database: {e}")
                        # Continue execution - the response already completed, just logging failed

            # Send sources
            yield f"data: {json.dumps({'type': 'sources', 'sources': [s.model_dump() for s in sources]})}\n\n"
            await asyncio.sleep(0.01)

            # Generate related questions
            yield f"data: {json.dumps({'type': 'status', 'message': 'Generating suggestions...'})}\n\n"
            related_questions = generate_related_questions(body.query, formatted_text)
            yield f"data: {json.dumps({'type': 'related_questions', 'questions': related_questions})}\n\n"
            await asyncio.sleep(0.01)

            # Track search for free tier users
            if not is_browser_user:
                track_search(user_identifier, db)
                logger.info(f"📊 Free tier follow-up tracked for {user_identifier}")

            # Send completion
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
            logger.info(f" Follow-up streaming session {body.sessionId} completed")

        except Exception as e:
            logger.error(f" Follow-up streaming error: {e}")
            import traceback
            traceback.print_exc()
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@app.post("/api/search/multimodal/stream")
@limiter.limit(RATE_LIMIT_MULTIMODAL)
async def search_multimodal_stream(
    request: Request,
    q: str = Form(...),
    file: UploadFile = File(...),
    browser_auth: Optional[str] = Header(None, alias="X-Browser-Auth"),
    user_id: Optional[str] = Header(None, alias="X-User-ID"),
    db: Session = Depends(get_db)
):
    """Multimodal streaming search - accepts image or PDF with query"""

    async def generate():
        # Check authentication and rate limits
        user_identifier, is_browser_user = get_user_identifier(request, browser_auth, user_id)

        # Free tier: check rate limit
        if not is_browser_user:
            if check_rate_limit(user_identifier, db):
                error_msg = f"Daily search limit ({FREE_TIER_DAILY_LIMIT} searches) exceeded. Please try again tomorrow."
                yield f"data: {json.dumps({'type': 'error', 'message': error_msg})}\n\n"
                return

        logger.info(f"🔐 Multimodal from: {'Browser Pro' if is_browser_user else 'Free tier'} | ID: {user_identifier}")

        try:
            # Read file
            file_contents = await file.read()
            file_size = len(file_contents)

            logger.info(f"📎 Received file: {file.filename} ({file.content_type}, {file_size} bytes)")

            # Sanitize filename to prevent directory traversal attacks
            safe_filename = FileValidator.sanitize_filename(file.filename or "upload")

            # Comprehensive file validation using FileValidator
            validator = FileValidator()
            is_valid, error_message = validator.validate_file(
                file_contents,
                safe_filename,
                file.content_type
            )

            if not is_valid:
                log_file_upload(safe_filename, file_size, file.content_type, False)
                log_error("File validation failed", error_message, {"filename": safe_filename})
                yield f"data: {json.dumps({'type': 'error', 'message': error_message})}\n\n"
                return

            log_file_upload(safe_filename, file_size, file.content_type, True)

            # Generate session and thread IDs
            session_id = generate_session_id()
            yield f"data: {json.dumps({'type': 'session_id', 'sessionId': session_id})}\n\n"
            await asyncio.sleep(0.01)

            # Create new thread (use sanitized filename)
            thread_title = f"{safe_filename}: {q[:50]}..." if len(q) > 50 else f"{safe_filename}: {q}"
            new_thread = Thread(
                title=thread_title,
                session_id=session_id,
                user_id=user_identifier,
                is_browser_user=is_browser_user
            )
            db.add(new_thread)
            db.flush()
            yield f"data: {json.dumps({'type': 'thread_id', 'threadId': new_thread.id})}\n\n"
            await asyncio.sleep(0.01)

            # Send status: Processing file (use sanitized filename)
            yield f"data: {json.dumps({'type': 'status', 'message': f'Processing {safe_filename}...'})}\n\n"
            await asyncio.sleep(0.01)

            # Encode file to base64
            file_data = base64.b64encode(file_contents).decode('utf-8')

            # Prepare multimodal content for Gemini
            if file.content_type == 'application/pdf':
                # For PDF, use document processing
                parts = [
                    {"text": f"Please analyze this PDF and answer: {q}"},
                    {
                        "inline_data": {
                            "mime_type": file.content_type,
                            "data": file_data
                        }
                    }
                ]
            else:
                # For images
                parts = [
                    {"text": q if q else "What's in this image?"},
                    {
                        "inline_data": {
                            "mime_type": file.content_type,
                            "data": file_data
                        }
                    }
                ]

            # Configure Gemini
            config = types.GenerateContentConfig(
                temperature=GEMINI_TEMPERATURE,
                top_p=GEMINI_TOP_P,
                top_k=GEMINI_TOP_K,
                max_output_tokens=GEMINI_MAX_OUTPUT_TOKENS,
            )

            # Stream the response
            full_text = ""
            markdown_buffer = StreamingMarkdownBuffer()
            yield f"data: {json.dumps({'type': 'status', 'message': 'Analyzing content...'})}\n\n"

            logger.info(f"🔄 Starting multimodal streaming for: {safe_filename}")

            for chunk in client.models.generate_content_stream(
                model=GEMINI_MODEL,
                contents={"parts": parts},
                config=config
            ):
                if hasattr(chunk, 'text') and chunk.text:
                    full_text += chunk.text
                    formatted_chunk = markdown_buffer.process_chunk(chunk.text)
                    if formatted_chunk:
                        yield f"data: {json.dumps({'type': 'token', 'content': formatted_chunk})}\n\n"
                    await asyncio.sleep(0.01)

            remaining = markdown_buffer.flush()
            if remaining:
                yield f"data: {json.dumps({'type': 'token', 'content': remaining})}\n\n"

            logger.info(f" Multimodal streaming complete. Total length: {len(full_text)}")

            # Format text
            formatted_text = format_response_to_markdown(full_text)

            # Save to database (use sanitized filename)
            try:
                user_message = Message(
                    thread_id=new_thread.id,
                    role='user',
                    content=f"[Uploaded {safe_filename}] {q}",
                    sources=None
                )
                db.add(user_message)

                assistant_message = Message(
                    thread_id=new_thread.id,
                    role='assistant',
                    content=formatted_text,
                    sources=[]
                )
                db.add(assistant_message)
                db.commit()
                log_database_operation("INSERT", "messages", new_thread.id)
                logger.info(f" Saved multimodal messages to thread {new_thread.id}")
            except Exception as e:
                db.rollback()
                logger.error(f" Failed to save multimodal messages to database: {e}")
                # Continue execution - the response already completed, just logging failed

            # No sources for multimodal (file is the source)
            yield f"data: {json.dumps({'type': 'sources', 'sources': []})}\n\n"

            # No related questions for now
            yield f"data: {json.dumps({'type': 'related_questions', 'questions': []})}\n\n"

            # Track search for free tier users
            if not is_browser_user:
                track_search(user_identifier, db)
                logger.info(f"📊 Free tier multimodal search tracked for {user_identifier}")

            # Send completion
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
            logger.info(f" Multimodal session {session_id} completed")

        except Exception as e:
            logger.exception(f" Multimodal streaming error: {e}")
            log_error("Multimodal streaming error", str(e), {"session_id": session_id})
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


# Thread management endpoints

@app.get("/api/threads", response_model=List[ThreadListResponse])
async def list_threads(
    request: Request,
    browser_auth: Optional[str] = Header(None, alias="X-Browser-Auth"),
    user_id: Optional[str] = Header(None, alias="X-User-ID"),
    db: Session = Depends(get_db),
    limit: int = 50
):
    """Get list of all threads for the current user, ordered by most recent"""
    user_identifier, is_browser_user = get_user_identifier(request, browser_auth, user_id)

    threads = db.query(Thread).filter(
        Thread.user_id == user_identifier
    ).order_by(Thread.updated_at.desc()).limit(limit).all()

    return [thread.to_dict() for thread in threads]


@app.get("/api/threads/{thread_id}", response_model=ThreadDetailResponse)
async def get_thread(
    thread_id: str,
    request: Request,
    browser_auth: Optional[str] = Header(None, alias="X-Browser-Auth"),
    user_id: Optional[str] = Header(None, alias="X-User-ID"),
    db: Session = Depends(get_db)
):
    """Get a specific thread with all its messages"""
    user_identifier, is_browser_user = get_user_identifier(request, browser_auth, user_id)

    thread = db.query(Thread).filter(
        Thread.id == thread_id,
        Thread.user_id == user_identifier
    ).first()

    if not thread:
        raise HTTPException(
            status_code=404,
            detail=f"Thread '{thread_id}' not found. It may have been deleted."
        )

    messages = db.query(Message).filter(Message.thread_id == thread_id).order_by(Message.created_at.asc()).all()

    return ThreadDetailResponse(
        id=thread.id,
        title=thread.title,
        session_id=thread.session_id,
        created_at=thread.created_at.isoformat(),
        updated_at=thread.updated_at.isoformat(),
        is_pinned=thread.is_pinned,
        messages=[msg.to_dict() for msg in messages]
    )


@app.patch("/api/threads/{thread_id}")
async def update_thread(
    thread_id: str,
    update: UpdateThreadRequest,
    request: Request,
    browser_auth: Optional[str] = Header(None, alias="X-Browser-Auth"),
    user_id: Optional[str] = Header(None, alias="X-User-ID"),
    db: Session = Depends(get_db)
):
    """Update thread (rename or pin/unpin)"""
    user_identifier, is_browser_user = get_user_identifier(request, browser_auth, user_id)

    thread = db.query(Thread).filter(
        Thread.id == thread_id,
        Thread.user_id == user_identifier
    ).first()

    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")

    try:
        if update.title is not None:
            thread.title = update.title
        if update.is_pinned is not None:
            thread.is_pinned = update.is_pinned

        thread.updated_at = datetime.now(timezone.utc)
        db.commit()

        return {"success": True, "thread": thread.to_dict()}
    except Exception as e:
        db.rollback()
        logger.error(f" Failed to update thread {thread_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update thread")


@app.delete("/api/threads/{thread_id}")
async def delete_thread(
    thread_id: str,
    request: Request,
    browser_auth: Optional[str] = Header(None, alias="X-Browser-Auth"),
    user_id: Optional[str] = Header(None, alias="X-User-ID"),
    db: Session = Depends(get_db)
):
    """Delete a thread and all its messages"""
    user_identifier, is_browser_user = get_user_identifier(request, browser_auth, user_id)

    thread = db.query(Thread).filter(
        Thread.id == thread_id,
        Thread.user_id == user_identifier
    ).first()

    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")

    try:
        db.delete(thread)
        db.commit()

        return {"success": True, "message": "Thread deleted"}
    except Exception as e:
        db.rollback()
        logger.error(f" Failed to delete thread {thread_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete thread")


@app.post("/api/threads/{thread_id}/share")
async def create_share_link(
    thread_id: str,
    request: Request,
    browser_auth: Optional[str] = Header(None, alias="X-Browser-Auth"),
    user_id: Optional[str] = Header(None, alias="X-User-ID"),
    db: Session = Depends(get_db)
):
    """Generate a shareable link for a thread"""
    user_identifier, is_browser_user = get_user_identifier(request, browser_auth, user_id)

    thread = db.query(Thread).filter(
        Thread.id == thread_id,
        Thread.user_id == user_identifier
    ).first()

    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")

    try:
        # Generate share ID if not already exists
        if not thread.share_id:
            thread.share_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=12))
            db.commit()

        return {"shareId": thread.share_id, "threadId": thread.id}
    except Exception as e:
        db.rollback()
        logger.error(f" Failed to create share link for thread {thread_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to create share link")


@app.get("/api/shared/{share_id}")
async def get_shared_thread(share_id: str, db: Session = Depends(get_db)):
    """Get a thread by its share ID (public access)"""
    thread = db.query(Thread).filter(Thread.share_id == share_id).first()
    if not thread:
        raise HTTPException(status_code=404, detail="Shared conversation not found")

    messages = db.query(Message).filter(Message.thread_id == thread.id).order_by(Message.created_at.asc()).all()

    return ThreadDetailResponse(
        id=thread.id,
        title=thread.title,
        session_id=thread.session_id,
        created_at=thread.created_at.isoformat(),
        updated_at=thread.updated_at.isoformat(),
        is_pinned=thread.is_pinned,
        messages=[msg.to_dict() for msg in messages]
    )


# Admin endpoints (require ADMIN_API_KEY)

def verify_admin_key(admin_key: str = Header(None, alias="X-Admin-Key")):
    """Verify admin API key"""
    if not ADMIN_API_KEY:
        raise HTTPException(status_code=501, detail="Admin API not configured")
    if admin_key != ADMIN_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid admin key")
    return True


@app.get("/api/admin/users")
async def get_all_users(
    db: Session = Depends(get_db),
    admin_verified: bool = Depends(verify_admin_key)
):
    """Get list of all users (browser users and free tier IPs) with stats"""
    from sqlalchemy import func

    # Get all unique users from threads with their stats
    user_stats = db.query(
        Thread.user_id,
        Thread.is_browser_user,
        func.count(Thread.id).label('thread_count'),
        func.max(Thread.updated_at).label('last_activity')
    ).group_by(Thread.user_id, Thread.is_browser_user).all()

    users = []
    for user_id, is_browser, thread_count, last_activity in user_stats:
        user_type = "Browser Pro" if is_browser else "Free Tier"
        users.append({
            "user_id": user_id,
            "user_type": user_type,
            "thread_count": thread_count,
            "last_activity": last_activity.isoformat() if last_activity else None
        })

    return {"users": users, "total": len(users)}


@app.get("/api/admin/rate-limits")
async def get_rate_limits(
    db: Session = Depends(get_db),
    admin_verified: bool = Depends(verify_admin_key),
    date: Optional[str] = None
):
    """Get rate limit stats for free tier users"""
    from datetime import date as date_type

    query = db.query(RateLimit)

    if date:
        # Filter by specific date (format: YYYY-MM-DD)
        try:
            filter_date = date_type.fromisoformat(date)
            query = query.filter(RateLimit.date == filter_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    else:
        # Default to today
        today = datetime.now(timezone.utc).date()
        query = query.filter(RateLimit.date == today)

    rate_limits = query.all()

    return {
        "rate_limits": [
            {
                "ip_address": rl.ip_address,
                "search_count": rl.search_count,
                "date": rl.date.isoformat(),
                "created_at": rl.created_at.isoformat()
            }
            for rl in rate_limits
        ],
        "total": len(rate_limits),
        "date_filter": date if date else "today"
    }


@app.get("/api/admin/user/{user_id}")
async def get_user_details(
    user_id: str,
    db: Session = Depends(get_db),
    admin_verified: bool = Depends(verify_admin_key)
):
    """Get detailed stats for a specific user"""
    from sqlalchemy import func

    # Get user's threads
    threads = db.query(Thread).filter(Thread.user_id == user_id).order_by(Thread.updated_at.desc()).all()

    if not threads:
        raise HTTPException(status_code=404, detail="User not found")

    # Get message count for this user
    thread_ids = [t.id for t in threads]
    message_count = db.query(func.count(Message.id)).filter(
        Message.thread_id.in_(thread_ids)
    ).scalar()

    # Get rate limit info if free tier
    rate_limit_info = None
    if threads and not threads[0].is_browser_user:
        today = datetime.now(timezone.utc).date()
        rate_limit = db.query(RateLimit).filter(
            RateLimit.ip_address == user_id,
            RateLimit.date == today
        ).first()
        if rate_limit:
            rate_limit_info = {
                "search_count": rate_limit.search_count,
                "limit": FREE_TIER_DAILY_LIMIT,
                "remaining": max(0, FREE_TIER_DAILY_LIMIT - rate_limit.search_count)
            }

    return {
        "user_id": user_id,
        "user_type": "Browser Pro" if threads[0].is_browser_user else "Free Tier",
        "thread_count": len(threads),
        "message_count": message_count,
        "first_activity": min(t.created_at for t in threads).isoformat(),
        "last_activity": max(t.updated_at for t in threads).isoformat(),
        "rate_limit": rate_limit_info,
        "recent_threads": [
            {
                "id": t.id,
                "title": t.title,
                "created_at": t.created_at.isoformat(),
                "updated_at": t.updated_at.isoformat()
            }
            for t in threads[:10]  # Last 10 threads
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=SERVER_HOST, port=SERVER_PORT)
