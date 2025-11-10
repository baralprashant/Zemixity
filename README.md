# Gemixity 🔍

**Next-Generation AI Search Engine** - A powerful AI-powered search platform with advanced RAG pipeline, inline citations, and conversational intelligence powered by Google's Gemini 2.0 Flash.

![Next.js](https://img.shields.io/badge/Next.js-15.5.4-black)
![Python](https://img.shields.io/badge/Python-3.13+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.118.0-green)
![TypeScript](https://img.shields.io/badge/TypeScript-5.0-blue)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## ✨ Key Features

### 🎯 **Core Capabilities**
- **Advanced RAG Pipeline** - Multi-stage retrieval, ranking, and source quality filtering
- **Inline Citations** - Perplexity-style citation numbers [1][2] linked to sources
- **Grounding Engine** - Ensures AI responses are strictly based on retrieved sources
- **Pro Search Mode** - Deep research with comprehensive multi-source analysis
- **Focus Modes** - Specialized search modes (Web, Academic, Code, Writing, News)
- **Conversational Threads** - Context-aware follow-ups with full conversation history
- **Multimodal Search** - Upload images and documents for AI analysis

### 📚 **Source & Citation Features**
- Beautiful source cards with images, favicons, and metadata
- Up to 10 high-quality sources per search
- Smart deduplication and relevance scoring
- Publication date tracking
- Domain filtering (include/exclude specific sites)
- Date range filters (past 24h, week, month, year)
- File type filters (PDF, DOC, etc.)

### 🔐 **Security & Access Control**
- Dual-tier authentication (Browser Pro + Public Free tier)
- Rate limiting with configurable quotas
- File upload validation with magic number checking
- XSS protection with DOMPurify sanitization
- SQL injection prevention with parameterized queries
- CORS configuration for production deployment

### 💾 **Data Management**
- Thread persistence with PostgreSQL/SQLite
- Conversation history with unlimited messages
- Thread sharing with public URLs
- Export conversations as HTML
- Thread pinning and renaming
- Database optimization with connection pooling

### 🎨 **Modern UI/UX**
- Clean, responsive design with Tailwind CSS 4
- Smooth animations with Framer Motion
- Collapsible source sections
- Typing animations for AI responses
- Keyboard shortcuts (Cmd+K, Cmd+/, Esc)
- Error boundaries for graceful error handling

---

## 🏗️ Architecture

### Frontend Stack
- **Framework**: Next.js 15.5.4 with App Router
- **UI Library**: React 19.1.0
- **Styling**: Tailwind CSS 4.1
- **State Management**: TanStack Query v5
- **Animations**: Framer Motion
- **Security**: DOMPurify for XSS prevention
- **Icons**: Lucide React

### Backend Stack
- **Framework**: FastAPI with async/await
- **AI Model**: Google Gemini 2.0 Flash
- **Search**: Google Custom Search API
- **Database**: PostgreSQL (SQLite fallback)
- **ORM**: SQLAlchemy 2.0 with connection pooling
- **Rate Limiting**: SlowAPI
- **Validation**: Pydantic v2

### Backend Engines
- **RAG Pipeline** - Source retrieval, ranking, and filtering
- **Grounding Engine** - Response validation and grounding score calculation
- **Citation Engine** - Automatic citation injection with source matching
- **Query Processor** - Query analysis, enhancement, and intent detection
- **Pro Search Engine** - Deep research orchestration
- **Focus Mode Manager** - Specialized search behavior per mode
- **Search Filter Manager** - Advanced filtering (date, domain, file type)

---

## 📋 Prerequisites

- **Node.js** 24.9.0 or higher
- **Python** 3.13 or higher
- **PostgreSQL** (optional - falls back to SQLite)
- **Redis** (optional - not currently used but supported)
- **Google AI API Key** ([Get one here](https://aistudio.google.com/apikey))
- **Google Custom Search Engine ID** ([Create one here](https://programmablesearchengine.google.com/))

---

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/Gemixity.git
cd Gemixity
```

### 2. Backend Setup

```bash
# Navigate to backend
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Edit .env with your API keys and configuration
nano .env  # or use your preferred editor
```

**Required environment variables:**
```bash
GOOGLE_API_KEY=your_google_api_key_here
GOOGLE_SEARCH_ENGINE_ID=your_search_engine_id_here
```

**Optional but recommended:**
```bash
# Authentication (generate with: openssl rand -hex 32)
BROWSER_API_KEY=your_secure_browser_key_here
ADMIN_API_KEY=your_secure_admin_key_here

# Database
DATABASE_URL=postgresql://localhost/gemixity  # Defaults to SQLite

# Rate Limiting
FREE_TIER_DAILY_LIMIT=10000  # For development

# CORS
CORS_ORIGINS=http://localhost:3005,https://yourdomain.com
```

### 3. Run the Backend

```bash
# Make sure you're in backend/ with venv activated
python3 main.py

# Or use uvicorn directly
uvicorn main:app --reload --port 8080
```

Backend will be available at [http://localhost:8080](http://localhost:8080)

### 4. Frontend Setup

```bash
# Navigate to frontend (from project root)
cd ..

# Install dependencies
npm install

# Create environment file
cp .env.local.example .env.local

# Edit .env.local
echo "NEXT_PUBLIC_API_URL=http://localhost:8080" > .env.local

# Run development server
npm run dev
```

Frontend will be available at [http://localhost:3005](http://localhost:3005)

### 5. Verify Everything Works

1. Open [http://localhost:3005](http://localhost:3005)
2. Try searching: "upcoming Bollywood movies 2025"
3. Check that sources appear below the response
4. Click "Sources" pill to expand and see all 10 sources
5. Ask a follow-up question to test conversation continuity
6. Check sidebar for conversation history

---

## 🔑 Getting API Keys

### Google AI API Key (Required)

1. Visit [Google AI Studio](https://aistudio.google.com/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the key and add to `backend/.env` as `GOOGLE_API_KEY`

**Note:** Free tier includes 1500 requests/day

### Google Custom Search Engine ID (Required)

1. Visit [Programmable Search Engine](https://programmablesearchengine.google.com/)
2. Click "Add" or "Create a search engine"
3. Under "What to search", select "Search the entire web"
4. Create the search engine
5. Go to "Edit search engine" → "Setup" → "Basic"
6. Copy the "Search engine ID" and add to `backend/.env` as `GOOGLE_SEARCH_ENGINE_ID`

**Note:** Free tier includes 100 queries/day

### Authentication Keys (Optional but Recommended)

Generate secure random keys for browser and admin authentication:

```bash
# Generate browser API key
openssl rand -hex 32

# Generate admin API key
openssl rand -hex 32
```

Add these to `backend/.env`:
```bash
BROWSER_API_KEY=<generated_key>
ADMIN_API_KEY=<generated_key>
```

---

## 📦 Project Structure

```
Gemixity/
├── src/                                # Frontend source
│   ├── app/                           # Next.js app directory
│   │   ├── page.tsx                  # Home page with search
│   │   ├── search/page.tsx           # Search results page
│   │   ├── shared/[shareId]/         # Shared thread viewer
│   │   ├── layout.tsx                # Root layout with sidebar
│   │   └── globals.css               # Global styles
│   ├── components/                    # React components
│   │   ├── SearchInput.tsx           # Main search input with file upload
│   │   ├── SearchResults.tsx         # Results display with streaming
│   │   ├── ConversationMessage.tsx   # Message bubbles with citations
│   │   ├── PersistentSidebar.tsx     # Conversation history sidebar
│   │   ├── FollowUpInput.tsx         # Follow-up question input
│   │   ├── RelatedQuestions.tsx      # AI-generated suggestions
│   │   ├── FocusMode.tsx             # Focus mode selector
│   │   ├── ErrorBoundary.tsx         # Error handling wrapper
│   │   ├── TypingAnimation.tsx       # Streaming text animation
│   │   └── ui/                       # shadcn/ui components
│   ├── hooks/                         # Custom React hooks
│   │   └── useStreamingSearch.ts     # Main search hook with SSE
│   └── lib/                           # Utilities
│       ├── analytics.ts              # Event tracking
│       └── export.ts                 # HTML export & sharing
├── backend/                           # Backend API
│   ├── main.py                       # FastAPI application (2000+ lines)
│   ├── models.py                     # SQLAlchemy models (Thread, Message, etc.)
│   ├── database.py                   # Database config with pooling
│   ├── citation_engine.py            # Citation injection engine
│   ├── grounding_engine.py           # Response grounding validation
│   ├── rag_pipeline.py               # RAG with ranking & filtering
│   ├── query_processor.py            # Query analysis & enhancement
│   ├── pro_search.py                 # Pro Search orchestration
│   ├── focus_modes.py                # Focus mode configurations
│   ├── search_filters.py             # Advanced search filters
│   ├── file_security.py              # File upload validation
│   ├── database_optimizer.py         # DB optimization utilities
│   ├── logger.py                     # Structured logging
│   ├── requirements.txt              # Python dependencies
│   ├── .env.example                  # Environment template
│   └── migrate_add_user_fields.py    # Database migration script
├── public/                            # Static assets
│   └── favicon.png                   # App icon
├── docs/                              # Documentation
│   └── commands.md                   # Useful commands
├── package.json                       # Node.js dependencies
├── next.config.ts                     # Next.js configuration
├── tailwind.config.ts                 # Tailwind CSS configuration
├── vercel.json                        # Vercel deployment config
└── CHANGELOG.md                       # Version history
```

---

## 🛠️ Development

### Frontend Commands

```bash
npm run dev          # Start development server (port 3005)
npm run build        # Build for production
npm run start        # Start production server
npm run lint         # Run ESLint
```

### Backend Commands

```bash
python3 main.py                          # Run backend server
uvicorn main:app --reload --port 8080    # Run with hot reload
python3 migrate_add_user_fields.py       # Run database migration

# Clean Python cache
find backend -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find backend -type f -name "*.pyc" -delete
```

### Database Operations

**SQLite (Default):**
```bash
# Database file: backend/gemixity.db
# Automatically created on first run
```

**PostgreSQL Migration:**
```bash
cd backend
python3 migrate_to_postgres.py
```

**Add User Authentication Fields:**
```bash
cd backend
python3 migrate_add_user_fields.py
```

---

## 🎯 Advanced Features

### Pro Search Mode

Enable deep research with comprehensive multi-source synthesis:

```typescript
// Frontend usage
const { search } = useStreamingSearch();
search(query, undefined, { proSearch: true });
```

**Pro Search provides:**
- Fetches 10 high-quality sources (Google API free tier limit)
- Uses more sources for comprehensive answers
- Deeper analysis with multiple perspectives
- Better section organization with markdown headers
- Longer, more detailed responses

### Focus Modes

Specialize search behavior for different use cases:

- **Web** (default) - General web search
- **Academic** - Scholarly articles, research papers, citations
- **Code** - Programming documentation, Stack Overflow, GitHub
- **Writing** - Style guides, grammar, creative writing
- **News** - Latest news with date filtering

### Search Filters

Apply advanced filters to narrow results:

```typescript
// Date filters
?date_filter=d1  // Past 24 hours
?date_filter=w1  // Past week
?date_filter=m1  // Past month
?date_filter=y1  // Past year

// Domain filters
?include_domains=wikipedia.org,github.com
?exclude_domains=pinterest.com,instagram.com

// File type filters
?file_type=pdf
?file_type=doc
```

### Authentication & Tiers

**Free Tier (Public Access):**
- IP-based rate limiting
- Configurable daily search limit
- All core features available

**Browser Pro Tier (Authenticated):**
- Unlimited searches
- No rate limiting
- Priority support
- Full feature access

**Authentication:**
```typescript
// Add headers to requests
headers: {
  'X-Browser-Auth': 'your_browser_api_key',
  'X-User-ID': 'unique_user_id'
}
```

---

## 🔧 Configuration

### Environment Variables Reference

#### Backend (.env)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GOOGLE_API_KEY` | ✅ Yes | - | Google AI Studio API key |
| `GOOGLE_SEARCH_ENGINE_ID` | ✅ Yes | - | Google Custom Search Engine ID |
| `GEMINI_MODEL` | No | `gemini-2.0-flash` | AI model version |
| `DATABASE_URL` | No | `sqlite:///./gemixity.db` | Database connection string |
| `FREE_TIER_DAILY_LIMIT` | No | `5` | Free tier daily search limit |
| `BROWSER_API_KEY` | No | - | Browser authentication key |
| `ADMIN_API_KEY` | No | - | Admin endpoint access key |
| `CORS_ORIGINS` | No | `http://localhost:3005` | Allowed CORS origins |
| `SERVER_PORT` | No | `8080` | Backend server port |
| `RATE_LIMIT_SEARCH` | No | `10/minute` | Search endpoint rate limit |
| `RATE_LIMIT_FOLLOWUP` | No | `20/minute` | Follow-up endpoint rate limit |

#### Frontend (.env.local)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `NEXT_PUBLIC_API_URL` | ✅ Yes | - | Backend API URL |

---

## 🐛 Troubleshooting

### Common Issues

**No sources appearing:**
- Check that Google Custom Search API key is valid
- Verify Search Engine ID is correct
- Check backend logs for API errors
- Ensure you haven't exceeded 100 queries/day (free tier)

**Grounding score warnings:**
- This is normal when AI provides conversational responses
- Sources still fetch correctly
- Check backend logs for actual grounding scores

**History chat restarts conversation:**
- This is now fixed in the latest version
- Make sure you have the updated `LayoutWithSidebar.tsx`

**Build errors:**
- Clear `.next` folder: `rm -rf .next`
- Delete `node_modules`: `rm -rf node_modules`
- Reinstall: `npm install`
- Rebuild: `npm run build`

**Database errors:**
- Check `DATABASE_URL` format
- For PostgreSQL: `postgresql://user:password@localhost/dbname`
- For SQLite: `sqlite:///./gemixity.db` (default)
- Run migrations if needed

**CORS errors:**
- Verify `CORS_ORIGINS` includes your frontend URL
- Check Next.js rewrites in `next.config.ts`
- Ensure backend is running on correct port

---

## 🚀 Deployment

### Vercel (Frontend - Recommended)

```bash
npm install -g vercel
vercel login
vercel
```

**Environment Variables:**
Set `NEXT_PUBLIC_API_URL` to your backend URL (e.g., `https://your-backend.render.com`)

### Render.com (Backend)

1. Create new Web Service
2. Connect your GitHub repository
3. Set build command: `pip install -r backend/requirements.txt`
4. Set start command: `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Add environment variables from `.env.example`

### Railway.app (Backend Alternative)

1. Create new project
2. Connect GitHub repository
3. Set root directory to `backend`
4. Add environment variables
5. Deploy automatically on push

### Database Hosting (Free Options)

- **Neon** - Serverless PostgreSQL (0.5GB free)
- **Supabase** - PostgreSQL with 500MB free
- **PlanetScale** - MySQL with 5GB free

### Redis Hosting (Optional)

- **Upstash** - Serverless Redis (10k requests/day free)
- **Redis Cloud** - 30MB free tier

---

## 📊 Performance

- **Frontend**: Optimized with Next.js 15 App Router
- **Backend**: Async FastAPI with connection pooling
- **Streaming**: Server-Sent Events (SSE) for real-time responses
- **Caching**: Query-based caching with TanStack Query
- **Database**: Indexed queries for fast lookups

**Typical Response Times:**
- Initial search: 2-4 seconds
- Follow-up: 1-3 seconds
- Thread loading: <100ms

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **Google Gemini AI** - Powerful language model
- **Next.js** - Amazing React framework
- **FastAPI** - High-performance Python framework
- **shadcn/ui** - Beautiful component library
- **Tailwind CSS** - Utility-first CSS framework

---

## 📞 Support & Contributing

**Issues or questions?**
1. Check the [Troubleshooting](#-troubleshooting) section
2. Review inline code documentation
3. Open an issue on GitHub

**Want to contribute?**
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

## 🗺️ Roadmap

- [ ] Problem #2: Improve AI grounding prompt
- [ ] Problem #3: Fix Pro Search source fetching logic
- [ ] Multi-language support
- [ ] Voice search integration
- [ ] Browser extension
- [ ] Mobile app (React Native)
- [ ] API rate limiting dashboard
- [ ] User accounts with preferences
- [ ] Collaborative thread sharing
- [ ] Export to PDF, Markdown

---

**Built with ❤️ using Next.js, FastAPI, and Google Gemini**

*Version 2.0.0 - Major update with RAG pipeline, citation engine, and security enhancements*
