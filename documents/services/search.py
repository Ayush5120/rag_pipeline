from pgvector.django import CosineDistance
from documents.models import DocumentChunk
from .embedder import embed_texts


def search_chunks(query: str, doc_id: int=None, top_k: int=5) -> list:
    """
    Find the most semantically relevant chunks for a query.
    
    HOW IT WORKS:
    1. Embed the query using the SAME model used at ingestion time
       (CRITICAL — mismatched models = garbage results)
    2. Use pgvector's CosineDistance to rank all chunks by similarity
    3. Return top_k closest chunks
    
    WHY CosineDistance not L2 (Euclidean)?
    L2 distance cares about vector magnitude (length).
    Cosine distance only cares about direction (angle between vectors).
    For text similarity, direction is what matters.
    "cat" and "cats" should be similar regardless of how long
    their vectors are.
    
    All-MiniLM-L6-v2 outputs normalized vectors (magnitude=1)
    so L2 and cosine give the same ranking. We use cosine explicitly
    for clarity and correctness when switching models.
    """
    # Embed query — returns list of one embedding

    query_embedding = embed_texts([query])[0]

    # Build queryset with cosine distance annotation

    queryset = (
        DocumentChunk.objects
        .annotate(distance= CosineDistance('embedding', query_embedding))
        .order_by('distance')
        # Lower distance = more similar
        # Distance 0.0 = identical, 1.0 = completely different
    )

    # Optional: filter to one document
    if doc_id:
        queryset = queryset.filter(document_id=doc_id)
    
    # Optional: only return high-quality matches
    # WHY 0.7 threshold? Empirically tuned — distances > 0.7
    # are usually irrelevant. Remove this for broader recall.
    queryset = queryset.filter(distance__lt=0.7)

    return list(queryset.select_related('document')[:top_k])


