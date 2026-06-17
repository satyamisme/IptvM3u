import unittest
import json
from main import app, load_status

class TestWebAPI(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_status_endpoint(self):
        response = self.app.get('/api/status')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('loaded', data)
        self.assertIn('loading', data)
        self.assertIn('total_channels', data)

    def test_presets_saving(self):
        preset_data = {
            "name": "Custom Test Preset",
            "filters": {
                "search_term": "news",
                "nsfw": False
            }
        }
        response = self.app.post('/api/presets', 
                                 data=json.dumps(preset_data),
                                 content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data["status"], "success")
        self.assertIn("Custom Test Preset", data["presets"])

if __name__ == "__main__":
    unittest.main()
