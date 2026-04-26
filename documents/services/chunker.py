# Place at: docqa/documents/services/chunker.py

from langchain_text_splitters import RecursiveCharacterTextSplitter


def chunk_document(text: str) -> list[dict]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=512,
        # 512 characters per chunk. Sweet spot — small enough to be
        # precise when retrieved, large enough to contain a full thought.
        # Too small: chunk lacks context to answer a question.
        # Too large: retrieval noise increases (irrelevant sentences included).

        chunk_overlap=64,
        # Consecutive chunks share 64 characters at their boundary.
        # This prevents a key sentence being split across two chunks
        # where neither chunk has enough context to answer about it.

        separators=["\n\n", "\n", ". ", " ", ""],
        # Priority order for WHERE to split.
        # Tries paragraph breaks first (most natural split point).
        # Falls back to line break → sentence end → word → character.
        # This is 'Recursive' because it tries each separator in order.
        # Result: chunks respect paragraph/sentence structure, not just
        # arbitrary character counts.

        length_function=len,
        # Use Python's len() to measure chunk size in characters.
        # Alternative: count tokens instead of characters (Week 3 upgrade).
    )

    chunks = splitter.create_documents([text])

    return [
        {
            "content": chunk.page_content,
            "metadata": chunk.metadata,
            "chunk_index": i,
        }
        for i, chunk in enumerate(chunks)
    ]