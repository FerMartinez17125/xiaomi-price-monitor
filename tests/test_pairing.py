import os
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch
from src.telegram import (
    save_chat_id, load_chat_id, credentials, TelegramConfigError
)
from src.telegram_pair import find_private_chat

TOKEN = "123456:TEST_TOKEN_SECRET"
CHAT = 123456789


class TelegramPairTests(unittest.TestCase):
    def test_encrypt_decrypt_without_plain_id(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "id.enc"
            save_chat_id(CHAT, token=TOKEN, destination=p)
            self.assertNotIn(str(CHAT).encode(), p.read_bytes())
            self.assertEqual(load_chat_id(token=TOKEN, source=p), str(CHAT))

    def test_changed_token_requires_repair(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "id.enc"
            save_chat_id(CHAT, token=TOKEN, destination=p)
            with self.assertRaises(TelegramConfigError):
                load_chat_id(token="123456:DIFFERENT_TOKEN", source=p)

    def test_pair_valid_private_chat(self):
        now = int(time.time())
        code = "MiClaveSegura_123"
        response = {
            "ok": True,
            "result": [{
                "update_id": 42,
                "message": {
                    "date": now - 20,
                    "text": "/vincular " + code,
                    "chat": {"id": CHAT, "type": "private"},
                    "from": {"id": CHAT}
                }
            }]
        }
        with patch("src.telegram_pair.requests.get") as get:
            get.return_value.status_code = 200
            get.return_value.json.return_value = response
            self.assertEqual(find_private_chat(code, TOKEN, now=now), CHAT)

    def test_ignore_public_groups_and_stale_messages(self):
        now = int(time.time())
        code = "MiClaveSegura_123"
        response = {
            "ok": True,
            "result": [
                {"message": {"date": now - 1500,
                  "text": "/vincular " + code,
                  "chat": {"id": CHAT, "type": "private"},
                  "from": {"id": CHAT}}},
                {"message": {"date": now - 30,
                  "text": "/vincular " + code,
                  "chat": {"id": -123, "type": "supergroup"},
                  "from": {"id": 55}}}
            ]
        }
        with patch("src.telegram_pair.requests.get") as get:
            get.return_value.status_code = 200
            get.return_value.json.return_value = response
            with self.assertRaises(RuntimeError):
                find_private_chat(code, TOKEN, now=now)

    def test_short_code_rejected(self):
        with self.assertRaises(ValueError):
            find_private_chat("123", TOKEN)

if __name__ == "__main__":
    unittest.main()
