import json
import math
import os
from datetime import datetime, timedelta

import requests
from flask import Flask, flash, jsonify, redirect, render_template, request, url_for
from flask_login import LoginManager, UserMixin, current_user, login_required, login_user, logout_user
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import validates
from werkzeug.security import check_password_hash, generate_password_hash

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
secret_key = os.environ.get("SECRET_KEY")
if not secret_key:
    raise RuntimeError("The SECRET_KEY environment variable must be set.")
app.config["SECRET_KEY"] = secret_key
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL",
    f"sqlite:///{os.path.join(basedir, 'instance', 'disasterguard.db')}",
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["MONGODB_URI"] = os.environ.get("MONGODB_URI", "").strip()
app.config["MONGODB_DATABASE"] = os.environ.get("MONGODB_DATABASE", "disasterguard")


db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"
mongo_client = None
mongo_client_uri = None


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default="registered_user")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, default=datetime.utcnow)

    @validates("username")
    def validate_username(self, key, value):
        return value.strip()

    @validates("email")
    def validate_email(self, key, value):
        return value.strip().lower()

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.before_request
def ensure_initialized():
    if not hasattr(app, "_db_ready"):
        with app.app_context():
            if app.config["SQLALCHEMY_DATABASE_URI"].startswith("sqlite:"):
                os.makedirs(os.path.join(basedir, "instance"), exist_ok=True)
            db.create_all()
            admin = User.query.filter_by(username="admin", role="administrator").first()
            if admin and admin.check_password("admin123"):
                db.session.delete(admin)
                db.session.commit()
        app._db_ready = True


def weather_code_to_text(code):
    codes = {
        0: "Clear sky",
        1: "Mostly clear",
        2: "Partly cloudy",
        3: "Overcast",
        45: "Fog",
        48: "Depositing rime fog",
        51: "Light drizzle",
        53: "Moderate drizzle",
        55: "Dense drizzle",
        61: "Slight rain",
        63: "Moderate rain",
        65: "Heavy rain",
        71: "Slight snow",
        73: "Moderate snow",
        75: "Heavy snow",
        80: "Rain showers",
        81: "Heavy showers",
        82: "Violent showers",
        95: "Thunderstorm",
        96: "Thunderstorm with hail",
        99: "Severe thunderstorm",
    }
    return codes.get(code, "Variable conditions")


def build_demo_weather(location_name="Dhaka, Bangladesh"):
    return {
        "source": "demo-mode",
        "status": "Demo mode active",
        "location": location_name,
        "last_updated": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
        "current": {
            "temperature": 29.4,
            "humidity": 83,
            "rainfall": 14.8,
            "wind_speed": 18.7,
            "wind_direction": 135,
            "pressure": 1007,
            "condition": "Heavy rain shower",
            "weather_code": 80,
        },
        "hourly": [
            {"time": "Now", "temp": 29.4, "rain": 42, "precipitation": 1.4},
            {"time": "+1h", "temp": 29.8, "rain": 48, "precipitation": 2.1},
            {"time": "+2h", "temp": 30.1, "rain": 57, "precipitation": 2.8},
            {"time": "+3h", "temp": 29.7, "rain": 61, "precipitation": 3.2},
            {"time": "+4h", "temp": 28.9, "rain": 55, "precipitation": 2.4},
            {"time": "+5h", "temp": 28.6, "rain": 43, "precipitation": 1.2},
        ],
        "daily": [
            {"day": "Mon", "max": 31, "min": 26, "rain": 58},
            {"day": "Tue", "max": 32, "min": 27, "rain": 70},
            {"day": "Wed", "max": 30, "min": 25, "rain": 64},
        ],
        "alert": "Demo weather feed is active until a live API is connected.",
    }


@app.route("/")
def index():
    return render_template("landing.html", page_title="AI DisasterGuard")


@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html", page_title="Disaster Dashboard")


