"""Pixel Weather — a small Flask app powered by the Open-Meteo APIs."""

from __future__ import annotations

import os
from datetime import datetime
from typing import Any

import requests
from flask import Flask, render_template, request

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024  # The search form only needs a tiny payload.

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
REQUEST_TIMEOUT = (3.05, 8)  # connect timeout, read timeout

WEATHER_TYPES: dict[str, dict[str, Any]] = {
    "clear": {"label": "Clear sky", "icon": "☀️", "scene": "clear"},
    "clouds": {"label": "Partly cloudy", "icon": "⛅", "scene": "clouds"},
    "overcast": {"label": "Overcast", "icon": "☁️", "scene": "clouds"},
    "fog": {"label": "Foggy", "icon": "🌫️", "scene": "fog"},
    "drizzle": {"label": "Drizzle", "icon": "🌦️", "scene": "drizzle"},
    "rain": {"label": "Rain", "icon": "🌧️", "scene": "rain"},
    "snow": {"label": "Snow", "icon": "❄️", "scene": "snow"},
    "showers": {"label": "Rain showers", "icon": "🌦️", "scene": "rain"},
    "snow-showers": {"label": "Snow showers", "icon": "🌨️", "scene": "snow"},
    "thunderstorm": {"label": "Thunderstorm", "icon": "⛈️", "scene": "thunderstorm"},
    "unknown": {"label": "Weather unavailable", "icon": "🌤️", "scene": "clouds"},
}


def describe_weather(code: int | None) -> dict[str, str]:
    """Translate a WMO weather code into display text and a pixel-scene class."""
    if code == 0:
        key = "clear"
    elif code == 1:
        key = "clouds"
    elif code in (2, 3):
        key = "overcast"
    elif code in (45, 48):
        key = "fog"
    elif code in (51, 53, 55, 56, 57):
        key = "drizzle"
    elif code in (61, 63, 65, 66, 67):
        key = "rain"
    elif code in (71, 73, 75, 77):
        key = "snow"
    elif code in (80, 81, 82):
        key = "showers"
    elif code in (85, 86):
        key = "snow-showers"
    elif code in (95, 96, 99):
        key = "thunderstorm"
    else:
        key = "unknown"
    return WEATHER_TYPES[key]


def fetch_json(url: str, params: dict[str, Any]) -> dict[str, Any]:
    """Fetch JSON from Open-Meteo and convert network/API failures into clear errors."""
    response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    data = response.json()
    if not isinstance(data, dict) or data.get("error"):
        reason = data.get("reason", "The weather service returned an unexpected response.") if isinstance(data, dict) else "Unexpected API response."
        raise ValueError(reason)
    return data


def format_clock(value: str | None) -> str:
    """Format an ISO local time from the API into a compact 12-hour clock."""
    if not value:
        return "—"
    try:
        return datetime.fromisoformat(value).strftime("%-I:%M %p")
    except (ValueError, TypeError):
        # Windows does not support %-I; this fallback is portable.
        try:
            return datetime.fromisoformat(value).strftime("%I:%M %p").lstrip("0")
        except (ValueError, TypeError):
            return "—"


@app.after_request
def add_security_headers(response):
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault("Permissions-Policy", "geolocation=(), microphone=(), camera=()")
    return response


@app.get("/")
def home():
    return render_template("index.html")


@app.post("/weather")
def weather():
    city_query = request.form.get("city", "").strip()
    if not city_query:
        return render_template("index.html", error="Please enter a city name."), 400
    if len(city_query) > 100:
        return render_template("index.html", error="City names must be 100 characters or fewer."), 400

    try:
        geo_data = fetch_json(
            GEOCODING_URL,
            {"name": city_query, "count": 1, "language": "en", "format": "json"},
        )
        results = geo_data.get("results") or []
        if not results:
            return render_template(
                "index.html",
                error=f"We couldn't find ‘{city_query}’. Check the spelling and try again.",
                city=city_query,
            ), 404

        place = results[0]
        latitude = place.get("latitude")
        longitude = place.get("longitude")
        if latitude is None or longitude is None:
            raise ValueError("The location service did not return coordinates for that city.")

        weather_data = fetch_json(
            FORECAST_URL,
            {
                "latitude": latitude,
                "longitude": longitude,
                "current": "temperature_2m,relative_humidity_2m,apparent_temperature,is_day,precipitation,wind_speed_10m,wind_direction_10m,weather_code",
                "daily": "weather_code,temperature_2m_max,temperature_2m_min,sunrise,sunset,precipitation_probability_max",
                "forecast_days": 5,
                "timezone": "auto",
            },
        )

        current = weather_data.get("current") or {}
        daily = weather_data.get("daily") or {}
        if "temperature_2m" not in current or "weather_code" not in current:
            raise ValueError("Current weather data is temporarily unavailable.")

        condition = describe_weather(current.get("weather_code"))
        forecast = []
        dates = daily.get("time", [])
        for index, day in enumerate(dates):
            day_code = value_at(daily, "weather_code", index)
            day_condition = describe_weather(day_code)
            forecast.append({
                "date": datetime.fromisoformat(day).strftime("%a, %b %d"),
                "high": value_at(daily, "temperature_2m_max", index),
                "low": value_at(daily, "temperature_2m_min", index),
                "rain_chance": value_at(daily, "precipitation_probability_max", index),
                "icon": day_condition["icon"],
                "condition": day_condition["label"],
            })

        location_parts = [place.get("name"), place.get("admin1"), place.get("country")]
        location_label = ", ".join(dict.fromkeys(part for part in location_parts if part))
        return render_template(
            "weather.html",
            city=place.get("name", city_query),
            location_label=location_label,
            temperature=round(current["temperature_2m"]),
            feels_like=round(current.get("apparent_temperature", current["temperature_2m"])),
            humidity=current.get("relative_humidity_2m", "—"),
            wind=current.get("wind_speed_10m", "—"),
            wind_direction=current.get("wind_direction_10m"),
            precipitation=current.get("precipitation", "—"),
            condition=condition["label"],
            icon=condition["icon"],
            scene_class=condition["scene"],
            is_day=bool(current.get("is_day", 1)),
            sunrise=format_clock(value_at(daily, "sunrise", 0)),
            sunset=format_clock(value_at(daily, "sunset", 0)),
            forecast=forecast,
            updated_at=current.get("time", ""),
            temperature_unit=weather_data.get("current_units", {}).get("temperature_2m", "°C"),
            wind_unit=weather_data.get("current_units", {}).get("wind_speed_10m", "km/h"),
        )
    except requests.Timeout:
        return render_template("index.html", error="The weather service took too long to respond. Please try again."), 504
    except requests.RequestException:
        app.logger.exception("Open-Meteo request failed")
        return render_template("index.html", error="Couldn't reach the weather service. Check your connection and try again."), 502
    except (ValueError, KeyError, TypeError):
        app.logger.exception("Unexpected weather response")
        return render_template("index.html", error="Weather data is temporarily unavailable. Please try again."), 502


def value_at(data: dict[str, Any], key: str, index: int):
    values = data.get(key) or []
    return values[index] if index < len(values) else None


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="127.0.0.1", port=port, debug=False)
