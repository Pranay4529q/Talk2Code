from langchain_chroma import Chroma
from langchain.retrievers import BM25Retriever
from config import CHROMA_DB_DIR
from services.embedding_service import EmbeddingService

class VectorStoreService:

    # Global multi-tenant runtime storage map for fast cache hit tracking
    bm25_store = {}

    @staticmethod
    def create_vector_store(repo_id, documents):
        embeddings = EmbeddingService.get_embeddings()

        # Instantiate persistent Chroma Vector Database
        vector_store = Chroma.from_documents(
            documents=documents,
            embedding=embeddings,
            persist_directory=f"{CHROMA_DB_DIR}/{repo_id}"
        )

        # Instantiate BM25 Retriever and optimize top-K visibility parameters
        bm25 = BM25Retriever.from_documents(documents)
        bm25.k = 6

        # Bind to memory matrix
        VectorStoreService.bm25_store[repo_id] = bm25

        return vector_store

    @staticmethod
    def load_vector_store(repo_id):
        embeddings = EmbeddingService.get_embeddings()

        vector_store = Chroma(
            persist_directory=f"{CHROMA_DB_DIR}/{repo_id}",
            embedding_function=embeddings
        )

        # Lazy reconstruction safeguard: if the server restarts, rehydrate BM25 index elements gracefully
        bm25 = VectorStoreService.bm25_store.get(repo_id)
        if not bm25:
            # Fallback extraction directly from the underlying vector db chunks
            try:
                all_chunks = vector_store.get()
                documents = []
                from langchain_core.documents import Document
                for idx in range(len(all_chunks['documents'])):
                    documents.append(
                        Document(
                            page_content=all_chunks['documents'][idx],
                            metadata=all_chunks['metadatas'][idx] if all_chunks['metadatas'] else {}
                        )
                    )
                if documents:
                    bm25 = BM25Retriever.from_documents(documents)
                    bm25.k = 6
                    VectorStoreService.bm25_store[repo_id] = bm25
            except Exception:
                bm25 = None

        return vector_store, bm25
