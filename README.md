# Pixel Weather App
A pixel-art weather application that lets you search for any city and view its current weather through a dynamic pixel-art environment.

## Features
- 🌡️ Real-time temperature
- 💧 Humidity information
- 💨 Wind speed
- 🔍 Search weather by city
- ☀️ Sunny pixel-art environment
- ☁️ Cloudy pixel-art environment
- 🌦️ Drizzle effects
- 🌧️ Animated pixel rain
- ⛈️ Thunderstorm with lightning and heavy rain
- ❄️ Snow environment
- 🎨 Weather-based dynamic backgrounds

## Tech Stack
- Python
- Flask
- HTML
- CSS
- Open-Meteo API

## Design
The application uses a retro pixel-art style where the environment changes according to the current weather conditions.
Mountains, trees, clouds, rain, snow, sunlight, and lightning are represented using CSS-based pixel-art effects.

## Getting Started
1. Clone the repository
```bash
git clone https://github.com/sanchita-22/weather-app.git
cd weather-app
```

2. Install dependencies
```bash
pip install flask requests
```

3. Run the application
```bash
python app.py
```

4. Open the application
Open your browser and go to:
```http://127.0.0.1:5000```

## API
This project uses the Open-Meteo API to fetch real-time weather information.
No API key is required.

## Project Structure

```text
weather.app/
├── app.py
├── static/
├── templates/
├── screenshots/
└── .gitignore
```
