import os
import unittest
from unittest.mock import patch
from src.whatsapp import (
    credentials, WhatsAppConfigurationError,
    payload_from_alert, send_template
)


class WhatsAppTest(unittest.TestCase):
    def test_parse_price_alert(self):
        msg = (
            "Xiaomi 17 512 GB — Liverpool\n"
            "$17,499.00 MXN\n"
            "Bajó 6% (>5%)\n"
            "https://www.liverpool.com.mx/tienda/pdp/demo"
        )
        self.assertEqual(
            payload_from_alert(msg),
            ["Xiaomi 17 512 GB", "Liverpool", "$17,499.00 MXN",
             "Bajó 6% (>5%)", "https://www.liverpool.com.mx/tienda/pdp/demo"]
        )

    def test_bad_url_rejected(self):
        msg = "Xiaomi 17 512 GB — Liverpool\n$16,000 MXN\nBajó 10%\nhttps://example.com"
        with self.assertRaises(ValueError):
            payload_from_alert(msg)

    def test_secret_validation(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(WhatsAppConfigurationError):
                credentials()

    def test_template_payload(self):
        env = {
            "WHATSAPP_ACCESS_TOKEN": "not-a-real-token",
            "WHATSAPP_PHONE_NUMBER_ID": "123456789",
            "WHATSAPP_TO": "5215512345678",
        }
        with patch.dict(os.environ, env, clear=True):
            with patch("src.whatsapp.requests.post") as post:
                post.return_value.ok = True
                post.return_value.json.return_value = {"messages": [{"id": "example"}]}
                send_template(["modelo", "tienda", "precio", "motivo", "url"])
                body = post.call_args.kwargs["json"]
                self.assertEqual(body["type"], "template")
                self.assertEqual(body["to"], "5215512345678")
                self.assertEqual(body["template"]["name"], "xiaomi_monitor_aviso")
                self.assertEqual(len(body["template"]["components"][0]["parameters"]), 5)

    def test_hello_world_no_params(self):
        env = {
            "WHATSAPP_ACCESS_TOKEN": "not-a-real-token",
            "WHATSAPP_PHONE_NUMBER_ID": "123456789",
            "WHATSAPP_TO": "5215512345678",
        }
        with patch.dict(os.environ, env, clear=True):
            with patch("src.whatsapp.requests.post") as post:
                post.return_value.ok = True
                post.return_value.json.return_value = {"messages": [{"id": "example"}]}
                send_template(name="hello_world", language="en_US")
                self.assertNotIn("components", post.call_args.kwargs["json"]["template"])


if __name__ == "__main__":
    unittest.main()
