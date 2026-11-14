import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

from fastapi.testclient import TestClient

from app import app
from services.file_service import chunk_python
from services.github_service import GithubService

URL = "https://github.com/example/example"
COMMIT = "a" * 40


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_allowlisted_repo_url(self):
        self.assertEqual(GithubService.normalize_url(URL.upper() + ".git/"), URL)
        for url in ("file:///tmp/example", URL + "/tree/main", URL + "?a=1"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                GithubService.normalize_url(url)

    def test_decorators_and_syntax_fallback_preserve_lines(self):
        chunks = list(chunk_python("import x\n@x.decorator\ndef f():\n    pass\n", "a.py"))
        self.assertEqual((chunks[-1]["symbol"], chunks[-1]["start_line"], chunks[-1]["end_line"]), ("f", 2, 4))
        self.assertEqual(list(chunk_python("def invalid(", "a.py"))[0]["start_line"], 1)

    def test_ui_and_input_validation(self):
        self.assertIn("Index repository", self.client.get("/").text)
        self.assertEqual(self.client.get("/assets/chat.js").status_code, 200)
        self.assertEqual(self.client.post("/ingest", json={"github_url": "https://example.com/a/b"}).status_code, 422)
        self.assertEqual(self.client.post("/chat", json={"repo_id": "../x", "question": "hello"}).status_code, 422)

    @staticmethod
    def fixture_clone(url, destination):
        destination.mkdir()
        (destination / "main.py").write_text("def greet():\n    return 'hello'\n")
        (destination / "skip.js").write_text("secret")
        return COMMIT

    def test_ingest_then_chat_with_verified_citation(self):
        with (
            tempfile.TemporaryDirectory() as directory,
            patch("app.GithubService.clone_repo", side_effect=self.fixture_clone),
            patch("services.vector_store_service.INDEX_DIR", Path(directory)),
            patch("services.vector_store_service.embed_texts", side_effect=lambda texts: [[1.0] for _ in texts]),
            patch("services.rag_service.GROQ_API_KEY", "test"),
            patch("services.rag_service.httpx.post") as completion,
        ):
            indexed = self.client.post("/ingest", json={"github_url": URL})
            self.assertEqual(indexed.status_code, 200)
            self.assertEqual(indexed.json()["documents_indexed"], 1)
            payload = {"repo_id": indexed.json()["repo_id"], "question": "What does greet do?"}

            def reply(citations):
                completion.return_value.json.return_value = {
                    "choices": [{"message": {"content": json.dumps({
                        "answer": "It returns hello [1].", "citations": citations,
                    })}}]
                }
                return self.client.post("/chat", json=payload)

            answer = reply([1])
            self.assertEqual(answer.status_code, 200)
            self.assertEqual(answer.json()["sources"][0]["url"], f"{URL}/blob/{COMMIT}/main.py#L1-L2")
            self.assertEqual(reply([99]).json()["sources"], [])
            self.assertEqual(self.client.post("/chat", json={**payload, "repo_id": str(uuid4())}).status_code, 404)
