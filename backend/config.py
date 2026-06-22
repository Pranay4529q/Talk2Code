import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

REPOSITORY_DIR = "repositories"
CHROMA_DB_DIR = "chroma_db"

EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"

GROQ_MODEL = "llama-3.1-8b-instant"