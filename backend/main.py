import os
import random
import string
import pickle
from datetime import datetime
from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException, Query, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
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
from models import Thread, Message
import requests
from urllib.parse import urlparse
from bs4 import BeautifulSoup

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
            missing_required.append(f"❌ {var}: {message}")

    # Check optional variables
    for var, message in optional_vars.items():
        if not os.getenv(var):
            missing_optional.append(f"⚠️  {var}: {message}")

    # Print results
    if missing_required:
        print("\n🔴 Missing Required Environment Variables:")
        for msg in missing_required:
            print(f"  {msg}")
        print("\nPlease add these to your .env file and restart the server.\n")
        raise ValueError("Missing required environment variables")

    if missing_optional:
        print("\n🟡 Optional Environment Variables Not Set:")
        for msg in missing_optional:
            print(f"  {msg}")
        print()

    print("✅ Environment validation passed")

# Validate environment
validate_environment()

# Create database tables
Base.metadata.create_all(bind=engine)
print("✅ Database tables created")

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Initialize FastAPI app
app = FastAPI(title="Zemixity Search API")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3003"],  # Next.js frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure Gemini AI
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in environment variables")

# Google Custom Search API configuration
GOOGLE_SEARCH_ENGINE_ID = os.getenv("GOOGLE_SEARCH_ENGINE_ID")
CUSTOM_SEARCH_API_URL = "https://www.googleapis.com/customsearch/v1"

client = genai.Client(api_key=GOOGLE_API_KEY)

# Redis configuration with fallback to in-memory storage
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))
SESSION_TTL = 86400  # 24 hours (prevents session expiry during long conversations)

# Try to connect to Redis, fallback to in-memory if unavailable
redis_client: Optional[redis.Redis] = None
try:
    redis_client = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=REDIS_DB,
        decode_responses=False,
        socket_connect_timeout=1
    )
    redis_client.ping()
    print("✅ Connected to Redis for session persistence")
except (redis.ConnectionError, redis.TimeoutError):
    print("⚠️  Redis not available, using in-memory session storage")
    redis_client = None

# In-memory fallback
chat_sessions: Dict[str, any] = {}


class SessionStore:
    """Session store that stores chat history instead of chat objects"""

    def set(self, session_id: str, history: list) -> None:
        """Store conversation history as a list of dicts"""
        if redis_client:
            try:
                # Store history as JSON string (no pickle needed)
                import json
                serialized = json.dumps(history)
                redis_client.setex(f"session:{session_id}", SESSION_TTL, serialized)
                print(f"✅ Stored session {session_id} in Redis")
            except Exception as e:
                print(f"Redis set error: {e}, falling back to memory")
                chat_sessions[session_id] = history
        else:
            chat_sessions[session_id] = history
            print(f"✅ Stored session {session_id} in memory")

    def get(self, session_id: str) -> Optional[list]:
        """Retrieve conversation history"""
        if redis_client:
            try:
                data = redis_client.get(f"session:{session_id}")
                if data:
                    import json
                    history = json.loads(data)
                    print(f"✅ Retrieved session {session_id} from Redis with {len(history)} messages")
                    return history
                else:
                    print(f"⚠️  Session {session_id} not found in Redis, checking memory")
                    return chat_sessions.get(session_id)
            except Exception as e:
                print(f"Redis get error: {e}, falling back to memory")
                return chat_sessions.get(session_id)
        else:
            history = chat_sessions.get(session_id)
            if history:
                print(f"✅ Retrieved session {session_id} from memory with {len(history)} messages")
            else:
                print(f"❌ Session {session_id} not found in memory")
            return history

    def delete(self, session_id: str) -> None:
        if redis_client:
            try:
                redis_client.delete(f"session:{session_id}")
            except Exception:
                pass
        if session_id in chat_sessions:
            del chat_sessions[session_id]


session_store = SessionStore()


