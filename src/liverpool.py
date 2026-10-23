"""Precio principal de Liverpool: extractor conservador de SKU, memoria y oferta."""
import re
from urllib.parse import urlparse


def extract_liverpool(soup, product, source, title):
    if source.get("store") != "Liverpool":
        raise ValueError("Extractor Liverpool exclusivo")
    path = urlparse(source.get("url", "")).path.rstrip("/")
    code = path.rsplit("/", 1)[-1]
    if not re.fullmatch(r"\d{9,12}", code):
        raise ValueError("La URL no identifica un producto Liverpool")
    text = soup.get_text(" ", strip=True)
    markers = list(re.finditer(r"C[oó]digo de producto:\s*(\d{9,12})\b", text, re.I))
    found = [m for m in markers if m.group(1) == code]
    if len(found) != 1:
        raise ValueError("Código Liverpool no confirmado en la página")
    section = text[found[0].start():found[0].start() + 2400]
    header = section[:400]
    if not re.search(r"\bXIAOMI\b", header, re.I):
        raise ValueError("Marca Xiaomi no confirmada")
    match_title = re.search(re.escape(title), header, re.I)
    if not match_title:
        raise ValueError("Título del producto no confirmado")
    after = section[match_title.end():]
    # No confundir el precio del equipo con mensualidades o seguros.
    area = re.split(
        r"Y/o hasta|Consulta las opciones de pago|Ver disponibilidad en tienda|Color:",
        after, maxsplit=1, flags=re.I,
    )[0]
    prices = re.findall(r"\$\s*([\d,]+)\.(\d{2})", area)
    if not prices or len(prices) > 2:
        raise ValueError("Precio principal no inequívoco")
    cents = [int(p.replace(",", "")) * 100 + int(dec) for p, dec in prices]
    price = cents[0]  # Con precio tachado, el descuento aparece primero.
    if len(cents) == 2 and cents[1] < cents[0]:
        raise ValueError("Orden de precios ambiguo")
    if not (300000 <= price <= 8000000):
        raise ValueError("Precio inválido")
    selection = re.search(r"Tama(?:ñ|n)o:\s*(.*?)Cantidad:", section, re.I)
    if not selection:
        raise ValueError("No aparece la selección de memoria")
    units = re.findall(r"(?<!\d)(\d+)\s*(GB|TB)\b", selection.group(1), re.I)
    if not units or any(n != "512" or u.upper() != "GB" for n, u in units):
        raise ValueError("Memoria de 512 GB no confirmada como única variante")
    buy_area = section.split("Cantidad:", 1)[-1].split("Adquiere Liverpool Care", 1)[0]
    if not re.search(r"Comprar ahora|Agregar a mi bolsa", buy_area, re.I):
        raise ValueError("La ficha no ofrece compra")
    if re.search(r"Agotado|Sin existencias|No disponible", buy_area, re.I):
        raise ValueError("Producto agotado")
    snippet = section[match_title.end():section.find("Adquiere Liverpool Care")]
    coupon = re.search(r"\bCup[oó]n\b.{0,45}", snippet, re.I)
    promo = re.search(r"\b(?:promoci[oó]n especial|descuento especial)\b.{0,45}", snippet, re.I)
    msi = bool(re.search(r"\d{1,2}\s+meses sin intereses", snippet, re.I))
    return {
        "price": price, "title": title,
        "coupon": coupon.group(0) if coupon else "",
        "promo": promo.group(0) if promo else "",
        "msi": int(msi),
    }
