from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from pathlib import Path
from datetime import datetime, timedelta, timezone
import sqlite3, json, os

BASE = Path(__file__).resolve().parent
DB_PATH = BASE / "ecoacuario.db"
FRONTEND = BASE.parent / "frontend"

app = Flask(__name__, static_folder=str(FRONTEND), static_url_path="")
CORS(app)

DEFAULT_CONFIG = {
    "ph_min": 6.5, "ph_max": 7.5,
    "temp_min": 22.0, "temp_max": 26.0,
    "heater_on": 23.0, "heater_off": 25.0,
    "level_min": 25.0, "level_max": 38.0,
    "tank_height": 45.0
}

# Proveedor temporal de demostración. Se reemplazará por el adaptador de sensores
# de Raspberry Pi/GrovePi+ cuando se conecte el hardware real.
DEMO = {"ph": 7.0, "temperature": 23.4, "level": 31.0}
OUTPUTS = {"pump": False, "heater": False, "heater_mode": "automatic",
           "pump_needs_confirmation": True}

def now_iso():
    return datetime.now().astimezone().isoformat(timespec="seconds")

def connect():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con

def init_db():
    with connect() as con:
        con.execute("""CREATE TABLE IF NOT EXISTS readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            variable TEXT NOT NULL, value REAL, unit TEXT NOT NULL,
            timestamp TEXT NOT NULL, valid INTEGER NOT NULL,
            reason TEXT DEFAULT ''
        )""")
        con.execute("""CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kind TEXT NOT NULL, message TEXT NOT NULL,
            timestamp TEXT NOT NULL, active INTEGER NOT NULL DEFAULT 1,
            recommendation TEXT DEFAULT ''
        )""")
        con.execute("""CREATE TABLE IF NOT EXISTS config (
            id INTEGER PRIMARY KEY CHECK(id=1), data TEXT NOT NULL
        )""")
        if not con.execute("SELECT id FROM config WHERE id=1").fetchone():
            con.execute("INSERT INTO config(id,data) VALUES(1,?)", (json.dumps(DEFAULT_CONFIG),))
        count = con.execute("SELECT COUNT(*) AS n FROM readings").fetchone()["n"]
        if count == 0:
            seed_demo_data(con)

def seed_demo_data(con):
    # Datos de demostración visibles hasta integrar los sensores reales.
    for mins, temp, ph, level in [
        (30, 23.4, 7.0, 31.0), (15, 23.5, 7.1, 31.0), (0, 23.4, 7.0, 31.0)
    ]:
        stamp = (datetime.now().astimezone() - timedelta(minutes=mins)).isoformat(timespec="seconds")
        for var, val, unit in [("temperature",temp,"°C"),("ph",ph,"pH"),("level",level,"cm")]:
            con.execute("INSERT INTO readings(variable,value,unit,timestamp,valid,reason) VALUES(?,?,?,?,1,'')",
                        (var,val,unit,stamp))

def get_config():
    with connect() as con:
        row = con.execute("SELECT data FROM config WHERE id=1").fetchone()
        return json.loads(row["data"])

def latest_readings():
    result = {}
    with connect() as con:
        for var in ("ph", "temperature", "level"):
            row = con.execute("SELECT * FROM readings WHERE variable=? ORDER BY id DESC LIMIT 1",(var,)).fetchone()
            if row:
                stamp = datetime.fromisoformat(row["timestamp"])
                age = (datetime.now(stamp.tzinfo) - stamp).total_seconds() / 60
                valid = bool(row["valid"]) and age <= 30
                result[var] = {"value": row["value"], "unit": row["unit"], "timestamp": row["timestamp"],
                               "valid": valid, "stored_valid": bool(row["valid"]),
                               "expired": age > 30, "age_minutes": round(age,1),
                               "reason": row["reason"] or ("Dato vencido" if age > 30 else "")}
    return result

def add_event(kind, message, recommendation=""):
    with connect() as con:
        active = con.execute("SELECT id FROM events WHERE kind=? AND active=1",(kind,)).fetchone()
        if not active:
            con.execute("INSERT INTO events(kind,message,timestamp,active,recommendation) VALUES(?,?,?,?,?)",
                        (kind,message,now_iso(),1,recommendation))
        else:
            con.execute("UPDATE events SET message=?, recommendation=? WHERE id=?",
                        (message,recommendation,active["id"]))

