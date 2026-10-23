"""Regresión: precio Liverpool, SKU exacto, mensualidades y variantes."""
import unittest

from src.monitor import extract


SRC = {
    "id": "liverpool-17", "store": "Liverpool",
    "url": "https://www.liverpool.com.mx/tienda/pdp/xiaomi-17-amoled-6-3-pulgadas/1196389537",
}
PRODUCT = {"id": "xiaomi-17-512", "name": "Xiaomi 17"}


def html(model="17 AMOLED 6.3 pulgadas", code="1196389537", memory="512 GB 512 GB",
         prices="$24,999.00", buy="Comprar ahora Agregar a mi bolsa"):
    return (
        "<html><body><main>Detalles del Producto "
        "Código de producto: " + code + " XIAOMI <h1>" + model + "</h1> "
        + prices +
        " Y/o hasta 13 meses sin intereses de $1,923.00 "
        "Consulta las opciones de pago Ver disponibilidad en tienda "
        "Color: Negro Tamaño: " + memory + " Cantidad: " + buy +
        " Adquiere Liverpool Care Plan Robo + Daño $5,059.00"
        "</main></body></html>"
    )


class LiverpoolTests(unittest.TestCase):
    def test_main_price_not_installment_or_insurance(self):
        q = extract(html(), PRODUCT, SRC)
        self.assertEqual(q["price"], 2499900)
        self.assertEqual(q["msi"], 1)

    def test_discount_price_first(self):
        q = extract(html(prices="$19,999.00 $24,999.00"), PRODUCT, SRC)
        self.assertEqual(q["price"], 1999900)

    def test_duplicate_prices_from_responsive_layout(self):
        q = extract(
            html(prices="$24,999.00 $24,999.00 $24,999.00"),
            PRODUCT, SRC,
        )
        self.assertEqual(q["price"], 2499900)

    def test_duplicate_discount_and_list(self):
        q = extract(
            html(prices="$19,999.00 $19,999.00 $24,999.00 $24,999.00"),
            PRODUCT, SRC,
        )
        self.assertEqual(q["price"], 1999900)

    def test_three_distinct_prices_rejected(self):
        with self.assertRaises(ValueError):
            extract(html(prices="$19,999.00 $21,999.00 $24,999.00"), PRODUCT, SRC)

    def test_inverted_price_rejected(self):
        with self.assertRaises(ValueError):
            extract(html(prices="$24,999.00 $19,999.00"), PRODUCT, SRC)

    def test_wrong_model(self):
        with self.assertRaises(ValueError):
            extract(html(model="17T Pro AMOLED 6.8 pulgadas"), PRODUCT, SRC)

    def test_wrong_product_code(self):
        with self.assertRaises(ValueError):
            extract(html(code="1184551224"), PRODUCT, SRC)

    def test_mixed_memories_must_fail(self):
        with self.assertRaises(ValueError):
            extract(html(memory="256 GB 512 GB"), PRODUCT, SRC)

    def test_no_purchase_button(self):
        with self.assertRaises(ValueError):
            extract(html(buy="Agotado"), PRODUCT, SRC)

    def test_no_price(self):
        with self.assertRaises(ValueError):
            extract(html(prices=""), PRODUCT, SRC)


if __name__ == "__main__":
    unittest.main()
