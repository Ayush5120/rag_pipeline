from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Document
from .serializers import DocumentSerializer, DocumentChunkSerializer
from .tasks import process_document_task


class DocumentViewSet(viewsets.ModelViewSet):
    queryset = Document.objects.all().order_by('-created_at')
    serializer_class = DocumentSerializer
    # ModelViewSet auto-generates these endpoints:
    # GET  /api/documents/        → list all documents
    # POST /api/documents/        → upload a new document
    # GET  /api/documents/{id}/   → get one document
    # PUT  /api/documents/{id}/   → update a document
    # DELETE /api/documents/{id}/ → delete a document

    def perform_create(self, serializer):
        doc = serializer.save()
        process_document_task.delay(doc.id)
        # perform_create is the hook: "after saving, do something extra."
        # .delay() pushes the task to Redis and returns immediately.
        # The user gets a 201 response right away.
        # Celery picks up the job and processes it in the background.
        # Without .delay() the POST would hang for 30 seconds.

    @action(detail=True, methods=['get'])
    def chunks(self, request, pk=None):
        # Creates: GET /api/documents/{id}/chunks/
        # Returns all chunks for a document. Useful for debugging —
        # "did my document get chunked correctly?"
        doc = self.get_object()
        serializer = DocumentChunkSerializer(doc.chunks.all(), many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def reprocess(self, request, pk=None):
        # Creates: POST /api/documents/{id}/reprocess/
        # Re-runs the ingestion pipeline. Useful when a document
        # failed and you want to retry without re-uploading the file.
        doc = self.get_object()
        doc.status = 'pending'
        doc.save(update_fields=['status'])
        process_document_task.delay(doc.id)
        return Response({'status': 'reprocessing started'})