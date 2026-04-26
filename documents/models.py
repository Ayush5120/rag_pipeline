from django.db import models
from pgvector.django import VectorField
# Create your models here.

class Document(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('done', 'Done'),
        ('failed', 'Failed'),
    ]

    title = models.CharField(max_length=255)
    file = models.FileField(upload_to='documents/')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
    
class DocumentChunk(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='chunks')
    # CASCADE: delete a Document → automatically delete all its chunks.
    # related_name='chunks' lets you do doc.chunks.all() instead of
    # DocumentChunk.objects.filter(document=doc). Much cleaner.

    chunk_index = models.IntegerField()
     # 768 for HuggingFace all-MiniLM-L6-v2; use 1536 for OpenAI text-embedding-ada-002
    content = models.TextField()
    embedding = VectorField(dimensions=384)
    # THE CORE RAG FIELD. A 768-dimensional float veccdtor.
    # 768 matches HuggingFace all-MiniLM-L6-v2.
    # Change to 1536 if you switch to OpenAI text-embedding-3-small.
    # They MUST match — you can't compare a 768-dim to a 1536-dim vector.
    # When a user asks a question, their question is also embedded to
    # 768 dims, then we find the chunks whose embedding is closest.
    # That's the entire retrieval mechanism.

    metadata = models.JSONField(default=list)
    # Flexible field for chunk-level info: page number, section title,
    # source URL etc. Useful for citations
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['chunk_index']
        indexes = [
            models.Index(fields=['document', 'chunk_index']),
            # Index for fast "give me all chunks of document X in order".
            # Without this, that query scans the full table.
        ]
    
    def __str__(self):
        return f"{self.document.title} — chunk {self.chunk_index}"


class QueryLog(models.Model):
    query = models.TextField()
    # The user's question.

    answer = models.TextField(blank=True)
    # The LLM's response.

    retrieved_chunk_ids = models.JSONField(default=list)
    # Which chunks were used to generate this answer.
    # Needed for RAGAS context recall evaluation in Week 6.

    latency_ms = models.IntegerField(default=0)
    # How long the full pipeline took in milliseconds.
    # Useful for identifying slow queries.

    ragas_score = models.FloatField(null=True, blank=True)
    # RAGAS evaluation score populated in Week 6.
    # null=True because it's computed after the fact, not at query time.

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.query[:80]