@app.route("/modules/<slug>")
@login_required
def module_page(slug):
    modules = {
        "ai-predictions": {
            "title": "AI Predictions",
            "eyebrow": "Multi-hazard intelligence",
            "description": "Review the latest hazard assessments and explore the demo prediction workflows. No trained production model is configured in this environment.",
            "metrics": [("Hazard modules", "3"), ("High-risk demo areas", "2"), ("Forecast horizon", "72 hours")],
            "items": [("Flood", "High", "Sylhet basin", "Rainfall and river-stage indicators"), ("Cyclone", "Moderate", "Bay of Bengal coast", "Forecast track and coastal exposure"), ("Landslide", "Moderate", "Chattogram Hill Tracts", "Rainfall and terrain susceptibility")],
            "mode": "Demo assessments",
        },
        "flood-prediction": {
            "title": "Flood Prediction",
            "eyebrow": "Hydrological risk",
            "description": "Submit rainfall, river, and terrain indicators for a transparent demo estimate. This is not an official warning or trained model output.",
            "metrics": [("Forecast horizon", "72 hours"), ("Inputs", "7 indicators"), ("Model status", "Demo mode")],
            "items": [("Rainfall intensity", "58 mm/h", "Sylhet", "Elevated"), ("River level", "64%", "Jamuna basin", "Rising"), ("Soil moisture", "74%", "Low-lying areas", "Saturated")],
            "mode": "Run flood estimate",
            "prediction": "flood",
            "fields": [("rainfall_intensity", "Rainfall intensity (mm/h)", "58"), ("rainfall_accumulation", "Rainfall accumulation (mm)", "126"), ("river_water_level", "River water level (%)", "64"), ("soil_moisture", "Soil moisture (%)", "74"), ("elevation", "Elevation (m)", "19"), ("slope", "Slope (degrees)", "23"), ("historical_flood_events", "Historical flood events", "3")],
        },
        "cyclone-prediction": {
            "title": "Cyclone Prediction",
            "eyebrow": "Coastal hazard outlook",
            "description": "Review a clearly labeled sample impact assessment. Check official meteorological advisories before making response decisions.",
            "metrics": [("Track status", "Demo scenario"), ("Coastal exposure", "Elevated"), ("Official feed", "Not connected")],
            "items": [("Wind exposure", "High", "Cox's Bazar", "Demo scenario: strong coastal winds"), ("Coastal surge", "Moderate", "Chattogram coast", "Demo scenario: monitor official bulletins"), ("Track confidence", "Unavailable", "Bay of Bengal", "No live cyclone track is connected")],
            "mode": "Demo assessment",
            "prediction": "cyclone",
            "fields": [("wind_speed", "Wind speed (km/h)", "85"), ("pressure", "Atmospheric pressure (hPa)", "990"), ("rainfall", "Rainfall (mm)", "80"), ("coast_distance", "Distance from coast (km)", "35")],
        },
        "landslide-prediction": {
            "title": "Landslide Prediction",
            "eyebrow": "Terrain susceptibility",
            "description": "Review a transparent demo susceptibility estimate based on rainfall and terrain conditions. It is not a validated operational prediction.",
            "metrics": [("Terrain zones", "24"), ("Rain trigger", "Elevated"), ("Model status", "Demo mode")],
            "items": [("Slope exposure", "High", "Chattogram Hill Tracts", "Demo scenario: steep terrain"), ("Rainfall trigger", "Moderate", "Bandarban", "Review local rainfall observations"), ("Historical susceptibility", "Moderate", "Rangamati", "Historical context is illustrative")],
            "mode": "Demo assessment",
            "prediction": "landslide",
            "fields": [("rainfall", "Rainfall (mm/24h)", "90"), ("slope", "Slope angle (degrees)", "38"), ("elevation", "Elevation (m)", "420"), ("soil_moisture", "Soil moisture (%)", "72")],
        },
        "weather-prediction": {
            "title": "Weather Prediction",
            "eyebrow": "Local weather outlook",
            "description": "Check current conditions and short-term forecasts from Open-Meteo when available. Choose a place on the Weather Monitoring page.",
            "metrics": [("Weather provider", "Open-Meteo"), ("Forecast", "Hourly + daily"), ("Current location", "Selected place")],
            "items": [("Current conditions", "Live when available", "Selected location", "See temperature, wind, rain, and pressure"), ("Hourly outlook", "Next 6 hours", "Selected location", "Forecast probabilities"), ("Daily outlook", "3 days", "Selected location", "Daily temperature and precipitation")],
            "mode": "Open weather monitor",
            "link": url_for("weather"),
        },
        "early-warning-center": {
            "title": "Early Warning Center",
            "eyebrow": "Alerts and advisories",
            "description": "Review the available sample alert feed. These examples are for interface demonstration and are not official emergency notifications.",
            "metrics": [("Active feed items", "3"), ("Official connection", "Not connected"), ("Delivery status", "Demo only")],
            "items": [("Cyclone watch for coastal districts", "High", "Coastal districts", "15 min ago"), ("River level rising near Jamuna basin", "Moderate", "Jamuna basin", "42 min ago"), ("Heavy rainfall advisory in hill tracts", "Warning", "Hill tracts", "1 hr ago")],
            "mode": "Demo alert feed",
        },
        "emergency-response": {
            "title": "Emergency Response",
            "eyebrow": "Incident coordination",
            "description": "Track illustrative incident assignments and response readiness. Dispatch actions are not connected to emergency services.",
            "metrics": [("Incidents under review", "9"), ("Response teams", "12 demo units"), ("Dispatch link", "Not connected")],
            "items": [("Flood readiness check", "In review", "Sylhet", "Verify shelters and supplies"), ("Coastal watch", "Standby", "Cox's Bazar", "Await official advisory"), ("Slope inspection", "Planned", "Khagrachhari", "Coordinate local assessment")],
            "mode": "Demo coordination",
        },
        "evacuation-planning": {
            "title": "Evacuation Planning",
            "eyebrow": "Community readiness",
            "description": "View illustrative monitored locations and preparedness priorities. Routes and shelter information require local authority verification.",
            "metrics": [("Monitored locations", "112"), ("Priority zones", "6"), ("Verified routes", "Not connected")],
            "items": [("Sunamganj", "Critical", "Flood exposure", "Verify nearest designated shelter"), ("Cox's Bazar", "High", "Coastal exposure", "Follow official evacuation instructions"), ("Khagrachhari", "Moderate", "Slope exposure", "Review locally approved safe routes")],
            "mode": "Demo planning data",
        },
        "analytics-reports": {
            "title": "Analytics & Reports",
            "eyebrow": "System performance",
            "description": "Summary metrics shown here are sample development data, not a validated historical record.",
            "metrics": [("Data availability", "98% demo"), ("Stations reporting", "94% demo"), ("Incidents shown", "9 demo")],
            "items": [("Rainfall trend", "Demo series", "Last 6 months", "Sample chart data"), ("Hazard mix", "Demo series", "Flood / cyclone / landslide", "Sample chart data"), ("Prediction history", "Illustrative", "Not validated", "No trained model history available")],
            "mode": "Demo analytics",
        },
        "disaster-risk-map": {
            "title": "Disaster Risk Map",
            "eyebrow": "GIS overview",
            "description": "Explore illustrative hazard locations on the map. Risk markers are sample data and are not official alerts.",
            "metrics": [("Mapped locations", "3 demo"), ("Map provider", "OpenStreetMap"), ("Risk layer", "Illustrative")],
            "items": [("Sunamganj", "Critical", "25.07, 91.40", "Illustrative flood risk"), ("Cox's Bazar", "High", "21.42, 91.98", "Illustrative coastal risk"), ("Khagrachhari", "Moderate", "23.10, 91.97", "Illustrative slope risk")],
            "mode": "Open interactive map",
            "link": url_for("map_page"),
        },
    }
    module = modules.get(slug)
    if module is None:
        return redirect(url_for("dashboard"))
    return render_template("module.html", page_title=module["title"], module=module)


