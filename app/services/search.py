import numpy as np
import ast


def cosine_similarity(vector1, vector2):
    vector1 = np.array(vector1)
    vector2 = np.array(vector2)

    dot_product = np.dot(vector1, vector2)

    norm_vector1 = np.linalg.norm(vector1)
    norm_vector2 = np.linalg.norm(vector2)

    if norm_vector1 == 0 or norm_vector2 == 0:
        return 0

    return dot_product / (norm_vector1 * norm_vector2)


def find_most_similar_chunks(
    question_embedding,
    document_chunks,
    top_k=3
):
    results = []

    for chunk in document_chunks:

        # Convert embedding string from database back to list
        chunk_embedding = ast.literal_eval(
            chunk.embedding
        )

        similarity = cosine_similarity(
            question_embedding,
            chunk_embedding
        )

        results.append({
            "id": chunk.id,
            "filename": chunk.filename,
            "text": chunk.chunk_text,
            "similarity": float(similarity)
        })

    # Sort by similarity score
    results.sort(
        key=lambda x: x["similarity"],
        reverse=True
    )

    return results[:top_k]