import unittest

from clinic_api.main import app
from fastapi.testclient import TestClient


class HealthTests(unittest.TestCase):
    def test_health_endpoint(self):
        response = TestClient(app).get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})
