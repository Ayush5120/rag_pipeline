from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Document
from .serializers import DocumentSerializer, DocumentChunkSerializer, QueryLog, QueryLogSerializer
from .tasks import process_document_task
from .services.search import search_chunks
import time
from rest_framework.views import APIView
from rest_framework import status

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
    
class DocumentViewSet(viewsets.ModelViewSet):
    queryset = Document.objects.all().order_by('-created_at')
    serializer_class = DocumentSerializer

    def perform_create(self, serializer):
        doc = serializer.save()
        process_document_task.delay(doc.id)

    @action(detail=True, methods=['get'])
    def chunks(self, request, pk=None):
        doc = self.get_object()
        serializer = DocumentChunkSerializer(doc.chunks.all(), many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def reprocess(self, request, pk=None):
        doc = self.get_object()
        doc.status = 'pending'
        doc.save(update_fields=['status'])
        process_document_task.delay(doc.id)
        return Response({'status': 'reprocessing started'})
    
class QueryView(APIView):
    """
    POST /api/query/
    
    Accepts: { "question": "...", "doc_id": 1 (optional) }
    Returns: { "chunks": [...], "query_log_id": 1 }
    
    WHY return chunks WITHOUT LLM answer at this stage?
    Test retrieval quality first. If the wrong chunks come back,
    no LLM prompt will fix that. Fix retrieval, then add LLM.
    """

    # documents/views.py — update QueryView.post()

    def post(self, request):
        from .services.llm import generate_answer

        question = request.data.get('question', '').strip()
        doc_id = request.data.get('doc_id')

        if not question:
            return Response(
                {'error': 'question is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        start_time = time.time()

        # Step 1: retrieve relevant chunks
        chunks = search_chunks(question, doc_id=doc_id, top_k=5)

        # Step 2: generate answer from chunks
        result = generate_answer(question, chunks)

        latency_ms = int((time.time() - start_time) * 1000)

        # Step 3: log everything for evaluation
        QueryLog.objects.create(
            query=question,
            answer=result['answer'],
            retrieved_chunk_ids=[c.id for c in chunks],
            latency_ms=latency_ms,
        )

        return Response({
            'answer': result['answer'],
            'sources': result['sources'],
            'latency_ms': latency_ms,
        })
