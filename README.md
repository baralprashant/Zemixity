# Zemixity

**AI-Powered Search** - A modern AI-powered search engine with conversational follow-ups, powered by Google's Gemini 2.0 Flash.

![Next.js](https://img.shields.io/badge/Next.js-15.5.4-black)
![Python](https://img.shields.io/badge/Python-3.13+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.118.0-green)
![TypeScript](https://img.shields.io/badge/TypeScript-5.0-blue)

## ✨ Features

- 🔍 **AI-Powered Search** - Intelligent search results using Google Gemini 2.0 Flash
- 💬 **Conversational Follow-ups** - Continue asking questions in context
- 📚 **Rich Source Cards** - Beautiful source previews with images and metadata
- 🎯 **Related Questions** - AI-generated follow-up suggestions
- 📝 **Thread Persistence** - Save and resume conversations
- 🎨 **Modern UI** - Clean, responsive design with smooth animations
- ⚡ **Fast & Efficient** - Built with Next.js 15 and React 19
- 🔐 **Rate Limited** - Protected API endpoints with slowapi

## 🏗️ Architecture

### Frontend
- **Framework**: Next.js 15.5.4 (App Router)
- **UI Library**: React 19.1.0
- **Styling**: Tailwind CSS 4.1
- **State Management**: TanStack Query
- **Animations**: Framer Motion

### Backend
- **Framework**: FastAPI
- **AI Model**: Google Gemini 2.0 Flash (with grounding)
- **Database**: PostgreSQL (with SQLite fallback)
- **Session Storage**: Redis (with in-memory fallback)
- **Rate Limiting**: slowapi

## 📋 Prerequisites

- **Node.js** 24.9.0 or higher
- **Python** 3.13 or higher
- **PostgreSQL** (optional - falls back to SQLite)
- **Redis** (optional - falls back to in-memory storage)
- **Google AI API Key** ([Get one here](https://aistudio.google.com/apikey))
- **Google Custom Search Engine ID** ([Create one here](https://programmablesearchengine.google.com/))

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/Gemixity.git
cd Gemixity
```

### 2. Frontend Setup

```bash
# Install dependencies
npm install

# Create frontend environment file
cp .env.local.example .env.local
# Edit .env.local and set NEXT_PUBLIC_API_URL=http://localhost:8000

# Run development server
npm run dev
```

The frontend will be available at [http://localhost:3000](http://localhost:3000)

### 3. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Edit .env and add your API keys
nano .env  # or use your preferred editor
```

**Required environment variables:**
```bash
GOOGLE_API_KEY=your_google_api_key_here
GOOGLE_SEARCH_ENGINE_ID=your_search_engine_id_here
```

**Optional environment variables:**
```bash
DATABASE_URL=postgresql://localhost/gemixity  # Defaults to SQLite
REDIS_HOST=localhost
REDIS_PORT=6379
```

### 4. Run the Backend

```bash
# Make sure you're in the backend directory with venv activated
python3 main.py

# Or use uvicorn directly
uvicorn main:app --reload --port 8000
```

The backend API will be available at [http://localhost:8000](http://localhost:8000)

### 5. Verify Everything Works

1. Open [http://localhost:3000](http://localhost:3000)
2. Try searching for something like "What is Next.js?"
3. Ask follow-up questions
4. Check the sidebar for conversation history

## 🔑 Getting API Keys

### Google AI API Key

1. Visit [Google AI Studio](https://aistudio.google.com/apikey)
2. Click "Create API Key"
3. Copy the key and add to `backend/.env`

### Google Custom Search Engine ID

1. Visit [Programmable Search Engine](https://programmablesearchengine.google.com/)
2. Click "Add" to create a new search engine
3. Set "Search the entire web" option
4. Copy the Search Engine ID and add to `backend/.env`

## 📦 Project Structure

```
Gemixity/
├── src/                          # Frontend source
│   ├── app/                      # Next.js app directory
│   │   ├── page.tsx             # Home page
│   │   ├── search/page.tsx      # Search results page
│   │   ├── layout.tsx           # Root layout
│   │   └── globals.css          # Global styles
│   ├── components/              # React components
│   │   ├── SearchInput.tsx
│   │   ├── SearchResults.tsx
│   │   ├── ConversationMessage.tsx
│   │   ├── PersistentSidebar.tsx
│   │   └── ui/                  # shadcn/ui components
│   └── hooks/                   # Custom React hooks
├── backend/                     # Backend API
│   ├── main.py                 # FastAPI application
│   ├── models.py               # SQLAlchemy models
│   ├── database.py             # Database configuration
│   ├── requirements.txt        # Python dependencies
│   └── .env.example           # Environment template
├── public/                     # Static assets
└── package.json               # Node.js dependencies
```

## 🛠️ Development

### Frontend Commands

```bash
npm run dev        # Start development server
npm run build      # Build for production
npm run start      # Start production server
npm run lint       # Run ESLint
```

### Backend Commands

```bash
python3 main.py                    # Run backend server
uvicorn main:app --reload          # Run with hot reload
python3 -m pytest                  # Run tests (if available)
```

### Database Migration

To migrate from SQLite to PostgreSQL:

```bash
cd backend
python3 migrate_to_postgres.py
```

## 🎨 Features in Detail

### Conversation Threads
- Each search creates a new thread
- Threads are automatically titled based on the first query
- Threads persist in the database
- Pin important threads to keep them at the top
- Rename threads for better organization
- Delete threads you no longer need

### Smart Follow-ups
- Context-aware responses
- Maintains conversation history
- Sources are fetched for each follow-up
- Related questions generated by AI

### Source Cards
- Rich previews with images
- Favicon and domain display
- Publication dates when available
- Collapsible source sections
- Direct links to original content

## 🔧 Configuration

### Next.js Configuration

The API proxy is configured in `next.config.ts`:

```typescript
async rewrites() {
  return [
    {
      source: '/api/:path*',
      destination: 'http://localhost:8000/api/:path*',
    },
  ];
}
```

### Backend Configuration

Rate limiting is configured in `backend/main.py`:
- Search endpoint: 10 requests/minute
- Follow-up endpoint: 20 requests/minute

## 🐛 Troubleshooting

### Frontend Issues

**Build fails with Suspense error**
- This is fixed in the latest version
- Make sure you're using the updated `src/app/search/page.tsx`

**API requests fail**
- Ensure backend is running on port 8000
- Check Next.js rewrites configuration

### Backend Issues

**Redis connection fails**
- This is normal if Redis isn't installed
- The app automatically falls back to in-memory storage

**Database errors**
- Check DATABASE_URL in `.env`
- The app falls back to SQLite if PostgreSQL isn't available

**API key errors**
- Verify GOOGLE_API_KEY is set correctly
- Ensure the API key has access to Gemini API
- Check that Custom Search Engine ID is correct

## 📝 Environment Variables Reference

### Backend (.env)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GOOGLE_API_KEY` | ✅ Yes | - | Google AI API key |
| `GOOGLE_SEARCH_ENGINE_ID` | ✅ Yes | - | Google Custom Search Engine ID |
| `DATABASE_URL` | ❌ No | `sqlite:///./gemixity.db` | Database connection string |
| `REDIS_HOST` | ❌ No | `localhost` | Redis server host |
| `REDIS_PORT` | ❌ No | `6379` | Redis server port |
| `REDIS_DB` | ❌ No | `0` | Redis database number |

## 🚀 Deployment

### Free Hosting Options

**Frontend (Vercel - Recommended)**
```bash
npm install -g vercel
vercel login
vercel
```
Set `NEXT_PUBLIC_API_URL` environment variable to your backend URL.

**Backend Options**
- **Render.com** - 750 hrs/month free
- **Railway.app** - $5 free credit/month
- **Fly.io** - Free tier available

**Database (Free)**
- **Neon** - PostgreSQL with 0.5GB free tier
- **Upstash** - Redis with 10k requests/day free

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Google Gemini AI for the powerful language model
- Next.js team for the amazing framework
- shadcn/ui for the beautiful component library
- FastAPI for the excellent Python framework

## 📞 Support

If you encounter any issues or have questions:
1. Check the [Troubleshooting](#-troubleshooting) section
2. Open an issue on GitHub
3. Review the inline documentation in the code

---

**Built with ❤️ using Next.js and Google Gemini**
