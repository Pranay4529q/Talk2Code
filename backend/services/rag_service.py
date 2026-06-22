from langchain_groq import ChatGroq

from config import (
    GROQ_API_KEY,
    GROQ_MODEL
)

from services.vector_store_service import (
    VectorStoreService
)


class RAGService:

    @staticmethod
    def ask_question(
        repo_id: str,
        question: str
    ):

        vector_store = (
            VectorStoreService.load_vector_store(
                repo_id
            )
        )

        docs = vector_store.similarity_search(
            question,
            k=5
        )

        context = "\n\n".join(
            [
                doc.page_content
                for doc in docs
            ]
        )

        prompt = f"""
You are an expert software engineer.

Answer ONLY using the provided repository context.

Repository Context:

{context}

Question:

{question}

If the answer is not present in the context,
say that the information could not be found.
"""

        llm = ChatGroq(
            model=GROQ_MODEL,
            temperature=0,
            api_key=GROQ_API_KEY
        )

        response = llm.invoke(prompt)

        return response.content