# Week 1 — Deep Notes: Chunking, Embeddings & the RAG Foundation

---

## What You Built This Week

You built the **memory system** for an AI Q&A application.

Think of it like this. Imagine you hire a very smart assistant (the LLM) but
this assistant has one problem — they can only read about 10 pages at a time.
You give them a 500-page book and ask a question. They cannot read all 500 pages.

So you build a system that:
1. Reads the entire book once upfront
2. Breaks it into small notes (chunks)
3. Tags each note with a "topic fingerprint" (embedding/vector)
4. When a question comes in — finds the 5 most relevant notes instantly
5. Hands those 5 notes to the assistant
6. Assistant reads just those 5 pages and answers perfectly

That is RAG. That is what you built the foundation of this week.

---

## Part 1 — Chunking (The Art of Splitting Text)

### What is chunking?

Chunking is breaking a large document into smaller pieces so that:
- Each piece fits inside an LLM's context window
- Each piece is small enough to be "about one thing"
- Retrieved chunks are precise — not entire chapters

### What you used: RecursiveCharacterTextSplitter

```python
splitter = RecursiveCharacterTextSplitter(
    chunk_size=512,
    chunk_overlap=64,
    separators=["\n\n", "\n", ". ", " ", ""],
)
```

### Understanding chunk_size=512

This means each chunk is at most 512 characters long.

Example — imagine this paragraph (125 chars):
Django is a Python framework. It has an ORM. The ORM lets you write
database queries in Python instead of SQL. This saves a lot of time.

With chunk_size=512 this fits in one chunk.
With chunk_size=50 it would be split into multiple chunks.

512 characters is roughly 80-100 words — about the size of a short paragraph.
That is enough context to answer a specific question but small enough to
be precise.

### Understanding chunk_overlap=64

Imagine your document has this text split across a boundary:
...Django's ORM is very powerful. It supports | PostgreSQL, MySQL, and SQLite.
↑
chunk boundary

Without overlap — chunk 1 ends at "powerful." and chunk 2 starts at
"PostgreSQL". If someone asks "what databases does Django support?" —
the answer is in chunk 2 but the context "Django's ORM" is in chunk 1.
The answer seems disconnected.

With overlap=64 — chunk 2 starts 64 characters BEFORE its boundary.
So chunk 2 includes "...It supports PostgreSQL, MySQL, and SQLite."
Full context preserved.
Chunk 1: "...Django's ORM is very powerful. It supports"
Chunk 2: "It supports PostgreSQL, MySQL, and SQLite..."
↑
64 chars overlap

### Understanding separators=["\n\n", "\n", ". ", " ", ""]

This is the priority order for WHERE to cut. The splitter tries each
separator in order:
"\n\n"  →  paragraph break (best cut point — most natural)
"\n"    →  line break
". "    →  sentence end
" "     →  word boundary
""      →  character (last resort — never ideal)

So if your chunk_size says "cut here" but it falls in the middle of a word,
the splitter looks backwards for the nearest sentence end, then line break,
then paragraph break. Result: chunks always end at natural boundaries.

This is why it is called RECURSIVE — it recursively tries each separator.

### What you got in the database

For your test.txt with 4 paragraphs you got roughly 3-4 chunks like:
Chunk 0: "Django is a high-level Python web framework that encourages
rapid development. It follows the Model-Template-View
architectural pattern. Django includes an ORM..."
Chunk 1: "pgvector is a PostgreSQL extension that adds vector similarity
search. It allows storing and querying high-dimensional
vectors directly in PostgreSQL..."
Chunk 2: "RAG stands for Retrieval Augmented Generation. It works by
retrieving relevant document chunks and passing them to
an LLM. The LLM generates an answer..."
Chunk 3: "Celery is a distributed task queue for Python. It handles
background jobs like sending emails or processing files..."

Each chunk is self-contained enough to answer a specific question.

---

## Part 2 — Embeddings (Teaching Machines to Understand Meaning)

### The core problem embeddings solve

Computers cannot understand meaning. They only understand numbers.

"Dog" and "puppy" — a computer sees two different strings. No connection.
A human knows they are related.

Embeddings solve this by converting text to numbers in a special way —
where similar meanings get similar numbers.

