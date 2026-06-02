import os

from flask import Blueprint, Response, current_app, jsonify, render_template, request, send_file

from config import add_android_device, find_device, legacy_view, load_devices, remove_device
from modules.android.driver import AndroidDriver

android_bp = Blueprint("android", __name__)


def _android_for_ip(ip: str) -> AndroidDriver:
    dev = find_device("android", ip)
    code = dev.get("device_code") if dev else None
    return AndroidDriver(ip, code)


@android_bp.route("/android")
def android_page():
    devices = legacy_view(load_devices())
    return render_template("android_devices.html", devices=devices["android_devices"])


@android_bp.route("/api/android/add", methods=["POST"])
def android_add():
    data = request.json or {}
    success = add_android_device(data.get("name"), data.get("ip"), data.get("device_code"))
    return jsonify(
        {"success": success, "message": "Dispositivo agregado" if success else "Ya existe esa IP"}
    )


@android_bp.route("/api/android/connect/<ip>", methods=["POST"])
def android_connect(ip):
    if not find_device("android", ip):
        return jsonify({"success": False, "message": "Dispositivo no encontrado"})
    result = _android_for_ip(ip).connect()
    return jsonify(result)


@android_bp.route("/api/android/open-url", methods=["POST"])
def android_open_url():
    data = request.json or {}
    result = _android_for_ip(data["ip"]).open_url(data["url"])
    return jsonify(result)


@android_bp.route("/api/android/open-app", methods=["POST"])
def android_open_app():
    data = request.json or {}
    result = _android_for_ip(data["ip"]).open_app(data["package"])
    return jsonify(result)


@android_bp.route("/api/android/install-apk", methods=["POST"])
def android_install_apk():
    if "apk" not in request.files:
        return jsonify({"success": False, "message": "No se envió ningún archivo APK"})

    file = request.files["apk"]
    ip = request.form.get("ip")

    if not file.filename or not file.filename.lower().endswith(".apk"):
        return jsonify({"success": False, "message": "Archivo APK inválido"})

    filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], file.filename)
    file.save(filepath)
    result = _android_for_ip(ip).install_apk(filepath)
    os.remove(filepath)
    return jsonify(result)


@android_bp.route("/api/android/scrcpy/<ip>", methods=["POST"])
def android_scrcpy(ip):
    result = _android_for_ip(ip).start_scrcpy(on_host=True)
    return jsonify(result)


@android_bp.route("/api/android/launcher/<ip>")
def android_launcher(ip):
    dev = find_device("android", ip)
    if not dev:
        return jsonify({"success": False, "message": "Dispositivo no encontrado"}), 404
    driver = AndroidDriver(ip, dev.get("device_code"))
    safe_name = dev.get("name", "android").replace(" ", "_")[:20]
    return Response(
        driver.launcher_cmd_content(),
        mimetype="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="scrcpy_{safe_name}.cmd"'},
    )


@android_bp.route("/api/android/screenshot/<ip>", methods=["GET"])
def android_screenshot(ip):
    img_path = _android_for_ip(ip).get_screenshot()
    if os.path.exists(img_path):
        return send_file(img_path, mimetype="image/png")
    return jsonify({"success": False, "message": "No se pudo capturar la pantalla"}), 500


@android_bp.route("/api/android/remove/<ip>", methods=["DELETE"])
def android_remove(ip):
    remove_device("android", ip)
    return jsonify({"success": True, "message": "Dispositivo eliminado"})


@android_bp.route("/api/android/devices", methods=["GET"])
def android_list_devices():
    return jsonify(AndroidDriver.list_devices())
