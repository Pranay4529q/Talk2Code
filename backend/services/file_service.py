import ast
import os
import tokenize
from pathlib import Path

from utils.file_filters import IGNORE_DIRS

MAX_FILES = 200
MAX_FILE_BYTES = 128 * 1024
MAX_SOURCE_BYTES = 2 * 1024 * 1024
MAX_CHUNK_LINES = 45


def chunk_python(text: str, source: str):
    lines = text.splitlines()
    try:
        tree = ast.parse(text)
    except (SyntaxError, RecursionError, ValueError):
        tree = None

    starts = {0: "<module>"}
    for node in tree.body if tree else ():
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            first = min([node.lineno, *(item.lineno for item in node.decorator_list)])
            starts[first - 1] = node.name

    boundaries = sorted(set(starts) | {len(lines)})
    for start, end in zip(boundaries, boundaries[1:]):
        offset = start
        while offset < end:
            stop = min(offset + MAX_CHUNK_LINES, end)
            content = "\n".join(lines[offset:stop])
            if content.strip():
                yield {
                    "text": content,
                    "source": source,
                    "symbol": starts[start],
                    "start_line": offset + 1,
                    "end_line": stop,
                }
            offset = stop - 5 if stop < end else end


class FileService:
    @staticmethod
    def load_documents(repo_path: Path):
        chunks = []
        files_indexed = 0
        total_bytes = 0
        limited = False
        for root, dirs, files in os.walk(repo_path):
            dirs[:] = sorted(
                name for name in dirs
                if name.lower() not in IGNORE_DIRS
                and not name.startswith(".")
            )
            for name in sorted(files):
                path = Path(root) / name
                if path.suffix != ".py" or name.startswith(".") or path.is_symlink() or not path.is_file():
                    continue
                size = path.stat().st_size
                if size > MAX_FILE_BYTES:
                    limited = True
                    continue
                if files_indexed >= MAX_FILES or total_bytes + size > MAX_SOURCE_BYTES:
                    return chunks, files_indexed, True
                total_bytes += size
                try:
                    with tokenize.open(path) as file:
                        text = file.read()
                except (SyntaxError, UnicodeError, LookupError, OSError):
                    continue
                file_chunks = list(chunk_python(text, path.relative_to(repo_path).as_posix()))
                if file_chunks:
                    chunks.extend(file_chunks)
                    files_indexed += 1
        return chunks, files_indexed, limited
