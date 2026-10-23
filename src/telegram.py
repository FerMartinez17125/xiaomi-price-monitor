"""Notificaciones directas a un chat de Telegram usando la API oficial."""
import os
import re

import requests


class TelegramConfigError(ValueError):
    """Se necesitan las credenciales secretas de GitHub Actions."""


def credentials():
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()
    if not token or not chat_id:
        raise TelegramConfigError(
            "Configura TELEGRAM_BOT_TOKEN y TELEGRAM_CHAT_ID como GitHub Actions Secrets"
        )
    if not re.fullmatch(r"\d+:[A-Za-z0-9_-]+", token):
        raise TelegramConfigError("Formato de token de bot inválido")
    if not re.fullmatch(r"-?\d+", chat_id):
        raise TelegramConfigError("El Chat ID debe ser numérico")
    return token, chat_id


def send_message(message):
    """Devuelve True cuando Telegram acepta el mensaje; no revela el token."""
    token, chat_id = credentials()
    if not isinstance(message, str) or not message.strip():
        raise ValueError("Mensaje vacío")
    # El token se inserta únicamente en la solicitud HTTPS, nunca en los logs.
    url = "https://api.telegram.org/bot" + token + "/sendMessage"
    try:
        response = requests.post(
            url,
            json={
                "chat_id": chat_id,
                "text": message[:4000],
                "disable_web_page_preview": True,
            },
            timeout=20,
        )
    except requests.RequestException as exc:
        raise RuntimeError("Fallo de conexión al enviar el mensaje a Telegram") from None
    try:
        data = response.json()
    except ValueError:
        data = {}
    if response.status_code != 200 or not data.get("ok"):
        # No registramos URLs completas o errores HTTP que puedan contener tokens.
        raise RuntimeError(f"Telegram rechazó el envío (HTTP {response.status_code})")
    return True


if __name__ == "__main__":
    print("Este módulo se utiliza desde GitHub Actions.")
