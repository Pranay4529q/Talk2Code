IGNORE_DIRS = {
    ".git",
    "node_modules",
    "venv",
    "__pycache__",
    "dist",
    "build",
    ".next",
    ".idea",
    ".vscode"
}

IGNORE_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".svg",
    ".ico",
    ".pdf",
    ".zip",
    ".tar",
    ".gz",
    ".mp4",
    ".mp3",
    ".env"
}


def should_ignore(path: str):
    path = path.lower()

    for directory in IGNORE_DIRS:
        if directory.lower() in path:
            return True

    for extension in IGNORE_EXTENSIONS:
        if path.endswith(extension):
            return True

    return False