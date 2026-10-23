"""Asociación de un chat privado mediante un código de un solo uso.

El usuario envía /vincular CODIGO a su bot, y después ejecuta el workflow
Vincular Telegram con el mismo código. No requiere copiar el Chat ID.
"""
import os
import re
import sys
import time

import requests

from .telegram import bot_token, save_chat_id, send_message

PATTERN = re.compile(r"[A-Za-z0-9_-]{12,64}")


def find_private_chat(code, token, now=None):
    if not PATTERN.fullmatch(code):
        raise ValueError("El código debe tener entre 12 y 64 caracteres: letras, números, - o _")
    now = int(now or time.time())
    try:
        response = requests.get(
            "https://api.telegram.org/bot" + token + "/getUpdates",
            params={"timeout": 0, "limit": 100,
                    "allowed_updates": '["message"]'},
            timeout=20,
        )
        data = response.json()
    except (requests.RequestException, ValueError):
        raise RuntimeError("No fue posible consultar Telegram") from None
    if response.status_code != 200 or not data.get("ok"):
        raise RuntimeError("Telegram rechazó la consulta de vinculación")
    matches = []
    expected = "/vincular " + code
    for item in data.get("result", []):
        msg = item.get("message") or {}
        chat = msg.get("chat") or {}
        sender = msg.get("from") or {}
        date = msg.get("date", 0)
        if (msg.get("text", "").strip() == expected
            and chat.get("type") == "private"
            and isinstance(chat.get("id"), int)
            and sender.get("id") == chat["id"]
            and isinstance(date, int)
            and now - 600 <= date <= now + 30):
            matches.append(chat["id"])
    if len(set(matches)) != 1:
        raise RuntimeError(
            "No se encontró exactamente un chat privado con /vincular y ese código "
            "en los últimos 10 minutos. Envíalo de nuevo al bot e inténtalo otra vez."
        )
    return matches[0]


def main():
    code = os.getenv("PAIRING_CODE", "")
    token = bot_token()
    chat = find_private_chat(code, token)
    save_chat_id(chat, token)
    print("Se encontró un chat privado válido y se guardó su identificador cifrado.")
    # GitHub Actions guardará el archivo cifrado en el repositorio antes
    # de ejecutar un envío de prueba desde otro paso del workflow.


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, ValueError) as exc:
        sys.exit(str(exc))
