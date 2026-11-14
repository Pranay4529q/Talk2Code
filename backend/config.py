import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
INDEX_DIR = Path(os.getenv("TALK2CODE_INDEX_DIR", "chroma_db/talk2code-v1"))
EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"
