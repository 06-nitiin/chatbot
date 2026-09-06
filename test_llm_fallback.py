import json
import unittest
from unittest.mock import Mock, patch

import llm_fallback


class LLMFallbackTests(unittest.TestCase):
    def setUp(self):
        self.original_api_key = llm_fallback.GEMINI_API_KEY
        llm_fallback.GEMINI_API_KEY = "test-key"

    def tearDown(self):
        llm_fallback.GEMINI_API_KEY = self.original_api_key

    def test_missing_api_key_raises_llm_unavailable(self):
        llm_fallback.GEMINI_API_KEY = ""

        with self.assertRaises(llm_fallback.LLMUnavailable):
            llm_fallback.ask_llm("hello")

    @patch("llm_fallback.requests.post")
    def test_successful_response_returns_text(self, mock_post):
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "candidates": [
                {"content": {"parts": [{"text": "  Hello from Gemini.  "}]}}
            ]
        }
        mock_post.return_value = response

        result = llm_fallback.ask_llm("hello")

        self.assertEqual(result, "Hello from Gemini.")
        mock_post.assert_called_once()

    @patch("llm_fallback.requests.post")
    def test_malformed_response_raises_llm_unavailable(self, mock_post):
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {"candidates": []}
        mock_post.return_value = response

        with self.assertRaises(llm_fallback.LLMUnavailable):
            llm_fallback.ask_llm("hello")

    @patch("llm_fallback.requests.post")
    def test_stream_returns_text_chunks(self, mock_post):
        response = Mock()
        response.raise_for_status.return_value = None
        response.iter_lines.return_value = [
            "data: " + json.dumps(
                {"candidates": [{"content": {"parts": [{"text": "Hello"}]}}]}
            ),
            "data: " + json.dumps(
                {"candidates": [{"content": {"parts": [{"text": " there!"}]}}]}
            ),
            "data: [DONE]",
        ]
        response.__enter__ = Mock(return_value=response)
        response.__exit__ = Mock(return_value=None)
        mock_post.return_value = response

        result = list(llm_fallback.ask_llm_stream("hello"))

        self.assertEqual(result, ["Hello", " there!"])

    @patch("llm_fallback.requests.post")
    def test_empty_stream_raises_llm_unavailable(self, mock_post):
        response = Mock()
        response.raise_for_status.return_value = None
        response.iter_lines.return_value = ["data: [DONE]"]
        response.__enter__ = Mock(return_value=response)
        response.__exit__ = Mock(return_value=None)
        mock_post.return_value = response

        with self.assertRaises(llm_fallback.LLMUnavailable):
            list(llm_fallback.ask_llm_stream("hello"))


if __name__ == "__main__":
    unittest.main()
