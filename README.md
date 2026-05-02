---

<div align="center">

# 🔍 Document Q&A System

### A production-grade RAG pipeline — upload any document, ask any question 
(For complete engineering notes, ref [Notes](Notes.md)).

![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-4.2-092E20?style=for-the-badge&logo=django&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-7-DC382D?style=for-the-badge&logo=redis&logoColor=white)
![Celery](https://img.shields.io/badge/Celery-5.3-37814A?style=for-the-badge&logo=celery&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)

<br/>

> Upload a PDF, TXT, or DOCX → ask a natural language question → get a precise, context-aware answer powered by vector search and an LLM.

<br/>

[Features](#-features) · [Quick Start](#-quick-start) · [API](#-api-reference) · [Commands](#-useful-commands)

</div>

---

## ✨ Features

- 📄 **Document ingestion** — upload TXT, PDF, DOCX files via REST API
- ✂️ **Smart chunking** — LangChain `RecursiveCharacterTextSplitter` preserves sentence and paragraph boundaries
- 🧠 **Semantic embeddings** — HuggingFace `all-MiniLM-L6-v2` converts text to 384-dim vectors locally, no API key needed
- ⚡ **Async processing** — Celery + Redis handles chunking and embedding in the background, API returns instantly
- 🔎 **Vector similarity search** — pgvector IVFFlat index for fast approximate nearest-neighbor retrieval
- 📊 **Query logging** — every question, answer, latency, and RAGAS score stored for evaluation
- 🐳 **Fully containerized** — one command to spin up the entire stack

---

<!-- ## 🏗 Architecture
┌─────────────────────────────────────────────────────────────────┐
│                        INGESTION PIPELINE                        │
│                                                                   │
│  POST /api/documents/                                             │
│         │                                                         │
│         ▼                                                         │
│  Django saves file ──► Celery Task ──► LangChain Chunker         │
│                                               │                   │
│                                               ▼                   │
│                                      HuggingFace Embedder        │
│                                               │                   │
│                                               ▼                   │
│                                    pgvector (PostgreSQL)          │
└─────────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────────┐
│                         QUERY PIPELINE                           │
│                                                                   │
│  POST /api/query/                                                 │
│         │                                                         │
│         ▼                                                         │
│  Embed Question ──► pgvector Search ──► Top-K Chunks ──► LLM    │
│                                                           │       │
│                                                           ▼       │
│                                                       Answer      │
└─────────────────────────────────────────────────────────────────┘

### Docker Services
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│     web      │────▶│      db      │     │    redis     │
│   Django     │     │  PostgreSQL  │     │   broker     │
│   :8000      │     │  + pgvector  │     │   :6379      │
└──────────────┘     └──────────────┘     └──────────────┘
│                    ▲                    ▲
│                    │                    │
▼                    │                    │
┌──────────────┐             │                    │
│    celery    │─────────────┴────────────────────┘
│    worker    │
└──────────────┘

---

## 📁 Project Structure
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
├── chunker.py              # LangChain text splitter
├── embedder.py             # HuggingFace embeddings
└── pipeline.py            # orchestrates chunk→embed→store -->

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
POST /api/documents/

curl -X POST http://localhost:8000/api/documents/ \
  -F "title=My Document" \
  -F "file=@/path/to/file.txt"
```

```json
{
  "id": 1,
  "title": "My Document",
  "status": "pending",
  "chunk_count": 0,
  "created_at": "2026-04-26T10:00:00Z"
}
```

### Check Processing Status

```bash
GET /api/documents/{id}/

curl http://localhost:8000/api/documents/1/
```

| Status | Meaning |
|--------|---------|
| `pending` | uploaded, waiting for Celery |
| `processing` | chunking and embedding in progress |
| `done` | chunks and embeddings stored, ready to query |
| `failed` | pipeline error, check Celery logs |

### View Chunks

```bash
GET /api/documents/{id}/chunks/

curl http://localhost:8000/api/documents/1/chunks/
```

### List All Documents

```bash
GET /api/documents/

curl http://localhost:8000/api/documents/
```

### Reprocess a Document

```bash
POST /api/documents/{id}/reprocess/

curl -X POST http://localhost:8000/api/documents/1/reprocess/
```

---

## 🗄 Database Schema

### Document
| Column | Type | Description |
|--------|------|-------------|
| `id` | BigInt | primary key |
| `title` | VARCHAR(255) | document name |
| `file` | FileField | path to uploaded file |
| `status` | VARCHAR(20) | pending / processing / done / failed |
| `created_at` | Timestamp | upload time |

### DocumentChunk
| Column | Type | Description |
|--------|------|-------------|
| `id` | BigInt | primary key |
| `document` | FK → Document | parent document |
| `chunk_index` | Integer | position within document |
| `content` | Text | raw chunk text |
| `embedding` | vector(384) | semantic embedding |
| `metadata` | JSONB | page number, section etc |

### QueryLog
| Column | Type | Description |
|--------|------|-------------|
| `id` | BigInt | primary key |
| `query` | Text | user's question |
| `answer` | Text | LLM generated answer |
| `retrieved_chunk_ids` | JSONB | chunks used as context |
| `latency_ms` | Integer | total pipeline time |
| `ragas_score` | Float | evaluation score |

---

## 🛠 Useful Commands

```bash
# ── Logs ──────────────────────────────────────────
docker compose logs -f web          # Django logs
docker compose logs -f celery       # task processing logs
docker compose logs -f db           # PostgreSQL logs

# ── Django ────────────────────────────────────────
docker compose exec web python manage.py shell
docker compose exec web python manage.py showmigrations

# ── Database ──────────────────────────────────────
docker compose exec db psql -U docqa_user -d docqa_db

# verify pgvector extension
docker compose exec db psql -U docqa_user -d docqa_db -c "\dx"

# inspect chunks and embeddings
docker compose exec db psql -U docqa_user -d docqa_db -c \
  "SELECT id, chunk_index, LEFT(content, 60) FROM documents_documentchunk;"

# ── Container management ──────────────────────────
docker compose up -d                # start in background
docker compose down                 # stop all containers
docker compose down -v              # stop and wipe database
docker compose restart celery       # restart celery worker
```

---

## ⚙️ Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `SECRET_KEY` | Django cryptographic key | ✅ |
| `DEBUG` | Enable debug mode | ✅ |
| `ALLOWED_HOSTS` | Comma-separated allowed hosts | ✅ |
| `POSTGRES_DB` | Database name | ✅ |
| `POSTGRES_USER` | Database username | ✅ |
| `POSTGRES_PASSWORD` | Database password | ✅ |
| `REDIS_URL` | Redis connection string | ✅ |
| `CELERY_BROKER_URL` | Celery message broker URL | ✅ |
| `CELERY_RESULT_BACKEND` | Celery result storage URL | ✅ |

---

## 🔮 Roadmap

- [x] Document ingestion pipeline
- [x] Async chunking and embedding via Celery
- [x] pgvector storage with IVFFlat index
- [x] Vector similarity search endpoint
- [ ] Hybrid search (vector + BM25 keyword)
- [ ] LLM answer generation
- [x] Redis semantic query caching
- [ ] RAGAS evaluation suite
- [x] PDF, DOC, PPT, CSV parsing supports
- [x] Production deployment with Gunicorn + Nginx

---

