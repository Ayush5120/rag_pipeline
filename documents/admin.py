from django.contrib import admin

# Register your models here.
# Place at: docqa/documents/admin.py

from django.contrib import admin
from .models import Document, DocumentChunk, QueryLog


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['title', 'status', 'created_at']
    list_filter = ['status']
    # Sidebar filter: click 'done' to see only processed documents.
    search_fields = ['title']


@admin.register(DocumentChunk)
class DocumentChunkAdmin(admin.ModelAdmin):
    list_display = ['document', 'chunk_index', 'created_at']


@admin.register(QueryLog)
class QueryLogAdmin(admin.ModelAdmin):
    list_display = ['query', 'latency_ms', 'ragas_score', 'created_at']