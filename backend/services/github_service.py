import os
import re
import subprocess
from pathlib import Path

REPO_URL = re.compile(
    r"https://github\.com/([A-Za-z0-9][A-Za-z0-9-]{0,38})/"
    r"([A-Za-z0-9_.-]{1,100})/?", re.IGNORECASE | re.ASCII
)


class GithubService:
    @staticmethod
    def normalize_url(url: str) -> str:
        match = REPO_URL.fullmatch(url.strip())
        if not match:
            raise ValueError("Enter an HTTPS GitHub repository URL, such as https://github.com/owner/repo.")
        owner, repo = match.groups()
        repo = re.sub(r"\.git$", "", repo, flags=re.IGNORECASE)
        if repo in {"", ".", ".."}:
            raise ValueError("Enter a GitHub repository name.")
        return f"https://github.com/{owner.lower()}/{repo.lower()}"

    @staticmethod
    def clone_repo(url: str, destination: Path) -> str:
        env = {
            **os.environ,
            "GIT_TERMINAL_PROMPT": "0",
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_ALLOW_PROTOCOL": "https",
            "GIT_LFS_SKIP_SMUDGE": "1",
        }
        subprocess.run(
            ["git", "-c", "http.followRedirects=false", "clone", "--depth", "1",
             "--no-tags", "--", url, str(destination)],
            check=True, capture_output=True, timeout=60, env=env,
        )
        return subprocess.check_output(
            ["git", "-C", str(destination), "rev-parse", "HEAD"],
            text=True, timeout=10, env=env,
        ).strip()