# Pydantic models
class FollowUpRequest(BaseModel):
    sessionId: str
    query: str
    threadId: Optional[str] = None  # Add thread ID for persistence


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

    # Process main sections (lines that start with word(s) followed by colon)
    processed_text = re.sub(r'^([A-Za-z][A-Za-z\s]+):(\s*)', r'## \1\2', processed_text, flags=re.MULTILINE)

    # Process sub-sections - Python compatible version (no variable-width lookbehind)
    # Split by lines, process each, then rejoin
    lines = processed_text.split('\n')
    processed_lines = []
    for line in lines:
        # Check if line starts with word(s) followed by colon (not followed by digit)
        if re.match(r'^([A-Za-z][A-Za-z\s]+):(?!\d)', line):
            # Only convert if not already a header
            if not line.startswith('#'):
                processed_lines.append(re.sub(r'^([A-Za-z][A-Za-z\s]+):', r'### \1', line))
            else:
                processed_lines.append(line)
        else:
            processed_lines.append(line)
    processed_text = '\n'.join(processed_lines)

    # Process bullet points
    processed_text = re.sub(r'^[•●○]\s*', '* ', processed_text, flags=re.MULTILINE)

    # Split into paragraphs
    paragraphs = [p for p in processed_text.split('\n\n') if p]

    # Process each paragraph
    formatted = []
    for p in paragraphs:
        # If it's a header or list item, preserve it
        if p.startswith('#') or p.startswith('*') or p.startswith('-'):
            formatted.append(p)
        else:
            # Add proper paragraph formatting
            formatted.append(f"{p}\n")

    markdown_text = '\n\n'.join(formatted)

    # Convert markdown to HTML
    html = markdown.markdown(
        markdown_text,
        extensions=['extra', 'nl2br']
    )

    return html


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
        print(f"Error extracting sources: {e}")

    return list(source_map.values())


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

        # Use Gemini 2.0 Flash for related questions (higher quota, lower cost)
        response = client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.7,
                max_output_tokens=256,
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
        print(f"Error generating related questions: {e}")
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


def fetch_google_custom_search(query: str, num_results: int = 10) -> List[Source]:
    """Fetch search results from Google Custom Search API with rich metadata"""
    if not GOOGLE_SEARCH_ENGINE_ID:
        print("⚠️  Google Custom Search Engine ID not configured, falling back to Gemini grounding")
        return []

    try:
        params = {
            'key': GOOGLE_API_KEY,
            'cx': GOOGLE_SEARCH_ENGINE_ID,
            'q': query,
            'num': num_results,
        }

        response = requests.get(CUSTOM_SEARCH_API_URL, params=params, timeout=10)
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

        print(f"✅ Fetched {len(sources)} sources from Google Custom Search API")
        return sources

    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching from Custom Search API: {e}")
        return []
    except Exception as e:
        print(f"❌ Unexpected error in Custom Search: {e}")
        return []


@app.get("/")
async def root():
    return {"message": "Gemini Search API is running"}


