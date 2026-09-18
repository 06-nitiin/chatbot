import unittest

import bot_engine
import long_responses


class BestRuleMatchTests(unittest.TestCase):
    def test_greeting_matches_the_greeting_intent(self):
        response, confidence, matched, intent_id = bot_engine.best_rule_match("hello")

        self.assertTrue(matched)
        self.assertEqual(intent_id, "greeting")
        self.assertEqual(response, "Hello!")
        self.assertGreaterEqual(confidence, bot_engine.CONFIDENCE_THRESHOLD)

    def test_typo_tolerance_matches_a_greeting(self):
        response, confidence, matched, intent_id = bot_engine.best_rule_match("helo")

        self.assertTrue(matched)
        self.assertEqual(intent_id, "greeting")
        self.assertEqual(response, "Hello!")
        self.assertGreaterEqual(confidence, bot_engine.CONFIDENCE_THRESHOLD)

    def test_required_words_prevent_a_partial_advice_match(self):
        response, confidence, matched, intent_id = bot_engine.best_rule_match("give")

        self.assertFalse(matched)
        self.assertIsNone(response)
        self.assertIsNone(intent_id)
        self.assertLess(confidence, bot_engine.CONFIDENCE_THRESHOLD)

    def test_unrelated_message_does_not_match_a_rule(self):
        response, confidence, matched, intent_id = bot_engine.best_rule_match(
            "what is the capital of France"
        )

        self.assertFalse(matched)
        self.assertIsNone(response)
        self.assertIsNone(intent_id)
        self.assertLess(confidence, bot_engine.CONFIDENCE_THRESHOLD)

    def test_capabilities_intent(self):
        response, confidence, matched, intent_id = bot_engine.best_rule_match(
            "What can you do?"
        )

        self.assertTrue(matched)
        self.assertEqual(intent_id, "capabilities")
        self.assertEqual(response, long_responses.R_CAPABILITIES)
        self.assertGreaterEqual(confidence, bot_engine.CONFIDENCE_THRESHOLD)

    def test_creator_intent(self):
        response, confidence, matched, intent_id = bot_engine.best_rule_match(
            "Who created you?"
        )

        self.assertTrue(matched)
        self.assertEqual(intent_id, "creator")
        self.assertEqual(response, long_responses.R_CREATOR)
        self.assertGreaterEqual(confidence, bot_engine.CONFIDENCE_THRESHOLD)

    def test_joke_intent(self):
        response, confidence, matched, intent_id = bot_engine.best_rule_match(
            "Tell me a joke"
        )

        self.assertTrue(matched)
        self.assertEqual(intent_id, "joke")
        self.assertEqual(response, long_responses.R_JOKE)
        self.assertGreaterEqual(confidence, bot_engine.CONFIDENCE_THRESHOLD)

    def test_quote_intent(self):
        response, confidence, matched, intent_id = bot_engine.best_rule_match(
            "Give me a quote"
        )

        self.assertTrue(matched)
        self.assertEqual(intent_id, "quote")
        self.assertEqual(response, long_responses.R_QUOTE)
        self.assertGreaterEqual(confidence, bot_engine.CONFIDENCE_THRESHOLD)


class ResponseRoutingTests(unittest.TestCase):
    def test_rule_response_uses_the_rules_source(self):
        response, confidence, matched, source, intent_id = (
            bot_engine.get_response_with_confidence(
                "thanks", allow_llm_fallback=False
            )
        )

        self.assertEqual(response, "You're welcome!")
        self.assertGreaterEqual(confidence, bot_engine.CONFIDENCE_THRESHOLD)
        self.assertTrue(matched)
        self.assertEqual(source, "rules")
        self.assertEqual(intent_id, "thanks_reply")

    def test_unmatched_response_can_use_the_canned_fallback(self):
        response, confidence, matched, source, intent_id = (
            bot_engine.get_response_with_confidence(
                "tell me something completely unrelated", allow_llm_fallback=False
            )
        )

        self.assertIsInstance(response, str)
        self.assertTrue(response)
        self.assertLess(confidence, bot_engine.CONFIDENCE_THRESHOLD)
        self.assertFalse(matched)
        self.assertEqual(source, "fallback")
        self.assertIsNone(intent_id)


if __name__ == "__main__":
    unittest.main()
