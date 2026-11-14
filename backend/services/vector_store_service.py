import json
import tempfile
from pathlib import Path

from config import INDEX_DIR
from services.embedding_service import embed_texts
from services.retrieval import fuse_rankings, lexical_rank


class VectorStoreService:
    @staticmethod
    def save(repo_id, index):
        chunks = index["chunks"]
        index["vectors"] = embed_texts([
            f"{chunk['source']} {chunk['symbol']}\n{chunk['text']}" for chunk in chunks
        ])
        INDEX_DIR.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=INDEX_DIR, delete=False) as file:
            temporary = Path(file.name)
            try:
                with file:
                    json.dump(index, file)
                temporary.replace(INDEX_DIR / f"{repo_id}.json")
            finally:
                temporary.unlink(missing_ok=True)

    @staticmethod
    def load(repo_id):
        with (INDEX_DIR / f"{repo_id}.json").open(encoding="utf-8") as file:
            return json.load(file)

    @staticmethod
    def rank(index, question, mode="hybrid"):
        chunks = index["chunks"]
        lexical = lexical_rank(chunks, question) if mode != "dense" else []
        if mode == "lexical":
            return lexical
        query = embed_texts([f"Represent this sentence for searching relevant passages: {question}"])[0]
        scores = [sum(a * b for a, b in zip(query, vector)) for vector in index["vectors"]]
        dense = sorted(range(len(chunks)), key=lambda i: (-scores[i], i))
        return dense if mode == "dense" else fuse_rankings(lexical[:20], dense[:20])
