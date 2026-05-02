import os
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage


def generate_answer(question: str, chunks: list) -> dict:
    if not chunks:
        return {'answer': "I could not find relevant information.", 'sources': []}

    context_parts = []
    for i, chunk in enumerate(chunks, 1):
        context_parts.append(
            f"[Source {i}] (Document: {chunk.document.title})\n{chunk.content}"
        )
    context = "\n\n---\n\n".join(context_parts)

    llm = ChatGroq(
        model='llama-3.1-8b-instant',
        temperature=0,
        api_key=os.getenv('GROQ_API_KEY'),
    )

    messages = [
        SystemMessage(content=(
            "You are a precise Q&A assistant. "
            "Answer using ONLY the provided sources. "
            "If the answer is not in the sources, say 'I don't have enough information.' "
            "Cite sources like: According to [Source 1]..."
        )),
        HumanMessage(content=f"Sources:\n\n{context}\n\nQuestion: {question}\n\nAnswer:"),
    ]

    response = llm.invoke(messages)

    return {
        'answer': response.content,
        'sources': [
            {
                'id': c.id,
                'content': c.content,
                'document_title': c.document.title,
                'chunk_index': c.chunk_index,
                'similarity_score': round(1 - c.distance, 4),
            }
            for c in chunks
        ]
    }