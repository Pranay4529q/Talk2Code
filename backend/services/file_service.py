import os
from langchain_core.documents import Document

from utils.file_filters import should_ignore


class FileService:

    @staticmethod
    def load_documents(repo_path):

        documents = []

        for root, dirs, files in os.walk(repo_path):

            dirs[:] = [
                d for d in dirs
                if d not in {
                    ".git",
                    "node_modules",
                    "venv"
                }
            ]

            for file in files:

                file_path = os.path.join(root, file)

                if should_ignore(file_path):
                    continue

                try:

                    with open(
                        file_path,
                        "r",
                        encoding="utf-8"
                    ) as f:

                        content = f.read()

                    documents.append(
                        Document(
                            page_content=content,
                            metadata={
                                "source": file_path
                            }
                        )
                    )

                except Exception:
                    continue

        return documents