from flask import Flask, jsonify, request
import requests

app = Flask(__name__)

def get_city_and_country():
    city = request.args.get("city")
    country = request.args.get("country")

    if not city or not country:
        return None, None, jsonify({"error": "Debes indicar los parámetros 'city' y 'country'"}), 400

    return city, country, None, None


def get_coordinates(city,country):

    url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&countryCode={country}"

    try:
        response = requests.get(url, timeout=5)
        data = response.json()
    except Exception:
        return None, None, jsonify({"error": "Error al llamar a la API de geocoding"}), 500

    results = data.get("results")
    if not results:
        return None, None, jsonify({"error": "City not found"}), 404

    latitude = results[0].get("latitude")
    longitude = results[0].get("longitude")

    if latitude is None or longitude is None:
        return None, None, jsonify({"error": "Invalid coordinates data"}), 500

    return latitude, longitude, None, None


def get_weather(latitude, longitude):
    url = f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&hourly=temperature_2m,apparent_temperature,precipitation_probability,precipitation,wind_speed_10m"

    try:
        response = requests.get(url, timeout=5)
        data = response.json()
    except Exception:
        return None, jsonify({"error": "Error al llamar a la API de weather"}), 500

    hourly = data.get("hourly")
    if not hourly:
        return None, jsonify({"error": "Invalid weather data"}), 500

    hours = hourly.get("time", [])
    temperatures = hourly.get("temperature_2m", [])
    app_temp = hourly.get("apparent_temperature", [])
    precipitation_prob = hourly.get("precipitation_probability", [])
    precipitation = hourly.get("precipitation", [])
    wind = hourly.get("wind_speed_10m", [])

    weather_data = []

    for hour, temp, app_temp, precip_prob, precip, wind in zip(hours, temperatures, app_temp, precipitation_prob, precipitation, wind):
        weather_data.append({
            "hour": hour,
            "temperature": temp,
            "apparent_temperature": app_temp,
            "precipitation_probability": precip_prob,
            "precipitation": precip,
            "wind_speed_10m": wind
        })

    return weather_data, None, None


@app.route("/")
def home():
    return jsonify({"mensaje": "API funcionando correctamente"})


@app.route("/geolocation")
def coordinates():
    city, country, error, code = get_city_and_country()
    if error:
        return error, code

    latitude, longitude, error, code = get_coordinates(city,country)
    if error:
        return error, code

    return jsonify({
        "city": city,
        "country": country,
        "latitude": latitude,
        "longitude": longitude
        })


@app.route("/weather")
def weather():
    city, country, error, code = get_city_and_country()
    if error:
        return error, code

    latitude, longitude, error, code = get_coordinates(city,country)
    if error:
        return error, code

    weather_data, error, code = get_weather(latitude,longitude)
    if error:
        return error, code

    return jsonify({
        "city": city,
        "country": country,
        "unit": "ºC",
        "weather": weather_data
    })


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8080))  # necesario para Cloud Run
    app.run(host="0.0.0.0", port=port)
