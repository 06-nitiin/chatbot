import unittest
from unittest.mock import patch

import app as app_module


class FlaskRouteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app_module.app.config.update(
            TESTING=True,
            SECRET_KEY="test-secret-key",
            SESSION_COOKIE_SECURE=False,
        )

    def setUp(self):
        self.client = app_module.app.test_client()

    def test_health_endpoint_returns_ok(self):
        response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"status": "ok"})

    def test_homepage_uses_the_current_intent_count(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            f"intents loaded: <span id=\"intent-count\">{len(app_module.bot_engine.INTENTS)}</span>",
            response.get_data(as_text=True),
        )

    def test_chat_rejects_an_empty_message(self):
        response = self.client.post("/api/chat", json={"message": "   "})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json(), {"error": "message is required"})

    def test_chat_returns_rule_response_and_metadata(self):
        response = self.client.post("/api/chat", json={"message": "thanks"})
        data = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["response"], "You're welcome!")
        self.assertEqual(data["source"], "rules")
        self.assertEqual(data["intent"], "thanks_reply")
        self.assertTrue(data["matched"])

    def test_stream_returns_rule_response_and_done_event(self):
        response = self.client.post("/api/chat/stream", json={"message": "thanks"})
        body = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "text/event-stream")
        self.assertIn('"type": "chunk"', body)
        self.assertIn("You're welcome!", body)
        self.assertIn('"source": "rules"', body)
        self.assertIn('"intent": "thanks_reply"', body)

    @patch.object(app_module.llm_fallback, "is_configured", return_value=False)
    def test_stream_uses_canned_fallback_when_llm_is_not_configured(self, _mock_is_configured):
        response = self.client.post(
            "/api/chat/stream",
            json={"message": "tell me something unrelated"},
        )
        body = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "text/event-stream")
        self.assertIn('"type": "chunk"', body)
        self.assertIn('"text": "', body)
        self.assertIn('"source": "fallback"', body)

    def test_stream_saves_rule_conversation_history(self):
        self.client.post("/api/chat/stream", json={"message": "thanks"})

        with self.client.session_transaction() as session:
            self.assertEqual(
                session["history"],
                [
                    {"role": "user", "message": "thanks"},
                    {"role": "bot", "message": "You're welcome!"},
                ],
            )

    def test_clear_removes_the_session_history(self):
        with self.client.session_transaction() as session:
            session["history"] = [
                {"role": "user", "message": "hello"},
                {"role": "bot", "message": "Hello!"},
            ]

        response = self.client.post("/api/clear")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"status": "cleared"})
        with self.client.session_transaction() as session:
            self.assertNotIn("history", session)

    def test_append_bot_reply_saves_a_valid_reply(self):
        response = self.client.post(
            "/api/chat/append-bot-reply",
            json={"message": "This is a streamed reply."},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"status": "ok"})
        with self.client.session_transaction() as session:
            self.assertEqual(
                session["history"],
                [{"role": "bot", "message": "This is a streamed reply."}],
            )

    def test_append_bot_reply_rejects_an_empty_message(self):
        response = self.client.post("/api/chat/append-bot-reply", json={"message": ""})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json(), {"error": "message is required"})


if __name__ == "__main__":
    unittest.main()