@app.route("/weather")
def weather():
    return render_template("weather.html", page_title="Weather Monitoring")


@app.route("/map")
def map_page():
    return render_template("map.html", page_title="Risk Map")


@app.route("/admin")
@login_required
def admin_panel():
    if current_user.role != "administrator":
        flash("Administrator access required.", "error")
        return redirect(url_for("dashboard"))
    return render_template("admin.html", page_title="Administration")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        identifier = request.form.get("identifier", "").strip()
        password = request.form.get("password", "")
        user = User.query.filter((User.username == identifier) | (User.email == identifier)).first()

        if user and user.check_password(password):
            login_user(user)
            user.last_login = datetime.utcnow()
            db.session.commit()
            flash("Welcome back!", "success")
            return redirect(url_for("dashboard"))

        flash("Invalid username/email or password.", "error")

    return render_template("login.html", page_title="Login")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not username or not email or not password:
            flash("All fields are required.", "error")
            return render_template("register.html", page_title="Register")

        if User.query.filter((User.username == username) | (User.email == email)).first():
            flash("A user with that username or email already exists.", "error")
            return render_template("register.html", page_title="Register")

        if len(password) < 8:
            flash("Password must be at least 8 characters long.", "error")
            return render_template("register.html", page_title="Register")

        user = User(username=username, email=email, role="registered_user")
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        flash("Registration successful.", "success")
        return redirect(url_for("dashboard"))

    return render_template("register.html", page_title="Register")