def close_event(kind):
    with connect() as con:
        con.execute("UPDATE events SET active=0 WHERE kind=? AND active=1",(kind,))

def evaluate():
    cfg, readings = get_config(), latest_readings()
    level = readings.get("level")
    temp = readings.get("temperature")
    ph = readings.get("ph")
    level_ok = bool(level and level["valid"])
    low = level_ok and level["value"] < cfg["level_min"]
    blocked = not level_ok or low

    if blocked:
        OUTPUTS["pump"] = False
        OUTPUTS["heater"] = False
        OUTPUTS["pump_needs_confirmation"] = True
        reason = "Nivel bajo" if low else "Nivel inválido o vencido"
        add_event("level_block", reason, "Revisar el nivel y el sensor. Tras recuperar el nivel, confirmar Encender bomba.")
    else:
        close_event("level_block")

    if level_ok and level["value"] > cfg["level_max"]:
        add_event("level_high", "Nivel por encima del máximo", "Revisar el llenado y la altura del agua.")
    else:
        close_event("level_high")

    if not temp or not temp["valid"]:
        OUTPUTS["heater"] = False
        add_event("temperature_invalid", "Temperatura inválida o vencida", "Revisar la sonda DS18B20.")
    else:
        close_event("temperature_invalid")
        if temp["value"] < cfg["temp_min"] or temp["value"] > cfg["temp_max"]:
            add_event("temperature_limit", "Temperatura fuera de los límites de alerta", "Revisar temperatura y calefactor.")
        else:
            close_event("temperature_limit")
        if blocked or temp["value"] >= cfg["temp_max"]:
            OUTPUTS["heater"] = False
        elif OUTPUTS["heater_mode"] == "automatic":
            if temp["value"] <= cfg["heater_on"]:
                OUTPUTS["heater"] = True
            elif temp["value"] >= cfg["heater_off"]:
                OUTPUTS["heater"] = False

    if not ph or not ph["valid"]:
        add_event("ph_invalid", "Lectura de pH inválida o vencida", "Revisar y calibrar la sonda de pH.")
    else:
        close_event("ph_invalid")
        if ph["value"] < cfg["ph_min"] or ph["value"] > cfg["ph_max"]:
            add_event("ph_limit", "pH fuera de los límites configurados", "Comprobar la sonda y revisar el agua.")
        else:
            close_event("ph_limit")
    return {"blocked": blocked}

def save_reading(variable, value, unit, valid=True, reason=""):
    with connect() as con:
        con.execute("INSERT INTO readings(variable,value,unit,timestamp,valid,reason) VALUES(?,?,?,?,?,?)",
                    (variable,value,unit,now_iso(),1 if valid else 0,reason))
    evaluate()

def get_status():
    state = evaluate()
    return {"project":"EcoAcuario", "server_time":now_iso(), "connection":"online",
            "readings":latest_readings(), "outputs":OUTPUTS.copy(),
            "blocked":state["blocked"], "config":get_config()}

@app.get("/")
def index():
    return send_from_directory(FRONTEND, "index.html")

@app.get("/api/status")
def api_status():
    return jsonify(get_status())

@app.post("/api/measure")
def api_measure():
    # En modo demo se usan los valores ajustados en el simulador.
    # En modo hardware, esta función llamará al adaptador físico.
    for var, unit in [("ph","pH"),("temperature","°C"),("level","cm")]:
        save_reading(var, DEMO[var], unit, True)
    return jsonify({"ok":True,"message":"Lectura de demostración registrada","status":get_status()})

@app.get("/api/history")
def api_history():
    variable = request.args.get("variable","temperature")
    hours = min(int(request.args.get("hours",24)), 720)
    if variable not in ("ph","temperature","level"):
        return jsonify({"error":"Variable no válida"}),400
    since = (datetime.now().astimezone()-timedelta(hours=hours)).isoformat()
    with connect() as con:
        rows = con.execute("""SELECT variable,value,unit,timestamp,valid,reason FROM readings
            WHERE variable=? AND timestamp>=? ORDER BY id DESC LIMIT 500""",(variable,since)).fetchall()
    return jsonify({"variable":variable,"records":[dict(r) for r in rows][::-1]})

@app.get("/api/config")
def api_get_config():
    return jsonify(get_config())