### What is a vector?

A vector is just a list of numbers. For example:
"Django is a framework"  →  [0.12, -0.45, 0.89, 0.23, -0.67, ...]
384 numbers total

384 numbers — that is what all-MiniLM-L6-v2 produces for any text,
whether it is 3 words or 300 words. Always exactly 384 numbers.

These 384 numbers are NOT random. Each number captures some aspect of
meaning. The model was trained on billions of sentences so it learned
which aspects of meaning matter.

### Why similar texts get similar vectors
"Django is a Python framework"    →  [0.12, -0.45, 0.89, ...]
"Flask is a Python web framework" →  [0.11, -0.43, 0.91, ...]
"I love eating pizza"             →  [0.87,  0.23, -0.34, ...]

The first two are similar (both about Python frameworks) so their
vectors are close to each other in 384-dimensional space.
The third is completely different so its vector is far away.

This is the magic. You never told the model "Django and Flask are similar".
It learned this from training data.

### The model you used: all-MiniLM-L6-v2

- Made by sentence-transformers (HuggingFace)
- Outputs 384-dimensional vectors
- ~90MB model size — runs on CPU, no GPU needed
- Fast — embeds hundreds of chunks in seconds
- Free — runs entirely locally, no API calls
- Good quality for English text

The "L6" means it has 6 transformer layers. More layers = better quality
but slower. L6 is the sweet spot for production use.

### What cosine similarity means

When you ask a question, we need to find which chunks are most relevant.
We do this by measuring the "angle" between vectors.
Question vector:  [0.12, -0.45, 0.89, ...]
Chunk 1 vector:   [0.11, -0.43, 0.91, ...]  ← very similar, small angle
Chunk 2 vector:   [0.87,  0.23, -0.34, ...]  ← very different, large angle

Cosine similarity = 1.0 means identical meaning
Cosine similarity = 0.0 means completely unrelated
Cosine similarity = -1.0 means opposite meaning

pgvector uses the <=> operator to find the chunks with the smallest
cosine distance (most similar) to your question. This is the entire
retrieval mechanism.

### The IVFFlat index you created

```sql
CREATE INDEX USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
```

Without the index — finding the most similar chunk requires comparing
your question vector against EVERY chunk in the database one by one.
1000 chunks = 1000 comparisons. 1 million chunks = 1 million comparisons.
This is called a brute-force scan. Too slow.

IVFFlat (Inverted File Flat) solves this:
1. During index creation — clusters all vectors into 100 groups
2. During search — only searches the closest 1-2 groups, not all 100
3. Result — searches 1% of the data but finds 95%+ of the right answers

This is called Approximate Nearest Neighbor (ANN) search.
Slightly less accurate than brute force but 100x faster at scale.

---

## Part 3 — What You Built vs What Production AI Uses

### Your stack this week
You:         all-MiniLM-L6-v2  →  384 dimensions  →  pgvector IVFFlat
Cost:        Free
Speed:       Fast on CPU
Quality:     Good for English
Scale:       Up to ~1M chunks comfortably

### What Claude, ChatGPT, and production systems use

#### Embeddings
OpenAI text-embedding-3-large   →  3072 dimensions  →  much richer meaning
OpenAI text-embedding-3-small   →  1536 dimensions  →  good balance
Google text-embedding-004       →  768 dimensions
Cohere embed-v3                 →  1024 dimensions

More dimensions = the model captures more nuanced aspects of meaning.
Your 384-dim model might confuse "bank" (river) with "bank" (finance).
A 3072-dim model handles this much better.

The fundamental concept is identical. Just bigger numbers, more nuance.

#### Vector databases
You used:    pgvector (PostgreSQL extension)
Production:  Pinecone, Weaviate, Qdrant, Milvus, Chroma

pgvector is excellent for:
- Teams already using PostgreSQL
- Up to ~5 million vectors
- Wanting SQL + vectors in one database
- Cost-conscious setups

Pinecone/Qdrant are used when:
- Billions of vectors (entire internet scale)
- Need managed infrastructure
- Sub-10ms query latency at massive scale
- Multi-region replication

Anthropic likely uses custom internal vector infrastructure for Claude.
OpenAI uses their own embedding + retrieval systems.