@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        user = User.query.filter_by(email=email).first()
        if user:
            flash("Password reset instructions have been sent to your email.", "success")
        else:
            flash("No account matched that email address.", "error")
        return redirect(url_for("login"))

    return render_template("forgot_password.html", page_title="Reset Password")


@app.route("/profile")
@login_required
def profile():
    return render_template("profile.html", page_title="Profile")


@app.route("/logout")
def logout():
    logout_user()
    flash("You have been logged out.", "success")
    return redirect(url_for("index"))


@app.route("/api/dashboard-summary")
def dashboard_summary():
    alerts = [
        {"title": "Cyclone watch for coastal districts", "hazard": "Cyclone", "severity": "High", "time": "15 min ago"},
        {"title": "River level rising near Jamuna basin", "hazard": "Flood", "severity": "Moderate", "time": "42 min ago"},
        {"title": "Heavy rainfall advisory in hill tracts", "hazard": "Weather", "severity": "Warning", "time": "1 hr ago"},
    ]
    risk_locations = [
        {"name": "Sunamganj", "risk": "Critical", "lat": 25.07, "lng": 91.4},
        {"name": "Cox's Bazar", "risk": "High", "lat": 21.42, "lng": 91.98},
        {"name": "Khagrachhari", "risk": "Moderate", "lat": 23.1, "lng": 91.97},
    ]
    recent_events = [
        {"event": "Flash flood alert", "time": "08:20"},
        {"event": "Heat hazard review", "time": "07:40"},
        {"event": "Coastal wind advisory", "time": "06:10"},
    ]
    return jsonify({
        "data_source": "Demo dashboard records; weather is loaded from Open-Meteo when available",
        "status": "Demo data",
        "cards": [
            {"label": "Active demo alerts", "value": str(len(alerts)), "tone": "danger"},
            {"label": "High-risk demo areas", "value": str(sum(location["risk"] in {"High", "Critical"} for location in risk_locations)), "tone": "warning"},
            {"label": "Mapped demo locations", "value": str(len(risk_locations)), "tone": "info"},
            {"label": "Weather feed status", "value": "Checking", "tone": "success"},
            {"label": "Recent demo events", "value": str(len(recent_events)), "tone": "neutral"},
            {"label": "Weather data source", "value": "Checking", "tone": "success"},
        ],
        "alerts": alerts,
        "risk_locations": risk_locations,
        "recent_events": recent_events,
    })


