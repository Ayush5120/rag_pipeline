from sentence_transformers import SentenceTransformer

_model = None
# Module-level variable. This is the singleton pattern.

def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer('all-MiniLM-L6-v2')
        # Downloads ~90MB model on first call, loads into memory.
        # Takes 3-5 seconds. We NEVER want this inside embed_texts()
        # directly — it would reload on every function call.
        # With the singleton: loads ONCE when Celery worker starts.
        # Every subsequent call reuses the in-memory model instantly.
    return _model


def embed_texts(texts: list[str]) -> list[list[float]]:
    """
    Convert a list of text strings into 768-dimensional vectors.
    Called once per document with all chunks in a single batch.
    """
    model = get_model()
    embeddings = model.encode(
        texts,
        batch_size=32,
        # Don't set too high — memory issues on low-RAM machines.
        show_progress_bar=False,
        convert_to_numpy=True,
        # Returns numpy array. .tolist() below converts to plain
        # Python lists which pgvector's VectorField expects.
    )
    return embeddings.tolist()