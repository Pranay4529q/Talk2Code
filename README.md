# Talk2Code

Talk2Code is a developer onboarding assistant for public GitHub repositories. Paste a repository URL, ask about its Python code, and open the cited lines at the exact commit that was indexed.

## Run locally

Requires Git, Python 3.11 or 3.12, and a Groq API key. The first indexing run downloads the BGE embedding model from Hugging Face.

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

On Windows PowerShell, activate with `.\.venv\Scripts\Activate.ps1`. Create `backend/.env`:

```dotenv
GROQ_API_KEY=your_key_here
# Optional
GROQ_MODEL=llama-3.1-8b-instant
```

From `backend`, run `python -m uvicorn app:app --reload` and open [the app](http://127.0.0.1:8000). API docs are at [/docs](http://127.0.0.1:8000/docs).

## Demo

1. Index `https://github.com/Pranay4529q/Talk2Code` after merging the onboarding changes.
2. Ask **How are the lexical and semantic rankings combined?** Open the linked lines and confirm the ranking formula.
3. Ask **Where is a repository index saved and how is the write made atomic?** Follow the citation to the index writer.
4. Ask **What production database credentials does this project use?** Check whether the assistant reports insufficient evidence.

## How it works

- A shallow clone captures a commit. The indexer reads only Python source and stores relative filenames, symbols, and line ranges. It uses the Python AST to find top-level class and function boundaries, with overlapping line windows for long sections and files that the local parser cannot parse.
- Keyword ranking matches identifiers and paths. BGE embeddings match paraphrased questions. Reciprocal rank fusion combines the two rankings and supplies up to five excerpts to Groq.
- The backend builds commit-pinned links from retrieved metadata and discards unknown citation IDs. If the model supplies no valid citation, the app returns an insufficient-evidence response. Citation ID checks do not measure whether every claim is supported.
- Local indexes use atomic JSON writes and a linear dense scan. Each ingestion gets a separate index. Earlier prototype indexes need to be rebuilt. The browser keeps a transcript for the current repository, and each question is answered independently.

The demo supports public GitHub repository URLs and indexes up to 200 readable Python files, 128 KiB per file, and 2 MiB of scanned Python source. Repository code is read without importing or running it. Retrieved excerpts are sent to Groq when answering. Run locally. A public deployment needs authentication or quotas, resource isolation for clones, and automatic index cleanup.

## Verify and evaluate

From `backend`:

```bash
python -m unittest discover -s tests -v
python evaluate.py --lexical-only
python evaluate.py
```

The workflow tests stub GitHub downloads, embeddings, and Groq. The eight-question benchmark labels relevant file and symbol pairs. It reports Hit@5, MRR@5 and median retrieval latency for keyword, dense, and hybrid retrieval. The full benchmark requires the BGE download and runs without a Groq key. It measures retrieval on this repository, with broader repository coverage and answer quality left for a separate evaluation.