@app.route("/api/weather-data")
def weather_data():
    lat = request.args.get("lat", "23.8103")
    lon = request.args.get("lon", "90.4125")
    location_name = request.args.get("location_name", "Dhaka, Bangladesh").strip() or "Selected location"
    try:
        response = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat,
                "longitude": lon,
                "current": "temperature_2m,relative_humidity_2m,precipitation,rain,wind_speed_10m,wind_direction_10m,pressure_msl,weather_code",
                "hourly": "temperature_2m,precipitation_probability,precipitation",
                "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
                "timezone": "auto",
                "forecast_days": 3,
            },
            timeout=10,
        )

        if response.ok:
            data = response.json()
            current = data.get("current", {})
            hourly = data.get("hourly", {})
            daily = data.get("daily", {})
            all_hourly_times = hourly.get("time", [])
            forecast_start = next(
                (index for index, value in enumerate(all_hourly_times) if value >= current.get("time", "")),
                0,
            )
            hourly_times = all_hourly_times[forecast_start:forecast_start + 12]
            hourly_temperatures = hourly.get("temperature_2m", [])[forecast_start:forecast_start + 12]
            hourly_probabilities = hourly.get("precipitation_probability", [])[forecast_start:forecast_start + 12]
            hourly_precipitation = hourly.get("precipitation", [])[forecast_start:forecast_start + 12]
            daily_times = daily.get("time", [])[:3]
            daily_maximums = daily.get("temperature_2m_max", [])[:3]
            daily_minimums = daily.get("temperature_2m_min", [])[:3]
            daily_precipitation = daily.get("precipitation_sum", [])[:3]
            return jsonify({
                "source": "Open-Meteo",
                "status": "Live",
                "location": location_name,
                "last_updated": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
                "current": {
                    "temperature": current.get("temperature_2m"),
                    "humidity": current.get("relative_humidity_2m"),
                    "rainfall": current.get("rain"),
                    "wind_speed": current.get("wind_speed_10m"),
                    "wind_direction": current.get("wind_direction_10m"),
                    "pressure": current.get("pressure_msl"),
                    "condition": weather_code_to_text(current.get("weather_code", 0)),
                },
                "hourly": [
                    {
                        "time": item_time,
                        "temp": temperature,
                        "rain": probability,
                        "precipitation": precipitation,
                    }
                    for item_time, temperature, probability, precipitation in zip(
                        hourly_times, hourly_temperatures, hourly_probabilities, hourly_precipitation
                    )
                ],
                "daily": [
                    {"day": day, "max": maximum, "min": minimum, "rain": precipitation}
                    for day, maximum, minimum, precipitation in zip(
                        daily_times, daily_maximums, daily_minimums, daily_precipitation
                    )
                ],
            })
    except requests.RequestException:
        pass

    return jsonify(build_demo_weather(location_name))


def normalized_risk_score(indicators):
    available_weight = sum(weight for value, weight in indicators if value is not None)
    if not available_weight:
        raise ValueError("The live forecast did not include enough data to estimate risk.")
    score = sum(
        min(100, max(0, value)) * weight
        for value, weight in indicators
        if value is not None
    ) / available_weight
    return round(score, 1)


def fetch_elevation_slope(latitude, longitude):
    points = [
        (latitude, longitude),
        (latitude + 0.001, longitude),
        (latitude - 0.001, longitude),
        (latitude, longitude + 0.001),
        (latitude, longitude - 0.001),
    ]
    response = requests.get(
        "https://api.open-meteo.com/v1/elevation",
        params={
            "latitude": ",".join(str(point[0]) for point in points),
            "longitude": ",".join(str(point[1]) for point in points),
        },
        timeout=10,
    )
    response.raise_for_status()
    elevations = response.json().get("elevation", [])
    if len(elevations) != len(points) or any(value is None for value in elevations):
        raise ValueError("Terrain elevation data is unavailable for this location.")

    center = elevations[0]
    slopes = []
    for (neighbor_latitude, neighbor_longitude), elevation in zip(points[1:], elevations[1:]):
        latitude_distance = math.radians(neighbor_latitude - latitude) * 6371000
        longitude_distance = math.radians(neighbor_longitude - longitude) * 6371000 * math.cos(math.radians(latitude))
        distance = math.hypot(latitude_distance, longitude_distance)
        if distance:
            slopes.append(abs(elevation - center) / distance)
    if not slopes:
        raise ValueError("Terrain slope could not be calculated for this location.")
    return center, math.degrees(math.atan(max(slopes)))


