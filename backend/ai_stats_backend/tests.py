from django.test import SimpleTestCase


class RootPageTests(SimpleTestCase):
    def test_home_page_serves_frontend_index(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "AI Statistical Analysis System")

    def test_spa_routes_fall_back_to_frontend_index(self):
        response = self.client.get("/dashboard")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "AI Statistical Analysis System")
