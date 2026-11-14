from functools import lru_cache

from config import EMBEDDING_MODEL


@lru_cache(maxsize=1)
def get_embeddings():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(EMBEDDING_MODEL)


def embed_texts(texts):
    return get_embeddings().encode(
        texts, normalize_embeddings=True, show_progress_bar=False
    ).tolist()
