import unittest
from unittest.mock import Mock, patch

import requests

import app as weather_app


class PixelWeatherTests(unittest.TestCase):
    def setUp(self):
        weather_app.app.config.update(TESTING=True)
        self.client = weather_app.app.test_client()

    def test_home_page_loads(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Pixel Weather", response.data)

    def test_empty_city_is_rejected_without_api_call(self):
        with patch("app.requests.get") as get:
            response = self.client.post("/weather", data={"city": "   "})
        self.assertEqual(response.status_code, 400)
        self.assertIn(b"Please enter a city name", response.data)
        get.assert_not_called()

    def test_unknown_city_shows_helpful_message(self):
        geo_response = Mock()
        geo_response.json.return_value = {"results": []}
        geo_response.raise_for_status.return_value = None
        with patch("app.requests.get", return_value=geo_response):
            response = self.client.post("/weather", data={"city": "NoSuchPlace"})
        self.assertEqual(response.status_code, 404)
        self.assertIn(b"couldn&#39;t find", response.data)

    def test_weather_page_renders_current_and_forecast_data(self):
        geo_response = Mock()
        geo_response.json.return_value = {
            "results": [{"name": "Delhi", "admin1": "Delhi", "country": "India", "latitude": 28.6, "longitude": 77.2}]
        }
        geo_response.raise_for_status.return_value = None
        forecast_response = Mock()
        forecast_response.raise_for_status.return_value = None
        forecast_response.json.return_value = {
            "current": {
                "temperature_2m": 29.4,
                "relative_humidity_2m": 42,
                "apparent_temperature": 31.1,
                "is_day": 1,
                "precipitation": 0,
                "wind_speed_10m": 8.2,
                "wind_direction_10m": 90,
                "weather_code": 0,
                "time": "2026-11-02T12:00",
            },
            "current_units": {"temperature_2m": "°C", "wind_speed_10m": "km/h"},
            "daily": {
                "time": ["2026-11-02", "2026-11-03"],
                "weather_code": [0, 61],
                "temperature_2m_max": [30.0, 27.0],
                "temperature_2m_min": [18.0, 17.0],
                "precipitation_probability_max": [0, 35],
                "sunrise": ["2026-11-02T06:30", "2026-11-03T06:31"],
                "sunset": ["2026-11-02T17:35", "2026-11-03T17:34"],
            },
        }
        with patch("app.requests.get", side_effect=[geo_response, forecast_response]) as get:
            response = self.client.post("/weather", data={"city": "Delhi"})
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Delhi", response.data)
        self.assertIn(b"29", response.data)
        self.assertIn(b"Feels like 31", response.data)
        self.assertIn(b"5-DAY FORECAST", response.data)
        self.assertEqual(get.call_count, 2)

    def test_api_timeout_is_handled(self):
        with patch("app.requests.get", side_effect=requests.Timeout):
            response = self.client.post("/weather", data={"city": "Delhi"})
        self.assertEqual(response.status_code, 504)
        self.assertIn(b"too long to respond", response.data)

    def test_weather_code_mapping_covers_thunderstorm(self):
        result = weather_app.describe_weather(99)
        self.assertEqual(result["label"], "Thunderstorm")
        self.assertEqual(result["scene"], "thunderstorm")

    def test_security_headers_are_present(self):
        response = self.client.get("/")
        self.assertEqual(response.headers["X-Content-Type-Options"], "nosniff")
        self.assertEqual(response.headers["X-Frame-Options"], "DENY")


if __name__ == "__main__":
    unittest.main()
