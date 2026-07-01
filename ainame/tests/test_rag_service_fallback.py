import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from core import rag_service


class RagServiceFallbackTest(unittest.TestCase):
    def test_missing_collection_returns_not_uploaded_message(self):
        with TemporaryDirectory() as temp_dir:
            with patch.object(rag_service, "DB_PATH", str(Path(temp_dir) / "missing_db")):
                with patch.object(rag_service, "RAG_IMPORT_ERROR", None):
                    result = rag_service.retrive_user_from_knowledge(123, "\u73af\u4fdd\u65b0\u6750\u6599")

        self.assertIn("\u5c1a\u672a\u4e0a\u4f20\u4f01\u4e1a\u77e5\u8bc6\u5e93", result)

    def test_existing_collection_with_no_results_returns_empty_result_message(self):
        class FakeChroma:
            def __init__(self, **kwargs):
                pass

            def similarity_search(self, query, k=2):
                return []

        with patch.object(rag_service, "RAG_IMPORT_ERROR", None):
            with patch.object(rag_service, "_collection_exists", return_value=True):
                with patch.object(rag_service, "Chroma", FakeChroma):
                    result = rag_service.retrive_user_from_knowledge(123, "\u73af\u4fdd\u65b0\u6750\u6599")

        self.assertIn("\u672c\u6b21\u672a\u68c0\u7d22\u5230\u76f8\u5173\u5185\u5bb9", result)

    def test_retrieval_exception_returns_service_unavailable_message(self):
        class BrokenChroma:
            def __init__(self, **kwargs):
                raise RuntimeError("embedding service down")

        with patch.object(rag_service, "RAG_IMPORT_ERROR", None):
            with patch.object(rag_service, "_collection_exists", return_value=True):
                with patch.object(rag_service, "Chroma", BrokenChroma):
                    result = rag_service.retrive_user_from_knowledge(123, "\u73af\u4fdd\u65b0\u6750\u6599")

        self.assertIn("\u77e5\u8bc6\u5e93\u68c0\u7d22\u670d\u52a1\u6682\u65f6\u4e0d\u53ef\u7528", result)


if __name__ == "__main__":
    unittest.main()
