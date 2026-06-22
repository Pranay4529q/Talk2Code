from langchain_chroma import Chroma

from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import CHROMA_DB_DIR

from services.embedding_service import EmbeddingService


class VectorStoreService:

    @staticmethod
    def create_vector_store(repo_id, documents):

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )

        chunks = splitter.split_documents(
            documents
        )

        embeddings = (
            EmbeddingService.get_embeddings()
        )

        vector_store = Chroma.from_documents(
            documents=chunks,
            embedding=embeddings,
            persist_directory=f"{CHROMA_DB_DIR}/{repo_id}"
        )

        return vector_store

    @staticmethod
    def load_vector_store(repo_id):

        embeddings = (
            EmbeddingService.get_embeddings()
        )

        return Chroma(
            persist_directory=f"{CHROMA_DB_DIR}/{repo_id}",
            embedding_function=embeddings
        )