---

<div align="center">

# 🔍 Document Q&A System

### A production-grade RAG pipeline — upload any document, ask any question
(For complete engineering notes, ref [Notes](Notes.md))

![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-4.2-092E20?style=for-the-badge&logo=django&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-7-DC382D?style=for-the-badge&logo=redis&logoColor=white)
![Celery](https://img.shields.io/badge/Celery-5.3-37814A?style=for-the-badge&logo=celery&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)

<br/>

> Upload a PDF, TXT, DOCX, CSV, or PPTX → ask a natural language question → get a precise, context-aware answer powered by vector search and an LLM.

<br/>

[Features](#-features) · [Quick Start](#-quick-start) · [API](#-api-reference) · [Useful Commands](#-useful-commands) · [Roadmap](#-roadmap)

</div>

---

## ✨ Features

- 📄 **Multi-format ingestion** — upload TXT, PDF, DOCX, CSV, PPTX files via REST API
- ✂️ **Smart chunking** — LangChain `RecursiveCharacterTextSplitter` preserves sentence and paragraph boundaries
- 🧠 **Semantic embeddings** — HuggingFace `all-MiniLM-L6-v2` converts text to 384-dim vectors locally, no API key needed
- ⚡ **Async processing** — Celery + Redis handles chunking and embedding in the background, API returns instantly
- 🔎 **Vector similarity search** — pgvector IVFFlat index for fast approximate nearest-neighbor retrieval
- 🗄️ **Semantic query caching** — Redis caches results to avoid redundant LLM calls, returns in <10ms on cache hit
- 📊 **Query logging** — every question, answer, latency, and retrieval metadata stored for evaluation
- 🚀 **Production-ready serving** — Gunicorn + Nginx for multi-process concurrent request handling
- 🐳 **Fully containerized** — one command to spin up the entire stack

---

## 🚀 Quick Start

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) installed and running
- Git

### 1. Clone the repository

```bash
git clone https://github.com/your-username/rag-pipeline.git
cd rag-pipeline
```

### 2. Set up environment

```bash
cp .env.example .env
```

Open `.env` and set your values:

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

POSTGRES_DB=docqa_db
POSTGRES_USER=your-db-user
POSTGRES_PASSWORD=your-db-password

REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

GROQ_API_KEY=your-groq-api-key
GEMINI_API_KEY=your-gemini-api-key
```

### 3. Create media directory

```bash
mkdir -p media/documents
```

### 4. Start the stack

```bash
docker compose up --build -d
```

### 5. Run migrations

```bash
docker compose exec web python manage.py migrate
```

### 6. Create admin user

```bash
docker compose exec web python manage.py createsuperuser
```

### 7. Verify

```bash
curl http://localhost:8000/api/documents/
# ✅ {"count":0,"next":null,"previous":null,"results":[]}
```

---

## 📡 API Reference

### Upload a Document

```bash
curl -X POST http://localhost:8000/api/documents/ \
  -F "title=My Document" \
  -F "file=@/path/to/file.pdf"
```

**Response:**
```json
{
  "id": 1,
  "title": "My Document",
  "status": "pending",
  "chunk_count": 0,
  "created_at": "2024-01-01T00:00:00Z"
}
```

### Check Document Status

```bash
curl http://localhost:8000/api/documents/1/
```

**Response:**
```json
{
  "id": 1,
  "title": "My Document",
  "status": "done",
  "chunk_count": 42,
  "created_at": "2024-01-01T00:00:00Z"
}
```

Status values: `pending` → `processing` → `done` | `failed`

### Query a Document

```bash
curl -X POST http://localhost:8000/api/query/ \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the refund policy?", "document_id": 1}'
```

**Response:**
```json
{
  "answer": "According to [Source 1], the refund policy allows returns within 30 days...",
  "sources": [
    { "chunk_index": 3, "content": "Refunds are accepted within 30 days...", "distance": 0.21 }
  ],
  "latency_ms": 1340,
  "cached": false
}
```

### List All Documents

```bash
curl http://localhost:8000/api/documents/
```

### Delete a Document

```bash
curl -X DELETE http://localhost:8000/api/documents/1/
```

### Admin Panel

```
http://localhost:8000/admin/
```

---

## 🛠 Useful Commands

### Stack Management

```bash
# Start all services in background
docker compose up -d

# Start and rebuild images (after code/dependency changes)
docker compose up --build -d

# Stop all services
docker compose down

# Stop and delete all volumes (wipe database completely)
docker compose down -v

# View status of all containers
docker compose ps

# Restart a single service
docker compose restart web
docker compose restart celery
```

### Logs

```bash
# Stream logs from all services
docker compose logs -f

# Logs from a specific service
docker compose logs -f web
docker compose logs -f celery
docker compose logs -f db

# Last 100 lines from celery
docker compose logs --tail=100 celery
```

### Django

```bash
# Run migrations
docker compose exec web python manage.py migrate

# Create a new migration after model changes
docker compose exec web python manage.py makemigrations

# Show migration status
docker compose exec web python manage.py showmigrations

# Create superuser
docker compose exec web python manage.py createsuperuser

# Open Django shell
docker compose exec web python manage.py shell

# Collect static files
docker compose exec web python manage.py collectstatic --noinput
```

### Database

```bash
# Open PostgreSQL shell
docker compose exec db psql -U your-db-user -d docqa_db

# Count total chunks stored
docker compose exec db psql -U your-db-user -d docqa_db \
  -c "SELECT COUNT(*) FROM documents_documentchunk;"

# Check pgvector extension is installed
docker compose exec db psql -U your-db-user -d docqa_db \
  -c "SELECT * FROM pg_extension WHERE extname = 'vector';"

# Wipe all documents and chunks (keep tables)
docker compose exec db psql -U your-db-user -d docqa_db \
  -c "TRUNCATE documents_document, documents_documentchunk, documents_querylog CASCADE;"
```

### Celery

```bash
# Check active Celery workers
docker compose exec celery celery -A docqa inspect active

# Check queued/reserved tasks
docker compose exec celery celery -A docqa inspect reserved

# Purge all pending tasks from queue
docker compose exec celery celery -A docqa purge

# Manually trigger document reprocessing (from Django shell)
docker compose exec web python manage.py shell
>>> from documents.tasks import process_document_task
>>> process_document_task.delay(document_id=1)
```

### Redis

```bash
# Open Redis CLI
docker compose exec redis redis-cli

# List all cached query keys
docker compose exec redis redis-cli KEYS "rag:query:*"

# Count cached queries
docker compose exec redis redis-cli KEYS "rag:query:*" | wc -l

# Flush only cached RAG queries
docker compose exec redis redis-cli KEYS "rag:query:*" | \
  xargs docker compose exec -T redis redis-cli DEL

# Flush entire Redis cache
docker compose exec redis redis-cli FLUSHALL
```

### Testing

```bash
# Run all tests
docker compose exec web python manage.py test

# Run a specific test file
docker compose exec web python manage.py test documents.tests.test_pipeline

# Run a specific test case
docker compose exec web python manage.py test documents.tests.test_pipeline.PipelineTestCase

# Run with verbosity
docker compose exec web python manage.py test --verbosity=2
```

---

## 📁 Project Structure

```
rag_pipeline/
├── 🐳 Dockerfile
├── 🐳 docker-compose.yml
├── 📦 requirements.txt
├── ⚙️  manage.py
├── 🔒 .env.example
│
├── docqa/                          # Django project config
│   ├── settings.py                 # all configuration
│   ├── urls.py                     # root URL routing
│   ├── celery.py                   # async task queue setup
│   └── wsgi.py
│
└── documents/                      # core app
    ├── models.py                   # Document, DocumentChunk, QueryLog
    ├── serializers.py              # DRF serializers
    ├── views.py                    # API ViewSets
    ├── urls.py                     # app URL routing
    ├── tasks.py                    # Celery async tasks
    ├── admin.py                    # Django admin config
    ├── migrations/
    │   └── 0001_initial.py         # pgvector + table setup
    └── services/
        ├── parser.py               # file reading (PDF, DOCX, CSV, PPTX)
        ├── chunker.py              # LangChain text splitter
        ├── embedder.py             # HuggingFace embeddings
        ├── llm.py                  # Groq/Gemini LLM calls
        ├── cache.py                # Redis query caching
        └── pipeline.py             # orchestrates parse→chunk→embed→store
```

---

## 🔑 Key Numbers

| Parameter | Value |
|---|---|
| Embedding model | `all-MiniLM-L6-v2` |
| Embedding dimensions | 384 |
| Chunk size | 512 characters (~128 tokens) |
| Chunk overlap | 64 characters (~16 tokens) |
| Cosine distance threshold | < 0.7 |
| Top-K retrieval | 5 chunks |
| IVFFlat lists | 100 (optimal up to 100K chunks) |
| Groq free tier | 14,400 req/day, 30 req/min |
| LLM temperature | 0 (deterministic) |
| Cache TTL | 3600s (1 hour) |

---

## 🔮 Roadmap

- [x] Document ingestion pipeline
- [x] Multi-format parsing — PDF, DOCX, TXT, CSV, PPTX
- [x] Async chunking and embedding via Celery
- [x] pgvector storage with IVFFlat index
- [x] Vector similarity search endpoint
- [x] LLM answer generation (Groq / Gemini)
- [x] Redis semantic query caching
- [x] Query logging with latency tracking
- [x] Production deployment with Gunicorn + Nginx
- [ ] Hybrid search (vector + BM25 keyword)
- [ ] RAGAS evaluation suite
- [ ] Query rewriting for better retrieval
- [ ] Streaming responses (SSE)
- [ ] JWT authentication + multi-tenancy
- [ ] HNSW index (faster than IVFFlat at scale)
- [ ] Monitoring with Prometheus + Grafana

---

## 🐛 Common Issues

| Error | Cause | Fix |
|---|---|---|
| `relation does not exist` | Migrations not run | `docker compose exec web python manage.py migrate` |
| `type vector does not exist` | pgvector extension missing | `docker compose down -v` → fix migration → restart |
| `expected 768 dimensions, not 384` | Model/field mismatch | Set `VectorField(dimensions=384)` everywhere |
| `No module named langchain.schema` | LangChain breaking change | `from langchain_core.messages import ...` |
| `model llama3-8b-8192 decommissioned` | Groq deprecated model | Use `llama-3.1-8b-instant` |
| `TimeoutError` during build | Slow network in container | Add `--timeout=120 --retries=5` to pip install in Dockerfile |
| `Not possible to fast-forward` | Diverged git branches | `git pull --rebase origin main` |