The core algorithm (cosine similarity search) is the same everywhere.

#### Chunking strategies
You used:       RecursiveCharacterTextSplitter (character-based)
Production:     Semantic chunking — splits at meaning boundaries not char count
Token-based chunking — splits by tokens not characters
Hierarchical chunking — keeps parent/child relationships
Document-structure-aware — respects headings, tables, code blocks

Character-based chunking (what you built) is simple and works well.
The fancier approaches exist because:
- A table should not be split mid-row
- A code block should stay intact
- A heading and its paragraph should often be one chunk

#### Retrieval approaches
You built:      Pure vector search (semantic similarity only)
Production:     Hybrid search = vector search + BM25 keyword search
Combined with a Reranker model for final ordering

Pure vector search sometimes misses exact keyword matches.
"What is the error code 404?" — the word "404" has no semantic meaning.
Keyword search finds "404" exactly. Hybrid search combines both.

This is Week 3 of your curriculum.

---

## Part 4 — Other Approaches You Could Have Taken

### Different embedding models

#### Option A — OpenAI embeddings (best quality, costs money)

```python
from openai import OpenAI
client = OpenAI()

def embed_texts(texts):
    response = client.embeddings.create(
        model="text-embedding-3-small",  # 1536-dim
        input=texts
    )
    return [item.embedding for item in response.data]
```

Pro: Better quality, especially for complex technical text
Con: $0.02 per million tokens, requires API key, data leaves your server

#### Option B — Google embeddings

```python
import google.generativeai as genai

def embed_texts(texts):
    result = genai.embed_content(
        model="models/text-embedding-004",
        content=texts,
    )
    return result['embedding']
```

#### Option C — Ollama (local, larger models, GPU recommended)

```python
import ollama

def embed_texts(texts):
    return [
        ollama.embeddings(model='nomic-embed-text', prompt=t)['embedding']
        for t in texts
    ]
```

Run completely locally with better quality than all-MiniLM-L6-v2.
Requires more RAM (4-8GB) and is slower on CPU.

### Different chunking strategies

#### Option A — Token-based chunking (more accurate for LLM context limits)

```python
import tiktoken
from langchain_text_splitters import TokenTextSplitter

# Split by tokens not characters
# LLM context windows are measured in tokens not characters
# 512 chars ≠ 512 tokens (tokens are roughly 4 chars each)
splitter = TokenTextSplitter(
    chunk_size=256,      # 256 tokens ≈ ~1024 characters
    chunk_overlap=32,
    encoding_name="cl100k_base",  # same tokenizer as GPT-4
)
```

Why this matters: if your LLM has a 4096 token context window and you
pass 5 chunks of 512 characters each — you might be fine or you might
overflow depending on how tokenization works. Token-based chunking
gives you precise control.

#### Option B — Semantic chunking (splits at meaning boundaries)

```python
from langchain_experimental.text_splitter import SemanticChunker
from langchain_openai import OpenAIEmbeddings

splitter = SemanticChunker(
    OpenAIEmbeddings(),
    breakpoint_threshold_type="percentile"
)
```

Instead of splitting every 512 chars, this embeds every sentence,
finds where the meaning "jumps" between sentences, and splits there.
Result: each chunk is truly about one topic.
More expensive (requires embedding every sentence upfront) but
produces much higher quality chunks.

#### Option C — Document structure aware (best for PDFs and docs)

```python
from langchain.document_loaders import PyPDFLoader
from langchain_text_splitters import MarkdownHeaderTextSplitter

# Split by markdown headers — keeps sections together
headers_to_split_on = [
    ("#", "Header 1"),
    ("##", "Header 2"),
    ("###", "Header 3"),
]
splitter = MarkdownHeaderTextSplitter(headers_to_split_on)
```

### Different vector stores

#### Option A — Chroma (simplest, great for prototyping)

```python
import chromadb

client = chromadb.Client()
collection = client.create_collection("documents")
collection.add(embeddings=embeddings, documents=texts, ids=ids)
results = collection.query(query_embeddings=[question_embedding], n_results=5)
```

No PostgreSQL needed. Runs in memory or on disk. Zero setup.
Not suitable for production at scale but perfect for learning.

