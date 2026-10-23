import os
import unittest
from unittest.mock import patch
from src.telegram import credentials, TelegramConfigError, send_message


class TelegramTests(unittest.TestCase):
    def test_without_credentials(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(TelegramConfigError):
                credentials()

    def test_invalid_chat(self):
        with patch.dict(os.environ, {
            "TELEGRAM_BOT_TOKEN": "123:ABC_def-xyz",
            "TELEGRAM_CHAT_ID": "not-a-number",
        }, clear=True):
            with self.assertRaises(TelegramConfigError):
                credentials()

    def test_success_payload(self):
        env = {
            "TELEGRAM_BOT_TOKEN": "123:ABC_def-xyz",
            "TELEGRAM_CHAT_ID": "12345678",
        }
        with patch.dict(os.environ, env, clear=True):
            with patch("src.telegram.requests.post") as post:
                post.return_value.status_code = 200
                post.return_value.json.return_value = {"ok": True}
                self.assertTrue(send_message("Oferta detectada"))
                self.assertEqual(post.call_args.kwargs["json"]["chat_id"], "12345678")
                self.assertEqual(post.call_args.kwargs["json"]["text"], "Oferta detectada")
                self.assertEqual(post.call_args.kwargs["timeout"], 20)

    def test_api_error_does_not_leak_secret(self):
        env = {
            "TELEGRAM_BOT_TOKEN": "123:ABC_def-xyz",
            "TELEGRAM_CHAT_ID": "12345678",
        }
        with patch.dict(os.environ, env, clear=True):
            with patch("src.telegram.requests.post") as post:
                post.return_value.status_code = 401
                post.return_value.json.return_value = {"ok": False}
                with self.assertRaisesRegex(RuntimeError, "HTTP 401") as caught:
                    send_message("Prueba")
                self.assertNotIn(env["TELEGRAM_BOT_TOKEN"], str(caught.exception))


if __name__ == "__main__":
    unittest.main()
