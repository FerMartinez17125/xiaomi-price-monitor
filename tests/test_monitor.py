import unittest
from src.monitor import amount, is_model, extract
P={"id":"xiaomi-17-512"}
S={"id":"mi-17"}
def page(name="Xiaomi 17 12GB RAM 512 GB",price="17999.00"):
    return ('<html><h1>'+name+'</h1><script type="application/ld+json">'
      '{"@type":"Product","name":"'+name+'","offers":{"@type":"Offer","price":"'+price+'",'
      '"priceCurrency":"MXN","itemCondition":"https://schema.org/NewCondition","availability":"https://schema.org/InStock"}}'
      '</script></html>')
class CheckMonitor(unittest.TestCase):
    def test_amount(self):
        self.assertEqual(amount("$20,999.00"),2099900)
        self.assertIsNone(amount("gratis"))
    def test_model(self):
        self.assertTrue(is_model("Xiaomi 17 512 GB",P))
        self.assertFalse(is_model("Xiaomi 17T Pro 512 GB",P))
    def test_quote(self):
        self.assertEqual(extract(page(),P,S)["price"],1799900)
    def test_reject_wrong_memory(self):
        with self.assertRaises(ValueError):extract(page("Xiaomi 17 256GB"),P,S)
    def test_reject_zero(self):
        with self.assertRaises(ValueError):extract(page(price="0"),P,S)
    def test_reject_used(self):
        with self.assertRaises(ValueError):extract(page("Xiaomi 17 usado 512 GB"),P,S)
if __name__=="__main__":unittest.main()
