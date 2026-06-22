from langchain_community.embeddings import HuggingFaceEmbeddings

from config import EMBEDDING_MODEL


class EmbeddingService:

    @staticmethod
    def get_embeddings():

        return HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL
        )