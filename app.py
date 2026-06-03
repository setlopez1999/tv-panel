import os
import subprocess

from flask import Flask, jsonify, render_template

from config import add_android_device, add_lg_tv, get_server_ip, legacy_view, load_devices
from modules.registry import list_connection_types
from routes import android_bp, lg_bp
from tools_paths import get_adb_path, get_scrcpy_path, tools_info

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = os.path.abspath("uploads")
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

app.register_blueprint(lg_bp)
app.register_blueprint(android_bp)


@app.context_processor
def inject_globals():
    return {
        "connection_types": list_connection_types(),
        "server_ip": get_server_ip(),
        "tools": tools_info(),
    }


@app.route("/")
def index():
    devices = legacy_view(load_devices())
    return render_template("index.html", devices=devices)


@app.route("/api/devices/add", methods=["POST"])
def add_device_unified():
    """Alta unificada: type=lg | android."""
    data = request.json or {}
    dtype = (data.get("type") or "").lower()
    name = data.get("name", "").strip()
    ip = data.get("ip", "").strip()
    if not name or not ip:
        return jsonify({"success": False, "message": "Nombre e IP son obligatorios"})

    if dtype == "lg":
        ok = add_lg_tv(name, ip)
        msg = "TV LG agregada" if ok else "Ya existe esa IP"
    elif dtype == "android":
        code = data.get("device_code") or f"{ip}:5555"
        ok = add_android_device(name, ip, code)
        msg = "Android TV agregada" if ok else "Ya existe esa IP"
    else:
        return jsonify({"success": False, "message": "Tipo inválido. Usa lg o android"})

    return jsonify({"success": ok, "message": msg, "type": dtype})


@app.route("/api/health")
def health():
    info = tools_info()
    checks = {"lgtv": False, "adb": False, "scrcpy": False}
    try:
        r = subprocess.run("lgtv scan", shell=True, capture_output=True, timeout=8)
        checks["lgtv"] = r.returncode == 0 or bool(r.stdout)
    except Exception:
        pass
    try:
        r = subprocess.run([get_adb_path(), "version"], capture_output=True, timeout=5)
        checks["adb"] = r.returncode == 0
    except Exception:
        pass
    try:
        r = subprocess.run([get_scrcpy_path(), "--version"], capture_output=True, timeout=5)
        checks["scrcpy"] = r.returncode == 0
    except Exception:
        pass
    return jsonify({"ok": True, "tools": checks, "paths": info, "server_ip": get_server_ip()})


if __name__ == "__main__":
    t = tools_info()
    print(f"TV Control Panel → http://{get_server_ip()}:5000")
    print(f"ADB: {t['adb']}")
    print(f"scrcpy: {t['scrcpy']}")
    app.run(host="0.0.0.0", port=5000, debug=False)