def save_location_prediction(prediction):
    global mongo_client, mongo_client_uri

    uri = app.config["MONGODB_URI"]
    if not uri:
        return "not_configured"

    try:
        if mongo_client is None or mongo_client_uri != uri:
            if mongo_client is not None:
                mongo_client.close()
            mongo_client = MongoClient(
                uri,
                appname="AI DisasterGuard",
                connectTimeoutMS=5000,
                serverSelectionTimeoutMS=5000,
            )
            mongo_client_uri = uri

        mongo_client.admin.command("ping")
        collection = mongo_client[app.config["MONGODB_DATABASE"]]["location_predictions"]
        collection.create_index("expires_at", expireAfterSeconds=0)
        now = datetime.utcnow()
        document = {
            "location": prediction["location"],
            "latitude": prediction["latitude"],
            "longitude": prediction["longitude"],
            "source": prediction["source"],
            "forecast_time": prediction["forecast_time"],
            "risk_indices": prediction["risks"],
            "created_at": now,
            "expires_at": now + timedelta(days=90),
        }
        collection.insert_one(document)
        return "saved"
    except PyMongoError:
        app.logger.exception("Could not save live location prediction to MongoDB.")
        return "unavailable"


@app.route("/api/predict/location", methods=["POST"])
def location_prediction():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"error": "Provide a JSON object with a location and coordinates."}), 400

    try:
        latitude = float(payload.get("latitude"))
        longitude = float(payload.get("longitude"))
    except (TypeError, ValueError):
        return jsonify({"error": "Enter valid latitude and longitude coordinates."}), 400

    if not math.isfinite(latitude) or not math.isfinite(longitude):
        return jsonify({"error": "Coordinates must be finite numbers."}), 400
    if not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
        return jsonify({"error": "Coordinates are outside the valid range."}), 400

    location = str(payload.get("location", "Selected location")).strip()[:120] or "Selected location"
    try:
        weather_response = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": latitude,
                "longitude": longitude,
                "current": "precipitation,rain,pressure_msl,wind_speed_10m",
                "hourly": "precipitation,precipitation_probability,soil_moisture_0_to_7cm",
                "forecast_days": 2,
                "timezone": "UTC",
            },
            timeout=12,
        )
        weather_response.raise_for_status()
        weather = weather_response.json()
        current = weather.get("current", {})
        hourly = weather.get("hourly", {})
        forecast_start = next(
            (
                index for index, value in enumerate(hourly.get("time", []))
                if value >= current.get("time", "")
            ),
            0,
        )
        precipitation = hourly.get("precipitation", [])[forecast_start:forecast_start + 24]
        probabilities = hourly.get("precipitation_probability", [])[forecast_start:forecast_start + 24]
        soil_values = hourly.get("soil_moisture_0_to_7cm", [])[forecast_start:forecast_start + 24]
        rainfall_24h = sum(value for value in precipitation if value is not None)
        peak_rain_probability = max((value for value in probabilities if value is not None), default=None)
        soil_moisture = next((value for value in soil_values if value is not None), None)
        if soil_moisture is not None:
            soil_moisture = soil_moisture * 100

        elevation, slope_degrees = fetch_elevation_slope(latitude, longitude)
    except (requests.RequestException, ValueError, KeyError, TypeError) as error:
        app.logger.warning("Live location prediction unavailable: %s", error)
        return jsonify({
            "error": "Could not retrieve live weather and terrain data for this location. Please try again.",
        }), 502

    try:
        current_rainfall = current.get("rain")
        flood_risk = normalized_risk_score([
            (min(rainfall_24h / 120 * 100, 100), 35),
            (min(current_rainfall / 20 * 100, 100) if current_rainfall is not None else None, 15),
            (peak_rain_probability, 25),
            (soil_moisture, 25),
        ])
        landslide_risk = normalized_risk_score([
            (min(rainfall_24h / 120 * 100, 100), 35),
            (min(current_rainfall / 20 * 100, 100) if current_rainfall is not None else None, 15),
            (peak_rain_probability, 15),
            (soil_moisture, 20),
            (min(slope_degrees / 45 * 100, 100), 15),
        ])
    except (TypeError, ValueError, ZeroDivisionError) as error:
        app.logger.warning("Live location risk indicators are incomplete: %s", error)
        return jsonify({"error": "The live data source did not return enough valid indicators for a risk estimate."}), 502

    def risk_category(score):
        if score >= 75:
            return "Very high"
        if score >= 50:
            return "High"
        if score >= 25:
            return "Moderate"
        return "Low"

    prediction = {
        "location": location,
        "latitude": latitude,
        "longitude": longitude,
        "source": "Open-Meteo forecast and elevation data",
        "forecast_time": weather.get("current", {}).get("time"),
        "forecast_horizon": "Next 24 hours",
        "risks": [
            {
                "hazard": "Flood",
                "risk_index_percent": flood_risk,
                "category": risk_category(flood_risk),
                "factors": [
                    f"{rainfall_24h:.1f} mm forecast precipitation in 24 hours",
                    f"Peak precipitation probability: {peak_rain_probability}%" if peak_rain_probability is not None else "Precipitation probability unavailable",
                    f"Soil moisture: {soil_moisture:.1f}%" if soil_moisture is not None else "Soil moisture unavailable",
                ],
            },
            {
                "hazard": "Landslide",
                "risk_index_percent": landslide_risk,
                "category": risk_category(landslide_risk),
                "factors": [
                    f"{rainfall_24h:.1f} mm forecast precipitation in 24 hours",
                    f"Estimated local terrain slope: {slope_degrees:.1f}°",
                    f"Soil moisture: {soil_moisture:.1f}%" if soil_moisture is not None else "Soil moisture unavailable",
                ],
            },
        ],
        "disclaimer": "These transparent weather-and-terrain risk indices are not calibrated disaster probabilities, a trained AI model, or official warnings. Check local emergency and meteorological authorities.",
    }
    prediction["database"] = {
        "provider": "MongoDB Atlas",
        "status": save_location_prediction(prediction),
    }
    return jsonify(prediction)


