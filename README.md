# Zemixity 🔍

**Next-Generation AI Search Engine** - A powerful AI-powered search platform with advanced RAG pipeline, inline citations, and conversational intelligence.

![Next.js](https://img.shields.io/badge/Next.js-15.5.4-black)
![Python](https://img.shields.io/badge/Python-3.13+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.118.0-green)
![TypeScript](https://img.shields.io/badge/TypeScript-5.0-blue)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## ✨ Key Features

### 🎯 **Core Capabilities**
- **Advanced RAG Pipeline** - Multi-stage retrieval, ranking, and source quality filtering
- **Inline Citations** - Citation numbers [1][2] linked to sources
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

**Built with ❤️**

*Version 2.0.0 - Major update with RAG pipeline, citation engine, and security enhancements*
