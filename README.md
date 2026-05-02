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
GEMINI_API_KEY=your-api-key

GROQ_API_KEY=your-api-key
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

## Part 10 — File Parsing

### Why a dedicated parser module
parser.py knows: how to read files
pipeline.py knows: how to orchestrate ingestion
chunker.py knows: how to split text
embedder.py knows: how to generate vectors

Each module has one job. This is the Single Responsibility Principle.
Adding EPUB support = add _read_epub() to parser.py. Nothing else changes.
Upgrading the chunking strategy = change chunker.py. Parser is untouched.

### PDF parsing with pdfplumber

PDFs are not plain text files. They are a binary format that describes
how to render text on a page — positions, fonts, coordinates.
pdfplumber reads this binary format and extracts the text content.

The empty check:
```python
if not result.strip():
    raise ValueError("No text found in PDF...")
```
Scanned PDFs are images disguised as PDFs. The scanner took a photo of
a page and saved it as PDF. There is no text — just pixels.
pdfplumber returns empty string. Without the check, you'd store a document
with zero chunks and return "I don't have enough information" for every query.
The explicit error tells the user to upload a text-based PDF or use OCR.

### Excel data_only=True

```python
wb = openpyxl.load_workbook(..., data_only=True)
```
Excel cells can contain formulas: =SUM(A1:A10) or values: 42.
data_only=True returns the computed value (42) not the formula string.
The LLM cannot interpret Excel formulas. It needs the actual values.

### The seek(0, 2) trick for file size

```python
file_field.seek(0, 2)    # seek to end of file
file_size = file_field.tell()  # position = file size in bytes
file_field.seek(0)       # seek back to beginning
```
seek(0, 2): the 2 means "seek relative to end". Position 0 from the end
= the end of the file. tell() returns the current position = file size.
Then seek(0) resets so we can read the file normally.
This measures file size without reading the entire file into memory first.
For a 500MB file, this saves significant memory.

---

## Part 11 — Testing Strategy

### Why mock embed_texts in tests

```python
@patch('documents.services.pipeline.embed_texts')
def test_pipeline_creates_chunks(self, mock_embed):
    mock_embed.return_value = [[0.0] * 384] * 10
```

The real embed_texts downloads a 90MB model and runs neural network inference.
In tests you want: fast (milliseconds not minutes), no network, no GPU.
mock_embed replaces the real function with one that returns fake vectors instantly.

The test verifies the LOGIC (chunks are created, status is updated)
without caring about the IMPLEMENTATION (actual embedding values).
This is the right level of abstraction for unit tests.

### Testing the failure path

```python
@patch('documents.services.pipeline.embed_texts')
def test_failed_embed_rolls_back(self, mock_embed):
    mock_embed.side_effect = Exception("Embedding service down")
    ...
    self.assertEqual(DocumentChunk.objects.count(), 0)
```

Testing failure paths is MORE important than testing happy paths.
Happy paths work until they don't. Failure handling is what separates
production systems from hobby projects.
This test verifies transaction.atomic() actually works.
Without this test, you might accidentally remove the atomic() wrapper
and not notice until a production incident.

### The testing pyramid for this project

![testing_pyramid](images/rag_test.png)

Your tests/test_pipeline.py covers unit tests.
Unit tests are the foundation — fast, focused, catch logic errors early.

---

## Part 12 — Production Considerations

### What's different in production vs development

Development (what you have):
manage.py runserver  ← single-threaded, not for concurrent users
DEBUG=True           ← verbose error pages with stack traces
.:/app volume mount  ← live code reload
SQLite ok for tests  ← but you use PostgreSQL (good)

Production (next steps):
gunicorn --workers 3  ← multi-process, handles concurrent requests
DEBUG=False           ← no stack traces exposed to users
COPY . . in Dockerfile ← code baked into image, no volume mount
HTTPS with SSL cert   ← encrypt all traffic
ALLOWED_HOSTS set     ← only accept requests to your domain

### Why gunicorn not runserver

Django's runserver is single-threaded.
User A makes request → server is busy → User B waits.
One slow LLM call blocks everyone.

Gunicorn spawns multiple worker processes:
workers = (2 × CPU_cores) + 1
Each worker handles one request independently.
3 workers = 3 simultaneous requests, no blocking.

### Environment variables vs hardcoded config

Never hardcode:
```python
# BAD — hardcoded in code, committed to git
DATABASES = {'default': {'PASSWORD': 'mysecretpassword'}}
```

Always use environment variables:
```python
# GOOD — read from environment
DATABASES = {'default': {'PASSWORD': os.getenv('POSTGRES_PASSWORD')}}
```

WHY: credentials in git history are a permanent security risk.
Even if you delete the file, git history preserves it.
Environment variables are injected at runtime and never touch the codebase.

### The .env.example pattern

