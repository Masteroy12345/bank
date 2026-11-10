"""Offline tests for the server-side Appwrite adapter."""
from __future__ import annotations

import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse
from unittest.mock import patch

from backend import appwrite_store


class FakeAppwriteHandler(BaseHTTPRequestHandler):
    requests_seen = []

    def log_message(self, *_args):
        return

    def _send(self, status, payload=None):
        body = b"" if payload is None else json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if body:
            self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        FakeAppwriteHandler.requests_seen.append(("GET", parsed.path, self.headers, parsed.query, b""))
        if parsed.path.endswith("/documents"):
            query_values = parse_qs(parsed.query).get("queries[]", [])
            if query_values:
                self._send(200, {"documents": [{"$id": "row-1", "status": "approved"}], "total": 1})
            else:
                self._send(200, {"documents": [], "total": 0})
        else:
            self._send(404, {"message": "Not found"})

    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length)
        FakeAppwriteHandler.requests_seen.append(("POST", urlparse(self.path).path, self.headers, "", body))
        if self.headers.get("Content-Type", "").startswith("multipart/form-data"):
            self._send(201, {"$id": "audio-1"})
            return
        payload = json.loads(body.decode())
        self._send(201, {"$id": payload.get("documentId"), "data": payload.get("data")})


class AppwriteStoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        FakeAppwriteHandler.requests_seen = []
        cls.server = HTTPServer(("127.0.0.1", 0), FakeAppwriteHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.endpoint = f"http://127.0.0.1:{cls.server.server_port}/v1"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.thread.join(timeout=3)
        cls.server.server_close()

    def setUp(self):
        FakeAppwriteHandler.requests_seen.clear()

    def test_private_document_write_uses_server_key_and_empty_permissions(self):
        with patch.multiple(
            appwrite_store,
            APPWRITE_ENDPOINT=self.endpoint,
            APPWRITE_PROJECT_ID="bank",
            APPWRITE_API_KEY="unit-test-only",
            APPWRITE_DATABASE_ID="safinum",
        ):
            document = appwrite_store.create_document(
                "translation_suggestions", "row-1", {"status": "pending_review"}
            )
        self.assertEqual(document["$id"], "row-1")
        method, path, headers, _query, body = FakeAppwriteHandler.requests_seen[0]
        self.assertEqual((method, path), ("POST", "/v1/databases/safinum/collections/translation_suggestions/documents"))
        self.assertEqual(headers.get("X-Appwrite-Key"), "unit-test-only")
        self.assertEqual(json.loads(body.decode())["permissions"], [])

    def test_equality_query_and_count_are_server_side(self):
        with patch.multiple(
            appwrite_store,
            APPWRITE_ENDPOINT=self.endpoint,
            APPWRITE_PROJECT_ID="bank",
            APPWRITE_API_KEY="unit-test-only",
            APPWRITE_DATABASE_ID="safinum",
        ):
            rows = appwrite_store.list_documents("translation_suggestions", equals={"status": "approved"})
            count = appwrite_store.all_count("translation_suggestions", equals={"status": "approved"})
        self.assertEqual(rows[0]["$id"], "row-1")
        self.assertEqual(count, 1)
        self.assertTrue(
            any(
                'equal("status",["approved"])' in parse_qs(query).get("queries[]", [""])[0]
                for *_, query, _body in FakeAppwriteHandler.requests_seen
            )
        )

    def test_audio_upload_is_multipart_and_does_not_make_file_public(self):
        with patch.multiple(
            appwrite_store,
            APPWRITE_ENDPOINT=self.endpoint,
            APPWRITE_PROJECT_ID="bank",
            APPWRITE_API_KEY="unit-test-only",
            APPWRITE_AUDIO_BUCKET_ID="safinum-audio",
        ):
            result = appwrite_store.upload_private_audio("audio-1", "audio-1.webm", "audio/webm", b"test-audio")
        self.assertEqual(result["$id"], "audio-1")
        method, path, headers, _query, body = FakeAppwriteHandler.requests_seen[0]
        self.assertEqual((method, path), ("POST", "/v1/storage/buckets/safinum-audio/files"))
        self.assertIn("multipart/form-data", headers.get("Content-Type", ""))
        self.assertIn(b"test-audio", body)
        self.assertNotIn(b"role:any", body)


if __name__ == "__main__":
    unittest.main()
