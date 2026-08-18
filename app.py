from flask import Flask, render_template, request
import requests
app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/weather", methods=["POST"])
def weather():
    city_name =  request.form["city"]
    geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city_name}"
    geo_response = requests.get(geo_url)
    geo_data = geo_response.json()
    city = geo_data["results"][0]
    latitude = city["latitude"]
    longitude = city["longitude"]

    weather_url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={latitude}"
        f"&longitude={longitude}"
        f"&current=temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code"
    )
    weather_response = requests.get(weather_url)
    weather_data = weather_response.json()
    temperature = weather_data["current"]["temperature_2m"]
    humidity = weather_data["current"]["relative_humidity_2m"]
    wind = weather_data["current"]["wind_speed_10m"]
    weather_code = weather_data["current"]["weather_code"]

    if weather_code == 0:
        condition = "Clear Sky"
    elif weather_code in [1, 2, 3]:
        condition = "Cloudy"
    elif weather_code in [51, 53, 55, 56, 57]:
        condition = "Drizzle"
    elif weather_code in [61, 63, 65, 66, 67]:
        condition = "Rain"
    elif weather_code in [71, 73, 75, 77]:
        condition = "Snow"
    elif weather_code in [80, 81, 82]:
        condition = "Rain Showers"
    elif weather_code == 95:
        condition = "Thunderstorm"
    else:
        condition = "Unknown"
    if weather_code == 0:
        icon = "☀️"
    elif weather_code in [1, 2, 3]:
        icon = "☁️"
    elif weather_code in [51, 53, 55, 56, 57]:
        icon = "🌦️"
    elif weather_code in [61, 63, 65, 66, 67]:
        icon = "🌧️"
    elif weather_code in [71, 73, 75, 77]:
        icon = "❄️"
    elif weather_code in [80, 81, 82]:
        icon = "🌦️"
    elif weather_code == 95:
        icon = "⛈️"
    else:
        icon = "🌤️"

    return render_template(
        "weather.html",
        city=city_name,
        temperature=temperature,
        humidity=humidity,
        wind=wind,
        condition=condition,
        icon=icon
)
app.run(debug=True)