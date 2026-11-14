import argparse
import json
import time
from pathlib import Path
from statistics import median
from tempfile import TemporaryDirectory
from unittest.mock import patch

from services.file_service import FileService
from services.vector_store_service import VectorStoreService


def evaluate(cases, index, mode, k):
    ranks = []
    durations = []
    for case in cases:
        started = time.perf_counter()
        hits = VectorStoreService.rank(index, case["question"], mode)[:k]
        durations.append((time.perf_counter() - started) * 1000)
        relevant = [
            rank for rank, hit in enumerate(hits, start=1)
            if (index["chunks"][hit]["source"], index["chunks"][hit]["symbol"])
            == (case["path"], case["symbol"])
        ]
        ranks.append(relevant[0] if relevant else 0)
    return {
        f"hit@{k}": sum(rank > 0 for rank in ranks) / len(ranks),
        f"mrr@{k}": sum(1 / rank for rank in ranks if rank) / len(ranks),
        "median_retrieval_ms": round(median(durations), 2),
        "ranks": ranks,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--lexical-only", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    cases = json.loads((root / "evaluation" / "cases.json").read_text(encoding="utf-8"))
    chunks, _, _ = FileService.load_documents(root)
    index = {"chunks": [chunk for chunk in chunks if chunk["source"] == "app.py"
                        or chunk["source"].startswith("services/")]}
    if not args.lexical_only:
        with TemporaryDirectory() as directory:
            with patch("services.vector_store_service.INDEX_DIR", Path(directory)):
                VectorStoreService.save("evaluation", index)
                # Warm the query path before measuring retrieval latency.
                VectorStoreService.rank(index, cases[0]["question"], "dense")
    modes = ["lexical"] if args.lexical_only else ["lexical", "dense", "hybrid"]
    print(json.dumps({mode: evaluate(cases, index, mode, 5) for mode in modes}, indent=2))


if __name__ == "__main__":
    main()