@app.put("/api/config")
def api_set_config():
    data = request.get_json(silent=True) or {}
    cfg = get_config()
    try:
        proposed = {k:float(data[k]) for k in DEFAULT_CONFIG}
    except (KeyError,TypeError,ValueError):
        return jsonify({"ok":False,"message":"Completa todos los valores numéricos."}),400
    if not (proposed["ph_min"] < proposed["ph_max"]):
        return jsonify({"ok":False,"message":"El mínimo de pH debe ser menor que el máximo."}),400
    if not (proposed["temp_min"] < proposed["heater_on"] < proposed["heater_off"] < proposed["temp_max"]):
        return jsonify({"ok":False,"message":"Se requiere: mínimo alerta < encender < apagar < máximo alerta."}),400
    if not (0 < proposed["level_min"] < proposed["level_max"] < proposed["tank_height"]):
        return jsonify({"ok":False,"message":"El nivel debe ser positivo y menor que el máximo y la altura del recipiente."}),400
    with connect() as con:
        con.execute("UPDATE config SET data=? WHERE id=1",(json.dumps(proposed),))
    evaluate()
    return jsonify({"ok":True,"message":"Configuración guardada","config":proposed})

@app.get("/api/alerts")
def api_alerts():
    with connect() as con:
        rows = con.execute("SELECT * FROM events ORDER BY id DESC LIMIT 100").fetchall()
    return jsonify({"alerts":[dict(r) for r in rows]})

@app.post("/api/control/heater")
def api_heater():
    data = request.get_json(silent=True) or {}
    mode = data.get("mode")
    action = data.get("action")
    if mode not in ("automatic","manual") or action not in ("on","off","auto"):
        return jsonify({"ok":False,"message":"Orden no válida."}),400
    if action == "auto":
        OUTPUTS["heater_mode"] = "automatic"
        evaluate()
        message = "Modo automático activado; se reevaluó la temperatura."
    else:
        OUTPUTS["heater_mode"] = "manual"
        state = evaluate()
        if action == "on":
            readings = latest_readings()
            temp = readings.get("temperature")
            if state["blocked"] or not temp or not temp["valid"] or temp["value"] >= get_config()["temp_max"]:
                OUTPUTS["heater"] = False
                return jsonify({"ok":False,"message":"Encendido bloqueado por nivel o temperatura inválida/fuera de seguridad.",
                                "status":get_status()}),409
            OUTPUTS["heater"] = True
            message = "Solicitud de encendido aceptada."
        else:
            OUTPUTS["heater"] = False
            message = "Calefactor apagado; quedó en modo manual."
    with connect() as con:
        con.execute("INSERT INTO events(kind,message,timestamp,active,recommendation) VALUES(?,?,?,?,?)",
                    ("control_heater",message,now_iso(),0,""))
    return jsonify({"ok":True,"message":message,"status":get_status()})

@app.post("/api/control/pump")
def api_pump():
    data = request.get_json(silent=True) or {}
    action = data.get("action")
    if action not in ("on","off"):
        return jsonify({"ok":False,"message":"Orden no válida."}),400
    state = evaluate()
    if action == "on":
        if state["blocked"]:
            return jsonify({"ok":False,"message":"Bomba bloqueada: revisar y recuperar el nivel de agua.",
                            "status":get_status()}),409
        OUTPUTS["pump"] = True
        OUTPUTS["pump_needs_confirmation"] = False
        message = "Bomba encendida tras confirmación."
    else:
        OUTPUTS["pump"] = False
        OUTPUTS["pump_needs_confirmation"] = True
        message = "Bomba apagada."
    with connect() as con:
        con.execute("INSERT INTO events(kind,message,timestamp,active,recommendation) VALUES(?,?,?,?,?)",
                    ("control_pump",message,now_iso(),0,""))
    return jsonify({"ok":True,"message":message,"status":get_status()})

@app.get("/api/demo")
def api_demo_values():
    return jsonify(DEMO)

@app.put("/api/demo")
def api_set_demo():
    data = request.get_json(silent=True) or {}
    try:
        for k in DEMO:
            if k in data: DEMO[k] = float(data[k])
    except (ValueError,TypeError):
        return jsonify({"ok":False,"message":"Valor inválido"}),400
    return jsonify({"ok":True,"values":DEMO})

init_db()

if __name__ == "__main__":
    # 0.0.0.0 permite abrir la aplicación desde otros dispositivos de la misma Wi-Fi.
    app.run(host="0.0.0.0", port=5000, debug=False)
