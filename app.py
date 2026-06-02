import os

from flask import Flask, jsonify, render_template

from config import get_server_ip, legacy_view, load_devices
from modules.registry import list_connection_types
from routes import android_bp, lg_bp

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "uploads"
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

app.register_blueprint(lg_bp)
app.register_blueprint(android_bp)


@app.context_processor
def inject_globals():
    return {
        "connection_types": list_connection_types(),
        "server_ip": get_server_ip(),
    }


@app.route("/")
def index():
    devices = legacy_view(load_devices())
    return render_template("index.html", devices=devices)


@app.route("/api/health")
def health():
    tools = {}
    for name, cmd in [("lgtv", "lgtv scan"), ("adb", "adb version"), ("scrcpy", "scrcpy --version")]:
        try:
            import subprocess

            r = subprocess.run(cmd, shell=True, capture_output=True, timeout=5)
            tools[name] = r.returncode == 0
        except Exception:
            tools[name] = False
    return jsonify({"ok": True, "tools": tools, "server_ip": get_server_ip()})


if __name__ == "__main__":
    print(f"TV Control Panel → http://{get_server_ip()}:5000")
    app.run(host="0.0.0.0", port=5000, debug=False)
