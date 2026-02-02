from flask import Flask, jsonify, request
from flask_cors import CORS
from skyfield.api import load, wgs84
from datetime import datetime, timedelta
import pytz
from timezonefinder import TimezoneFinder


app = Flask(__name__)

# 🔓 CORS abierto para desarrollo local
CORS(app, resources={r"/*": {"origins": "*"}})
# 🛰️ Cargar datos reales de la Estación Espacial Internacional (EEI)
ts = load.timescale()
satellites = load.tle_file(
    "https://celestrak.org/NORAD/elements/stations.txt"
)
iss = [s for s in satellites if "ISS" in s.name][0]
tf = TimezoneFinder()

@app.route("/")
def home():
    return "Backend Cielo Urbano funcionando correctamente"

@app.route("/iss/next-passes", methods=["GET"])
def iss_next_passes():
    lat = request.args.get("lat")
    lon = request.args.get("lon")

    if lat is None or lon is None:
        return jsonify({"error": "lat y lon son obligatorios"}), 400

    lat = float(lat)
    lon = float(lon)

    pases = calcular_pases_iss(lat, lon)

    return jsonify({"passes": pases})

    # 🔧 DATOS GARANTIZADOS (sin cálculos astronómicos)
    # Esto evita errores 403 / 500 / Skyfield
    data = {
        "passes": [
            {
                "date": "2026-02-10",
                "start": "21:32",
                "end": "21:38",
                "max_altitude": 62,
                "visible": True,
                "azimuth": "Oeste → Este"
            },
            {
                "date": "2026-02-11",
                "start": "05:10",
                "end": "05:16",
                "max_altitude": 48,
                "visible": False,
                "azimuth": "Noroeste → Sureste"
            },
            {
                "date": "2026-02-12",
                "start": "22:05",
                "end": "22:11",
                "max_altitude": 71,
                "visible": True,
                "azimuth": "Suroeste → Noreste"
            }
        ]
    }

    return jsonify(data)

# 🚀 ARRANQUE
if __name__ == "__main__":
    import os

def calcular_pases_iss(lat, lon):
    observador = wgs84.latlon(lat, lon)

    ahora = datetime.utcnow().replace(tzinfo=pytz.utc)
    despues = ahora + timedelta(hours=24)

    t0 = ts.from_datetime(ahora)
    t1 = ts.from_datetime(despues)

    tiempos, eventos = iss.find_events(
        observador, t0, t1, altitude_degrees=10.0
    )

    pases = []
    pase = {}

    for t, e in zip(tiempos, eventos):
        hora = t.utc_datetime()
zona = tf.timezone_at(lat=lat, lng=lon)
tz = pytz.timezone(zona) if zona else pytz.utc
hora_local = hora.astimezone(tz)


        if e == 0:  # aparece
            pase = {
                "date": hora_local.date().isoformat(),
                "start": hora_local.strftime("%H:%M")

            }

        elif e == 1:  # punto más alto
            alt, az, _ = (iss - observador).at(t).altaz()
            pase["max_altitude"] = round(alt.degrees)

        elif e == 2:  # desaparece
            pase["end"] = hora.strftime("%H:%M")
            pase["visible"] = pase.get("max_altitude", 0) >= 30
            pases.append(pase)

    return pases[:5]

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)


