import os
import uuid
from git import Repo

from config import REPOSITORY_DIR


class GithubService:

    @staticmethod
    def clone_repo(github_url: str):

        repo_id = str(uuid.uuid4())

        repo_path = os.path.join(
            REPOSITORY_DIR,
            repo_id
        )

        Repo.clone_from(
            github_url,
            repo_path
        )

        return repo_id, repo_path