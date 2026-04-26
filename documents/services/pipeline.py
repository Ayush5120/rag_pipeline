# Place at: docqa/documents/services/pipeline.py

from documents.models import Document, DocumentChunk
from .chunker import chunk_document
from .embedder import embed_texts


def process_document(document_id: int) -> None:
    doc = Document.objects.get(id=document_id)
    doc.status = 'processing'
    doc.save(update_fields=['status'])
    # update_fields=['status'] sends UPDATE documents SET status=...
    # instead of updating ALL fields. Safer and faster.

    try:
        # Step 1: read raw text
        text = doc.file.read().decode('utf-8')
        # Works for plain .txt files.
        # Week 3 adds PDF/DOCX parsing here — only this line changes.

        # Step 2: split into chunks
        chunks = chunk_document(text)

        # Step 3: embed all chunks in one batch
        texts = [c['content'] for c in chunks]
        embeddings = embed_texts(texts)
        # One batch call to the model — much faster than embedding
        # one chunk at a time in a loop.

        # Step 4: wipe old chunks (idempotency)
        DocumentChunk.objects.filter(document=doc).delete()
        # If this task is retried after a crash, we don't want
        # duplicate chunks. Delete first → re-insert is always safe.
        # This pattern is called idempotency — safe to run N times.

        # Step 5: bulk insert to PostgreSQL
        DocumentChunk.objects.bulk_create([
            DocumentChunk(
                document=doc,
                chunk_index=c['chunk_index'],
                content=c['content'],
                embedding=emb,
                metadata=c['metadata'],
            )
            for c, emb in zip(chunks, embeddings)
        ])
        # bulk_create = ONE INSERT statement with all rows.
        # Without it: 50 chunks = 50 round-trips to Postgres.
        # With it: 50 chunks = 1 round-trip. Always use for batch inserts.

        doc.status = 'done'

    except Exception as e:
        doc.status = 'failed'
        raise e
        # Re-raise so Celery knows the task failed and can retry.

    finally:
        doc.save(update_fields=['status'])
        # finally = runs whether try succeeded or except was hit.
        # Guarantees status is always saved to DB.