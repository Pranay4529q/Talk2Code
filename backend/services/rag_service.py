from langchain_groq import ChatGroq
from config import GROQ_API_KEY, GROQ_MODEL
from services.vector_store_service import VectorStoreService

class RAGService:

    @staticmethod
    def reciprocal_rank_fusion(vector_docs, bm25_docs, k_rrf=60):
        """
        Merges results from Vector Search and BM25 using Reciprocal Rank Fusion.
        Ensures a balanced ranking across keyword accuracy and semantic matching.
        """
        rrf_scores = {}
        doc_map = {}

        # Process Vector Store Ranks
        for rank, doc in enumerate(vector_docs):
            content = doc.page_content
            doc_map[content] = doc
            rrf_scores[content] = rrf_scores.get(content, 0.0) + (1.0 / (k_rrf + rank + 1))

        # Process BM25 Ranks
        for rank, doc in enumerate(bm25_docs):
            content = doc.page_content
            doc_map[content] = doc
            rrf_scores[content] = rrf_scores.get(content, 0.0) + (1.0 / (k_rrf + rank + 1))

        # Sort based on highest unified RRF value
        sorted_contents = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
        return [doc_map[content] for content, score in sorted_contents]

    @staticmethod
    def ask_question(repo_id: str, question: str):
        vector_store, bm25 = VectorStoreService.load_vector_store(repo_id)

        # Retrieve candidates from both indexing subsystems
        vector_docs = vector_store.similarity_search(question, k=6) if vector_store else []
        bm25_docs = bm25.invoke(question) if bm25 else []

        # Merge and intelligently re-rank using RRF
        unique_docs = RAGService.reciprocal_rank_fusion(vector_docs, bm25_docs)

        # Build highly structured system contexts
        context_blocks = []
        for doc in unique_docs[:7]:
            context_blocks.append(doc.page_content)
        
        context = "\n\n".join(context_blocks)

        # Structured XML Prompt layout optimized for Llama 3.1 instruction handling
        prompt = f"""You are an expert, analytical software engineering AI assistant.
Your task is to answer the user's question accurately using ONLY the provided repository codebase context.

Guidelines:
1. Ground your answer completely inside the given repository context.
2. If the context does not contain the answer, reply exactly: "Not found in repository." Do not guess or hallucinate.
3. Explicitly reference file paths and structural code components (like class names or function hooks) relevant to your answer.

<repository_context>
{context}
</repository_context>

User Question: {question}

Answer:"""

        llm = ChatGroq(
            model=GROQ_MODEL,
            temperature=0.0,  # Strict, low-variance deterministic reasoning
            api_key=GROQ_API_KEY
        )

        response = llm.invoke(prompt)
        return response.content