@app.route("/api/predict/flood", methods=["POST"])
def flood_prediction():
    payload = request.get_json(silent=True) or {}
    rainfall_intensity = float(payload.get("rainfall_intensity", 0) or 0)
    rainfall_accumulation = float(payload.get("rainfall_accumulation", 0) or 0)
    river_water_level = float(payload.get("river_water_level", 0) or 0)
    soil_moisture = float(payload.get("soil_moisture", 0) or 0)
    elevation = float(payload.get("elevation", 0) or 0)
    slope = float(payload.get("slope", 0) or 0)
    historical_flood_events = float(payload.get("historical_flood_events", 0) or 0)

    score = (
        rainfall_intensity * 0.2
        + rainfall_accumulation * 0.18
        + river_water_level * 0.2
        + soil_moisture * 0.15
        + (100 - elevation) * 0.08
        + slope * 0.09
        + historical_flood_events * 0.1
    )
    probability = max(0, min(100, round(score, 1)))
    if probability >= 75:
        risk_category = "Critical"
    elif probability >= 50:
        risk_category = "High"
    elif probability >= 30:
        risk_category = "Moderate"
    else:
        risk_category = "Low"

    contributing_factors = []
    if rainfall_intensity > 45:
        contributing_factors.append("High rainfall intensity")
    if river_water_level > 55:
        contributing_factors.append("Elevated river stage")
    if soil_moisture > 60:
        contributing_factors.append("Saturated soil")
    if historical_flood_events > 2:
        contributing_factors.append("Prior flood history")

    if not contributing_factors:
        contributing_factors = ["Baseline hydrological conditions"]

    return jsonify({
        "demo_mode": True,
        "model_version": "demo-flood-xgboost-v1",
        "forecast_horizon": "72 hours",
        "prediction_timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
        "flood_probability": probability,
        "risk_category": risk_category,
        "risk_explanation": "This demo prediction uses a transparent heuristic model and is displayed in demo mode because no trained production model is available for the live environment.",
        "contributing_factors": contributing_factors,
        "status": "Demo mode active"
    })


