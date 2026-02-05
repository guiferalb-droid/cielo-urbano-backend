from flask import Flask, jsonify, request
from flask_cors import CORS
from skyfield.api import load, wgs84
from datetime import datetime, timedelta
import pytz
from timezonefinder import TimezoneFinder
import os

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# 🛰️ Cargar datos reales de la EEI
ts = load.timescale()
satellites = load.tle_file(
    "https://celestrak.org/NORAD/elements/stations.txt"
)
iss = [s for s in satellites if "ISS" in s.name][0]
tf = TimezoneFinder()


@app.route("/")
def home():
    return "Backend Cielo Urbano funcionando correctamente"


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

    zona = tf.timezone_at(lat=lat, lng=lon)
    tz = pytz.timezone(zona) if zona else pytz.utc

    for t, e in zip(tiempos, eventos):
        hora_utc = t.utc_datetime()
        hora_local = hora_utc.astimezone(tz)

        if e == 0:  # aparece
            pase = {
                "date": hora_local.date().isoformat(),
                "start": hora_local.strftime("%H:%M")
            }

        elif e == 1:  # punto más alto
            alt, az, _ = (iss - observador).at(t).altaz()
            pase["max_altitude"] = round(alt.degrees)

        elif e == 2:  # desaparece
            pase["end"] = hora_local.strftime("%H:%M")
            pase["visible"] = pase.get("max_altitude", 0) >= 30
            pases.append(pase)

    return pases[:10]


@app.route("/iss/next-passes", methods=["GET"])
def iss_next_passes():
    lat = request.args.get("lat")
    lon = request.args.get("lon")

    if lat is None or lon is None:
        return jsonify({"error": "lat y lon son obligatorios"}), 400

    pases = calcular_pases_iss(float(lat), float(lon))
    return jsonify({"passes": pases})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

# Azimut al inicio del pase
alt_start, az_start, _ = difference.at(t_start).altaz()

# Azimut al final del pase
alt_end, az_end, _ = difference.at(t_end).altaz()

# Tomamos un punto ligeramente después del inicio
t_appear = t_start + 10 / 86400   # +10 segundos

# Y un punto ligeramente antes del final
t_disappear = t_end - 10 / 86400  # -10 segundos

alt_a, az_a, _ = difference.at(t_appear).altaz()
alt_d, az_d, _ = difference.at(t_disappear).altaz()