#### Option B — Pinecone (fully managed, production scale)

```python
import pinecone

index = pinecone.Index("documents")
index.upsert(vectors=[(id, embedding, metadata)])
results = index.query(vector=question_embedding, top_k=5)
```

No infrastructure to manage. Scales to billions of vectors.
Costs money but saves engineering time.

#### Option C — FAISS (Meta's library, fastest on CPU/GPU)

```python
import faiss
import numpy as np

index = faiss.IndexFlatIP(384)  # inner product = cosine similarity
index.add(np.array(embeddings))
distances, indices = index.search(np.array([question_embedding]), k=5)
```

Fastest pure vector search library. Used internally at Meta.
No persistence built-in — you manage saving/loading yourself.

---

## Part 5 — How Claude and ChatGPT Actually Work

They do NOT just have one giant vector database. The reality is layered:

### Layer 1 — Training (what the model "knows")

The LLM itself was trained on trillions of tokens of text. This gives it
general knowledge baked into its weights. This is not RAG — this is
the model's "long term memory" from training.

### Layer 2 — Context window (what the model can "see" right now)

Claude has a 200K token context window. ChatGPT-4 has 128K.
This is the "working memory" — everything in the current conversation
plus any retrieved documents.

### Layer 3 — Retrieval (RAG — exactly what you built)

For specific private data, recent information, or long documents —
the system retrieves relevant chunks and puts them in the context window.

Your project implements this layer.

### Layer 4 — Tools and function calling

Claude and ChatGPT can call external APIs, run code, search the web.
This is beyond RAG — the model decides when to call a tool and what
to do with the result.

### The full production pipeline at scale looks like
User question
│
▼
Query rewriting (LLM rewrites question for better retrieval)
│
▼
Hybrid search (vector + keyword)
│
▼
Reranker model (reorders results by relevance)
│
▼
Context compression (LLM compresses chunks to fit context window)
│
▼
LLM generates answer with citations
│
▼
RAGAS evaluation (faithfulness, relevancy, recall scored automatically)

You are building this entire pipeline over 18 weeks.
This week you completed the first two boxes: document ingestion and
vector storage. Each week adds one more box.

---

## Part 6 — Key Numbers to Remember
all-MiniLM-L6-v2 dimensions:    384
OpenAI ada-002 dimensions:      1536
OpenAI text-3-large dimensions: 3072
Your chunk size:                512 characters ≈ 128 tokens
Your chunk overlap:             64 characters ≈ 16 tokens
IVFFlat lists=100:              good for up to 100,000 chunks
IVFFlat lists=1000:             good for up to 1,000,000 chunks
Cosine similarity range:        -1.0 to 1.0
Good retrieval threshold:       > 0.7 cosine similarity

---

## Part 7 — What to Explore Further

If you want to go deeper on any of these topics:

**Embeddings**
- Read: "Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks" (the paper behind all-MiniLM)
- Try: Compare embeddings of similar vs different sentences using cosine similarity in the Django shell

**Chunking**
- Experiment: Change chunk_size to 256 and 1024. Re-upload the same document. See how chunk quality changes.
- Try: Token-based chunking with tiktoken

**pgvector**
- Read: pgvector GitHub README — covers HNSW index (faster than IVFFlat for most cases)
- Try: HNSW index instead of IVFFlat (Week 3 upgrade)

**RAG quality**
- Read: "RAGAS: Automated Evaluation of Retrieval Augmented Generation" paper
- This is the evaluation framework you will implement in Week 6

---

## Summary — What Week 1 Actually Means

You did not just "set up a Django project". You built:

1. A document ingestion system that scales to thousands of documents
2. An async processing pipeline that handles chunking without blocking the API
3. A vector storage system using the same core technology as production AI systems
4. The foundation that every week of this curriculum builds on top of

The concepts — embeddings, vector similarity, chunking strategy, approximate
nearest neighbor search — these are the same concepts used inside every
major AI company building RAG systems today.

Your implementation uses simpler/cheaper tools (all-MiniLM vs OpenAI,
pgvector vs Pinecone) but the architecture is identical. Swapping the
embedding model or vector store is a configuration change, not a
redesign. That is good software architecture.
