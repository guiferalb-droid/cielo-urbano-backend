from flask import Flask, jsonify, request
from flask_cors import CORS
from skyfield.api import load, wgs84
eph = load("de421.bsp")
sun = eph["sun"]
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
    despues = ahora + timedelta(hours=72)

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

        difference = iss - observador

        if e == 0:  # aparece
            alt, az, _ = difference.at(t).altaz()

            pase = {
                "date": hora_local.date().isoformat(),
                "start": hora_local.strftime("%H:%M"),
                "az_start": round(az.degrees)
            }

        elif e == 1:  # punto más alto
    alt, az, _ = difference.at(t).altaz()
    pase["max_altitude"] = round(alt.degrees)

    # 🌞 Altura del Sol en ese momento
    sol_alt, _, _ = (
        (sun - observador)
        .at(t)
        .altaz()
    )

    pase["sun_altitude"] = round(sol_alt.degrees, 1)


        elif e == 2:  # desaparece
            alt, az, _ = difference.at(t).altaz()

            pase["end"] = hora_local.strftime("%H:%M")
            pase["az_end"] = round(az.degrees)
            pase["visible"] = (
    		pase.get("max_altitude", 0) >= 30 and
   		pase.get("sun_altitude", 0) < -6
	    )


            pases.append(pase)



    return pases[:15]


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




