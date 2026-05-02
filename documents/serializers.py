# Place at: docqa/documents/serializers.py

from rest_framework import serializers
from .models import Document, DocumentChunk, QueryLog


ALLOWED_CONTENT_TYPES = ['application/pdf', 'text/plain']
MAX_FILE_SIZE_MB = 10

class DocumentSerializer(serializers.ModelSerializer):
    chunk_count = serializers.SerializerMethodField()
    # SerializerMethodField = a computed field not on the model.
    # Calls get_chunk_count() below. The API response includes
    # "chunk_count": 42 without adding a column to the DB.

    class Meta:
        model = Document
        fields = ['id', 'title', 'file', 'status', 'chunk_count', 'created_at']
        read_only_fields = ['status', 'created_at']
        # status is set by the pipeline, not by the user.
        # read_only_fields means DRF ignores these in POST/PUT requests.

    def get_chunk_count(self, obj):
        return obj.chunks.count()
        # obj.chunks is the related_name we set on DocumentChunk.
        # .count() = one SELECT COUNT query, not fetching all chunks.


class DocumentChunkSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentChunk
        fields = ['id', 'chunk_index', 'content', 'metadata']
        # Intentionally exclude 'embedding' — it's a 768-float array.
        # Returning it in the API would bloat every response by ~3KB.


class QueryLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = QueryLog
        fields = ['id', 'query', 'answer', 'latency_ms', 'ragas_score', 'created_at']

class DocumentUploadSerializer(serializers.Serializer):
    file = serializers.FileField(required=False)
    text = serializers.CharField(required=False, allow_blank=False, max_length=500_000)
    title = serializers.CharField(max_length=255)

    def validate(self, data):
        if not data.get('file') and not data.get('text'):
            raise serializers.ValidationError(
                "Provide either a 'file' or 'text' field."
            )
        return data

    def validate_file(self, file):
        max_size = 10 * 1024 * 1024
        if file.size > max_size:
            raise serializers.ValidationError(
                f"File size {file.size / 1024 / 1024:.1f}MB exceeds 10MB limit."
            )
        allowed = ['application/pdf', 'text/plain']
        if file.content_type not in allowed:
            raise serializers.ValidationError(
                f"Only PDF or plain text allowed."
            )
        return file

