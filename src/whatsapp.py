"""Envío seguro de plantillas mediante la API oficial de WhatsApp Cloud."""
import json
import os
import re
import sys

import requests

GRAPH_VERSION = os.getenv("WHATSAPP_GRAPH_VERSION", "v26.0")
REQUIRED = ("WHATSAPP_ACCESS_TOKEN", "WHATSAPP_PHONE_NUMBER_ID", "WHATSAPP_TO")
DEFAULT_TEMPLATE = "xiaomi_monitor_aviso"
DEFAULT_LANGUAGE = "es_MX"


class WhatsAppConfigurationError(ValueError):
    pass


def credentials():
    data = {key: os.getenv(key, "").strip() for key in REQUIRED}
    absent = [key for key, value in data.items() if not value]
    if absent:
        raise WhatsAppConfigurationError("Faltan secretos de WhatsApp: " + ", ".join(absent))
    if not re.fullmatch(r"\d{10,15}", data["WHATSAPP_TO"]):
        raise WhatsAppConfigurationError("WHATSAPP_TO debe contener únicamente dígitos, con prefijo de país")
    if not re.fullmatch(r"\d+", data["WHATSAPP_PHONE_NUMBER_ID"]):
        raise WhatsAppConfigurationError("WHATSAPP_PHONE_NUMBER_ID inválido")
    if not re.fullmatch(r"v\d+\.0", GRAPH_VERSION):
        raise WhatsAppConfigurationError("Versión Graph inválida")
    return data


def payload_from_alert(message):
    """Mapear mensajes de la cola anterior al formato fijo de plantilla aprobada."""
    if not isinstance(message, str) or not message.strip():
        raise ValueError("Mensaje vacío")
    rows = message.splitlines()
    if rows[0].startswith("Monitor Xiaomi:"):
        return ["Monitor Xiaomi", "Xiaomi y Liverpool", "Sin cotización",
                rows[0][:350], "https://github.com/FerMartinez17125/xiaomi-price-monitor/blob/main/reports/latest.md"]
    first = rows[0].split(" — ", 1)
    if len(first) != 2 or len(rows) < 4:
        raise ValueError("Formato de alerta de precio no reconocido")
    product, store = first
    price = rows[1]
    url = rows[-1]
    reasons = "; ".join(rows[2:-1])
    if not url.startswith(("https://www.mi.com/", "https://www.liverpool.com.mx/")):
        raise ValueError("URL de oferta no validada")
    return [product[:100], store[:100], price[:80], reasons[:350], url[:400]]


def send_template(params=None, name=None, language=None):
    """Aceptación por Meta, no garantía de entrega final (requiere webhooks)."""
    creds = credentials()
    name = name or os.getenv("WHATSAPP_TEMPLATE_NAME", DEFAULT_TEMPLATE)
    language = language or os.getenv("WHATSAPP_TEMPLATE_LANGUAGE", DEFAULT_LANGUAGE)
    if not re.fullmatch(r"[a-z][a-z0-9_]{1,80}", name):
        raise WhatsAppConfigurationError("Nombre de plantilla inválido")
    body = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": creds["WHATSAPP_TO"],
        "type": "template",
        "template": {"name": name, "language": {"code": language}},
    }
    if params is not None:
        body["template"]["components"] = [{
            "type": "body",
            "parameters": [{"type": "text", "text": str(p)} for p in params],
        }]
    endpoint = (f"https://graph.facebook.com/{GRAPH_VERSION}/"
                f"{creds['WHATSAPP_PHONE_NUMBER_ID']}/messages")
    response = requests.post(
        endpoint,
        headers={"Authorization": "Bearer " + creds["WHATSAPP_ACCESS_TOKEN"]},
        json=body,
        timeout=25,
    )
    try:
        result = response.json()
    except ValueError:
        result = {}
    if not response.ok or not result.get("messages"):
        error = result.get("error", {}) if isinstance(result, dict) else {}
        code = error.get("code", "desconocido") if isinstance(error, dict) else "desconocido"
        raise RuntimeError(f"Meta WhatsApp: HTTP {response.status_code}, error {code}")
    return True


def send_price_notification(message):
    return send_template(payload_from_alert(message))


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] != "--test":
        sys.exit("Uso: python -m src.whatsapp --test")
    # Meta provee hello_world para pruebas de Cloud API; requiere destinatario autorizado.
    send_template(params=None, name="hello_world", language="en_US")
    print("Meta aceptó el mensaje de prueba; confirma su llegada en WhatsApp.")
