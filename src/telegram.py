"""Canal Telegram privado para el monitor Xiaomi.

El chat se puede configurar con TELEGRAM_CHAT_ID o mediante el proceso
de vinculación, que cifra su identificador con una clave derivada del token.
"""
import base64
import hashlib
import os
import re
from pathlib import Path

import requests
from cryptography.fernet import Fernet, InvalidToken

ROOT = Path(__file__).resolve().parents[1]
CHAT_FILE = ROOT / "data" / "telegram_chat.enc"
TOKEN_PATTERN = re.compile(r"\d+:[A-Za-z0-9_-]+")
CHAT_PATTERN = re.compile(r"-?\d+")


class TelegramConfigError(ValueError):
    """Configuración incompleta o vinculación inválida."""


def bot_token():
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    if not TOKEN_PATTERN.fullmatch(token):
        raise TelegramConfigError("Configura TELEGRAM_BOT_TOKEN con un token válido en GitHub Secrets")
    return token


def _cipher(token):
    digest = hashlib.sha256(b"xiaomi-price-monitor:v1:telegram-chat\x00" + token.encode("utf-8")).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def save_chat_id(chat_id, token=None, destination=None):
    token = token or bot_token()
    chat_id = str(chat_id)
    if not CHAT_PATTERN.fullmatch(chat_id):
        raise TelegramConfigError("Chat ID no válido")
    path = Path(destination) if destination else CHAT_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(_cipher(token).encrypt(chat_id.encode("ascii")) + b"\n")


def load_chat_id(token=None, source=None):
    token = token or bot_token()
    path = Path(source) if source else CHAT_FILE
    if not path.is_file():
        return None
    try:
        chat = _cipher(token).decrypt(path.read_bytes().strip()).decode("ascii")
    except (InvalidToken, ValueError, UnicodeDecodeError) as exc:
        raise TelegramConfigError(
            "No se puede descifrar el chat. Si cambiaste el token, vuelve a vincular el bot."
        ) from None
    if not CHAT_PATTERN.fullmatch(chat):
        raise TelegramConfigError("Chat ID almacenado no válido")
    return chat


def credentials():
    token = bot_token()
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()
    if not chat_id:
        chat_id = load_chat_id(token)
    if not chat_id:
        raise TelegramConfigError(
            "Falta vincular el bot: Actions > Vincular Telegram > Run workflow"
        )
    if not CHAT_PATTERN.fullmatch(chat_id):
        raise TelegramConfigError("TELEGRAM_CHAT_ID debe ser numérico")
    return token, chat_id


def send_message(message):
    """True si Telegram acepta el envío (sin prometer entrega al dispositivo)."""
    token, chat_id = credentials()
    if not isinstance(message, str) or not message.strip():
        raise ValueError("Mensaje vacío")
    try:
        response = requests.post(
            "https://api.telegram.org/bot" + token + "/sendMessage",
            json={"chat_id": chat_id, "text": message[:4000],
                  "disable_web_page_preview": True},
            timeout=20,
        )
    except requests.RequestException:
        raise RuntimeError("No se pudo conectar con Telegram") from None
    try:
        data = response.json()
    except ValueError:
        data = {}
    if response.status_code != 200 or not data.get("ok"):
        raise RuntimeError(f"Telegram rechazó el envío (HTTP {response.status_code})")
    return True
