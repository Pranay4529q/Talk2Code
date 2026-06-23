import os
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter, Language
from utils.file_filters import should_ignore

class FileService:

    @staticmethod
    def get_splitter_for_file(file_path: str) -> RecursiveCharacterTextSplitter:
        """
        Dynamically returns a language-aware splitter based on file extension.
        """
        ext = os.path.splitext(file_path).lower()
        
        # Optimized sizing for code bases: prevents context truncation while keeping embedding dense
        chunk_size = 750
        chunk_overlap = 100

        lang_mapping = {
            ".py": Language.PYTHON,
            ".js": Language.JS,
            ".ts": Language.TS,
            ".tsx": Language.TS,
            ".jsx": Language.JS,
            ".java": Language.JAVA,
            ".cpp": Language.CPP,
            ".cc": Language.CPP,
            ".c": Language.C,
            ".go": Language.GO,
            ".rb": Language.RUBY,
            ".rs": Language.RUST,
            ".html": Language.HTML,
            ".md": Language.MARKDOWN,
        }

        if ext in lang_mapping:
            return RecursiveCharacterTextSplitter.from_language(
                language=lang_mapping[ext],
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap
            )
        
        # Safe fallback splitter for text/json/yaml configuration files
        return RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )

    @staticmethod
    def load_documents(repo_path):
        documents = []

        for root, dirs, files in os.walk(repo_path):
            dirs[:] = [
                d for d in dirs
                if d not in {".git", "node_modules", "venv", "__pycache__"}
            ]

            for file in files:
                file_path = os.path.join(root, file)

                if should_ignore(file_path):
                    continue

                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()

                    if not content.strip():
                        continue

                    rel_path = os.path.relpath(file_path, repo_path)
                    splitter = FileService.get_splitter_for_file(file_path)
                    raw_chunks = splitter.split_text(content)

                    for chunk in raw_chunks:
                        if len(chunk.strip()) > 30:
                            # Context Injection: Explicitly forces filenames into the BM25 text corpus
                            enriched_content = f"--- File Context ---\nFile Path: {rel_path}\n-------------------\n\n{chunk}"

                            documents.append(
                                Document(
                                    page_content=enriched_content,
                                    metadata={"source": rel_path}
                                )
                            )

                except Exception:
                    continue

        return documents