@app.route("/api/predict/<hazard>", methods=["POST"])
def hazard_prediction(hazard):
    if hazard == "flood":
        return flood_prediction()
    if hazard not in {"cyclone", "landslide"}:
        return jsonify({"error": "Unsupported prediction type."}), 404

    payload = request.get_json(silent=True) or {}
    try:
        values = {key: float(value) for key, value in payload.items()}
    except (TypeError, ValueError):
        return jsonify({"error": "Prediction inputs must be numeric."}), 400

    if hazard == "cyclone":
        wind = values.get("wind_speed", 0)
        pressure = values.get("pressure", 1013)
        rainfall = values.get("rainfall", 0)
        coast_distance = values.get("coast_distance", 100)
        score = (wind / 150 * 40) + ((1013 - pressure) / 60 * 20) + (rainfall / 200 * 20) + ((100 - coast_distance) / 100 * 20)
        factors = []
        if wind >= 75:
            factors.append("Elevated wind speed")
        if pressure < 1000:
            factors.append("Low atmospheric pressure")
        if coast_distance < 50:
            factors.append("Coastal proximity")
        if rainfall >= 75:
            factors.append("Heavy rainfall")
        label = "Cyclone local impact estimate"
    else:
        rainfall = values.get("rainfall", 0)
        slope = values.get("slope", 0)
        elevation = values.get("elevation", 0)
        soil_moisture = values.get("soil_moisture", 0)
        score = (rainfall / 200 * 30) + (slope / 60 * 40) + (soil_moisture / 100 * 20) + (min(elevation, 1000) / 1000 * 10)
        factors = []
        if rainfall >= 75:
            factors.append("High recent rainfall")
        if slope >= 30:
            factors.append("Steep slope")
        if soil_moisture >= 65:
            factors.append("High soil moisture")
        label = "Landslide susceptibility estimate"

    probability = round(max(0, min(100, score)), 1)
    risk_category = "Critical" if probability >= 75 else "High" if probability >= 50 else "Moderate" if probability >= 30 else "Low"
    if not factors:
        factors.append("No elevated demo indicators")
    return jsonify({
        "demo_mode": True,
        "model_version": f"demo-{hazard}-heuristic-v1",
        "forecast_horizon": "72 hours",
        "prediction_timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
        "flood_probability": probability,
        "risk_category": risk_category,
        "risk_explanation": f"{label} calculated with a transparent heuristic for demonstration only. No trained operational model is connected.",
        "contributing_factors": factors,
        "status": "Demo mode",
    })


@app.route("/api/alerts")
def alerts():
    return jsonify({
        "items": [
            {"type": "Flood", "location": "Sylhet", "status": "Watch", "time": "09:25"},
            {"type": "Cyclone", "location": "Cox's Bazar", "status": "Warning", "time": "09:00"},
            {"type": "Landslide", "location": "Khagrachhari", "status": "Alert", "time": "08:10"},
        ]
    })


@app.route("/api/notifications")
def notifications():
    return jsonify({
        "items": [
            {"id": "cyclone-watch", "title": "Cyclone watch for coastal districts", "severity": "High", "time": "15 min ago", "location": "Coastal districts"},
            {"id": "jamuna-river", "title": "River level rising near Jamuna basin", "severity": "Moderate", "time": "42 min ago", "location": "Jamuna basin"},
            {"id": "hill-rainfall", "title": "Heavy rainfall advisory in hill tracts", "severity": "Warning", "time": "1 hr ago", "location": "Hill tracts"},
        ],
        "demo_mode": True,
    })


@app.route("/api/system-health")
def system_health():
    return jsonify({
        "stations": 94,
        "api_latency": 220,
        "uptime": "99.7%",
        "active_services": ["Weather API", "Risk engine", "Map services", "Alerting queue"],
    })


@app.context_processor
def inject_context():
    return {
        "site_name": "AI DisasterGuard",
        "current_year": datetime.utcnow().year,
        "current_user": current_user,
    }


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