@app.get("/health")
@app.get("/api/health")
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint for monitoring"""
    health_status = {
        "status": "healthy",
        "version": "0.1.0",
        "timestamp": datetime.utcnow().isoformat()
    }

    # Check database connection
    try:
        db.execute("SELECT 1")
        health_status["database"] = "connected"
    except Exception as e:
        health_status["database"] = f"error: {str(e)}"
        health_status["status"] = "unhealthy"

    # Check Redis connection
    if redis_client:
        try:
            redis_client.ping()
            health_status["redis"] = "connected"
        except Exception as e:
            health_status["redis"] = f"error: {str(e)} (falling back to in-memory)"
    else:
        health_status["redis"] = "unavailable (using in-memory storage)"

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


@app.get("/api/search", response_model=SearchResponse)
@limiter.limit("10/minute")
async def search(request: Request, q: str = Query(..., description="Search query"), db: Session = Depends(get_db)):
    """Search endpoint - creates a new chat session and thread"""
    try:
        if not q:
            raise HTTPException(status_code=400, detail="Query parameter 'q' is required")

        # Configure Google Search grounding tool
        grounding_tool = types.Tool(google_search=types.GoogleSearch())

        config = types.GenerateContentConfig(
            temperature=0.9,
            top_p=1.0,
            top_k=1,
            max_output_tokens=2048,
            tools=[grounding_tool],
        )

        # Create a chat session
        chat = client.chats.create(
            model="gemini-2.0-flash-exp",
            config=config,
        )

        # Send message
        response = chat.send_message(q)
        text = response.text

        print(f"Raw Google API Response text: {text}")

        # Format the response text to proper markdown/HTML
        formatted_text = format_response_to_markdown(text)

        # Check if this is a conversational query (no sources needed)
        if is_conversational_query(q):
            sources = []
            print(f"💬 Conversational query detected, skipping source fetch")
        else:
            # Fetch rich sources from Google Custom Search API
            custom_search_sources = fetch_google_custom_search(q, num_results=10)

            # If Custom Search API returned sources, use those; otherwise fall back to Gemini grounding
            if custom_search_sources and len(custom_search_sources) > 0:
                sources = custom_search_sources
                print(f"✅ Using {len(sources)} sources from Custom Search API")
            else:
                sources = extract_sources(response)
                print(f"⚠️  Using {len(sources)} sources from Gemini grounding (fallback)")

        # Generate a session ID and store the conversation history
        session_id = generate_session_id()
        # Store history as list of dicts with role and content
        conversation_history = [
            {"role": "user", "parts": [q]},
            {"role": "model", "parts": [text]}
        ]
        session_store.set(session_id, conversation_history)

        # Check if a thread with the exact same first message exists recently (within 5 minutes)
        # This prevents duplicate threads on refresh or accidental re-search
        from datetime import timedelta
        recent_time = datetime.utcnow() - timedelta(minutes=5)

        existing_thread = db.query(Thread).join(Message).filter(
            Message.role == 'user',
            Message.content == q,
            Thread.created_at >= recent_time
        ).order_by(Thread.created_at.desc()).first()

        if existing_thread:
            # Reuse existing thread
            new_thread = existing_thread
            print(f"♻️  Reusing existing thread {existing_thread.id} (created {existing_thread.created_at})")
        else:
            # Create new thread in database
            thread_title = generate_thread_title(q)
            new_thread = Thread(
                title=thread_title,
                session_id=session_id
            )
            db.add(new_thread)
            db.flush()  # Get the thread ID
            print(f"✅ Created new thread {new_thread.id}")

        # Only save messages if this is a new thread (not reused)
        if not existing_thread:
            # Save user message
            user_message = Message(
                thread_id=new_thread.id,
                role='user',
                content=q,
                sources=None
            )
            db.add(user_message)

            # Save assistant response
            assistant_message = Message(
                thread_id=new_thread.id,
                role='assistant',
                content=formatted_text,
                sources=[s.dict() for s in sources] if sources else []
            )
            db.add(assistant_message)
            db.commit()
        else:
            # For existing thread, just fetch the existing messages
            user_message = db.query(Message).filter(
                Message.thread_id == new_thread.id,
                Message.role == 'user'
            ).first()
            assistant_message = db.query(Message).filter(
                Message.thread_id == new_thread.id,
                Message.role == 'assistant'
            ).first()

        # Generate related questions
        related_questions = generate_related_questions(q, formatted_text)

        print(f"✅ Created thread {new_thread.id} with session {session_id}")

        # Build conversation history
        conversation = [
            MessageResponse(
                id=user_message.id,
                role='user',
                content=user_message.content,
                sources=[],
                created_at=user_message.created_at.isoformat()
            ),
            MessageResponse(
                id=assistant_message.id,
                role='assistant',
                content=assistant_message.content,
                sources=sources,
                created_at=assistant_message.created_at.isoformat()
            )
        ]

        return SearchResponse(
            sessionId=session_id,
            threadId=new_thread.id,
            summary=formatted_text,
            sources=sources,
            relatedQuestions=related_questions,
            conversation=conversation
        )

    except Exception as e:
        print(f"Search error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=str(e) or "An error occurred while processing your search"
        )


@app.post("/api/follow-up", response_model=FollowUpResponse)
@limiter.limit("20/minute")
async def follow_up(request: Request, body: FollowUpRequest, db: Session = Depends(get_db)):
    """Follow-up endpoint - continues existing chat session"""
    try:
        if not body.sessionId or not body.query:
            raise HTTPException(
                status_code=400,
                detail="Both sessionId and query are required"
            )

        # Get conversation history from session store
        conversation_history = session_store.get(body.sessionId)
        if not conversation_history:
            raise HTTPException(
                status_code=404,
                detail="Chat session not found or expired. Please start a new conversation by asking a new question."
            )

        # Recreate chat session from history
        config = types.GenerateContentConfig(
            temperature=0.9,
            top_p=1.0,
            top_k=1,
            max_output_tokens=2048,
            tools=[grounding_tool],
        )

        # Create new chat with history
        chat = client.chats.create(
            model="gemini-2.0-flash-exp",
            config=config,
            history=conversation_history  # Restore previous conversation
        )

        # Send follow-up message in existing chat
        response = chat.send_message(body.query)
        text = response.text

        # Update conversation history
        conversation_history.append({"role": "user", "parts": [body.query]})
        conversation_history.append({"role": "model", "parts": [text]})
        session_store.set(body.sessionId, conversation_history)

        print(f"Raw Google API Follow-up Response text: {text}")

        # Format the response text to proper markdown/HTML
        formatted_text = format_response_to_markdown(text)

        # Check if this is a conversational query (no sources needed)
        if is_conversational_query(body.query):
            sources = []
            print(f"💬 Conversational follow-up detected, skipping source fetch")
        else:
            # Fetch rich sources from Google Custom Search API
            custom_search_sources = fetch_google_custom_search(body.query, num_results=10)

            # If Custom Search API returned sources, use those; otherwise fall back to Gemini grounding
            if custom_search_sources and len(custom_search_sources) > 0:
                sources = custom_search_sources
                print(f"✅ Using {len(sources)} sources from Custom Search API")
            else:
                sources = extract_sources(response)
                print(f"⚠️  Using {len(sources)} sources from Gemini grounding (fallback)")

        # Save follow-up messages to database if threadId provided
        if body.threadId:
            thread = db.query(Thread).filter(Thread.id == body.threadId).first()
            if thread:
                # Save user follow-up
                user_message = Message(
                    thread_id=thread.id,
                    role='user',
                    content=body.query,
                    sources=None
                )
                db.add(user_message)

                # Save assistant response
                assistant_message = Message(
                    thread_id=thread.id,
                    role='assistant',
                    content=formatted_text,
                    sources=[s.dict() for s in sources] if sources else []
                )
                db.add(assistant_message)

                # Update thread timestamp
                thread.updated_at = datetime.utcnow()
                db.commit()
                print(f"✅ Saved follow-up to thread {thread.id}")

                # Build full conversation history from database
                all_messages = db.query(Message).filter(
                    Message.thread_id == thread.id
                ).order_by(Message.created_at.asc()).all()

                conversation = []
                for msg in all_messages:
                    msg_sources = []
                    if msg.sources:
                        for src in msg.sources:
                            msg_sources.append(Source(**src))

                    conversation.append(MessageResponse(
                        id=msg.id,
                        role=msg.role,
                        content=msg.content,
                        sources=msg_sources,
                        created_at=msg.created_at.isoformat()
                    ))
            else:
                # Thread not found, return just current exchange
                conversation = []
        else:
            # No threadId provided, return just current exchange
            conversation = []

        # Generate related questions
        related_questions = generate_related_questions(body.query, formatted_text)

        return FollowUpResponse(
            summary=formatted_text,
            sources=sources,
            relatedQuestions=related_questions,
            conversation=conversation
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"Follow-up error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=str(e) or "An error occurred while processing your follow-up question"
        )


# Thread management endpoints

@app.get("/api/threads", response_model=List[ThreadListResponse])
async def list_threads(db: Session = Depends(get_db), limit: int = 50):
    """Get list of all threads, ordered by most recent"""
    threads = db.query(Thread).order_by(Thread.updated_at.desc()).limit(limit).all()
    return [thread.to_dict() for thread in threads]


@app.get("/api/threads/{thread_id}", response_model=ThreadDetailResponse)
async def get_thread(thread_id: str, db: Session = Depends(get_db)):
    """Get a specific thread with all its messages"""
    thread = db.query(Thread).filter(Thread.id == thread_id).first()
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
async def update_thread(thread_id: str, update: UpdateThreadRequest, db: Session = Depends(get_db)):
    """Update thread (rename or pin/unpin)"""
    thread = db.query(Thread).filter(Thread.id == thread_id).first()
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")

    if update.title is not None:
        thread.title = update.title
    if update.is_pinned is not None:
        thread.is_pinned = update.is_pinned

    thread.updated_at = datetime.utcnow()
    db.commit()

    return {"success": True, "thread": thread.to_dict()}


@app.delete("/api/threads/{thread_id}")
async def delete_thread(thread_id: str, db: Session = Depends(get_db)):
    """Delete a thread and all its messages"""
    thread = db.query(Thread).filter(Thread.id == thread_id).first()
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")

    db.delete(thread)
    db.commit()

    return {"success": True, "message": "Thread deleted"}


@app.post("/api/threads/{thread_id}/share")
async def create_share_link(thread_id: str, db: Session = Depends(get_db)):
    """Generate a shareable link for a thread"""
    thread = db.query(Thread).filter(Thread.id == thread_id).first()
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")

    # Generate share ID if not already exists
    if not thread.share_id:
        thread.share_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=12))
        db.commit()

    return {"shareId": thread.share_id, "threadId": thread.id}


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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
