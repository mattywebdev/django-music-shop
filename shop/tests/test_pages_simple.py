from django.test import TestCase, Client

class SimplePagesTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_landing_and_about(self):
        self.assertEqual(self.client.get("/").status_code, 200)
        self.assertEqual(self.client.get("/about/").status_code, 200)