.env — real secrets, in .gitignore, never committed
.env.example — fake values, committed to git
.env:          POSTGRES_PASSWORD=my_actual_password_123
.env.example:  POSTGRES_PASSWORD=your-db-password-here

New developer clones repo → cp .env.example .env → fills in real values.
Everyone knows what variables are needed without seeing the actual secrets.

---

## Part 13 — What Production Systems Like Claude Actually Do

### Layer 1 — Training (permanent knowledge)

The LLM (Claude, GPT-4, Llama) was trained on trillions of tokens.
This bakes in general knowledge about the world, coding, science, language.
This is NOT RAG. This is the model's foundation.

### Layer 2 — RAG (document-specific knowledge)

For company-specific data, recent events, private documents —
the system retrieves relevant chunks and adds them to the prompt.
This is exactly what you built.

### Layer 3 — Context window (conversation memory)

Claude has a 200K token context window.
Everything in the current conversation + retrieved docs fits here.
This is "working memory" — temporary, per-conversation.

### Layer 4 — Tools (dynamic information)

Claude can call external APIs, run code, search the web.
The model decides when a tool is needed and what to do with the result.
This is beyond RAG — it's agentic behavior.

### What your project implements vs production
Your project:

![production_features](images/rag_prod_comp.png)


Production additions:
○ Query rewriting (LLM rewrites question for better retrieval)
○ Hybrid search (vector + BM25 keyword)
○ Reranker model (CrossEncoder reorders retrieved chunks)
○ Context compression (summarize chunks before LLM)
○ RAGAS evaluation (automated quality scoring)
○ Streaming responses (SSE for real-time output)
○ Multi-tenancy (per-user document isolation)
○ HNSW index (faster than IVFFlat)
○ Monitoring (Prometheus + Grafana)
○ Rate limiting
○ Authentication (JWT tokens)

The gap is real but smaller than it looks.
Your architecture is identical. The additions are incremental improvements.
A senior engineer could take your codebase and add these features.
That is the mark of good foundational architecture.

---

## Part 14 — Key Numbers to Memorize
EMBEDDINGS
all-MiniLM-L6-v2 dimensions:     384
OpenAI text-embedding-3-small:   1536
OpenAI text-embedding-3-large:   3072
Google text-embedding-004:        768
CHUNKING
Your chunk_size:                 512 characters ≈ 128 tokens
Your chunk_overlap:              64 characters ≈ 16 tokens
1 token ≈ 4 characters (rough average for English)
PGVECTOR
IVFFlat lists=100:               optimal up to 100K chunks
IVFFlat lists=1000:              optimal up to 1M chunks
Cosine distance range:           0.0 (identical) to 2.0 (opposite)
Good retrieval threshold:        distance < 0.7
LLM CONTEXT WINDOWS
Llama 3.1 8B (Groq):             8K tokens
GPT-4o:                          128K tokens
Claude 3.5 Sonnet:               200K tokens
Gemini 1.5 Pro:                  1M tokens
GROQ FREE TIER
llama-3.1-8b-instant:           14,400 requests/day
Rate limit:                      30 requests/minute
DOCKER
web container port:              8000
db container port:               5432
redis container port:            6379

---

## Part 15 — Common Bugs You Hit and Why They Happened

### "relation documents_document does not exist"

Django's tables are created by migrations.
docker compose up starts the server but does NOT run migrations.
Django intentionally separates "start server" from "modify database".
Fix: docker compose exec web python manage.py migrate

### "type vector does not exist"

pgvector extension was not installed in PostgreSQL.
VectorExtension() in migrations creates it.
If migrations ran before VectorExtension() was added — re-run from scratch.
Fix: docker compose down -v → fix migration → docker compose up → migrate

### "expected 768 dimensions, not 384"

VectorField(dimensions=768) in models.py but embedding model outputs 384.
The column and the model must match exactly.
all-MiniLM-L6-v2 outputs 384, not 768.
Fix: VectorField(dimensions=384) everywhere.

### "No module named langchain.schema"

LangChain moved classes between packages in version 0.1+.
langchain.schema no longer exists.
Fix: from langchain_core.messages import HumanMessage, SystemMessage

### "model llama3-8b-8192 has been decommissioned"

Groq deprecated this model.
Fix: model='llama-3.1-8b-instant'

### pip dependency conflicts

langchain 0.2.0 requires langchain-core < 0.3.0
langchain-google-genai 4.x requires langchain-core >= 1.2.0
They cannot coexist.
Fix: upgrade all langchain packages together. Let pip resolve versions.
Then freeze: pip freeze > requirements.txt

### "TimeoutError" during docker build

ChromeOS Linux network can be slow/unstable inside containers.
pip download times out mid-file.
Fix: --timeout=120 --retries=5 in Dockerfile RUN pip install command.

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

