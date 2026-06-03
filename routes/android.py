import os
import uuid

from flask import Blueprint, Response, current_app, jsonify, render_template, request, send_file
from werkzeug.utils import secure_filename

from config import add_android_device, find_device, legacy_view, load_devices, remove_device, update_device
from modules.android.driver import AndroidDriver
from tools_paths import tools_info

android_bp = Blueprint("android", __name__)


def _android_for_ip(ip: str) -> AndroidDriver:
    dev = find_device("android", ip)
    code = dev.get("device_code") if dev else None
    return AndroidDriver(ip, code)


@android_bp.route("/android")
def android_page():
    devices = legacy_view(load_devices())
    return render_template(
        "android_devices.html",
        devices=devices["android_devices"],
        tools=tools_info(),
    )


@android_bp.route("/api/android/add", methods=["POST"])
def android_add():
    data = request.json or {}
    success = add_android_device(data.get("name"), data.get("ip"), data.get("device_code"))
    return jsonify(
        {"success": success, "message": "Android TV agregada" if success else "Ya existe esa IP"}
    )


@android_bp.route("/api/android/connect/<ip>", methods=["POST"])
def android_connect(ip):
    if not find_device("android", ip):
        return jsonify({"success": False, "message": "Dispositivo no encontrado"})
    driver = _android_for_ip(ip)
    result = driver.connect()
    result["device_code"] = driver.device_code
    return jsonify(result)


@android_bp.route("/api/android/open-url", methods=["POST"])
def android_open_url():
    data = request.json or {}
    return jsonify(_android_for_ip(data["ip"]).open_url(data["url"]))


@android_bp.route("/api/android/open-app", methods=["POST"])
def android_open_app():
    data = request.json or {}
    return jsonify(_android_for_ip(data["ip"]).open_app(data["package"]))


@android_bp.route("/api/android/install-apk", methods=["POST"])
def android_install_apk():
    if "apk" not in request.files:
        return jsonify({"success": False, "message": "No se envió ningún archivo APK"})

    file = request.files["apk"]
    ip = request.form.get("ip")

    if not file.filename or not file.filename.lower().endswith(".apk"):
        return jsonify({"success": False, "message": "Archivo APK inválido"})

    upload_dir = os.path.abspath(current_app.config["UPLOAD_FOLDER"])
    os.makedirs(upload_dir, exist_ok=True)
    safe = secure_filename(file.filename) or "app.apk"
    filepath = os.path.join(upload_dir, f"{uuid.uuid4().hex}_{safe}")
    file.save(filepath)
    try:
        result = _android_for_ip(ip).install_apk(filepath)
    finally:
        if os.path.isfile(filepath):
            os.remove(filepath)
    return jsonify(result)


@android_bp.route("/api/android/list-packages", methods=["POST"])
def android_list_packages():
    data = request.json or {}
    ip = data["ip"]
    result = _android_for_ip(ip).list_packages()
    if result.get("success") and result.get("packages"):
        update_device("android", ip, cached_packages=result["packages"])
    return jsonify(result)


@android_bp.route("/api/android/uninstall", methods=["POST"])
def android_uninstall():
    data = request.json or {}
    return jsonify(_android_for_ip(data["ip"]).uninstall(data["package"]))


@android_bp.route("/api/android/keyevent", methods=["POST"])
def android_keyevent():
    data = request.json or {}
    return jsonify(_android_for_ip(data["ip"]).keyevent(int(data["key"])))


@android_bp.route("/api/android/input-text", methods=["POST"])
def android_input_text():
    data = request.json or {}
    return jsonify(_android_for_ip(data["ip"]).input_text(data.get("text", "")))


@android_bp.route("/api/android/push-file", methods=["POST"])
def android_push_file():
    if "file" not in request.files:
        return jsonify({"success": False, "message": "No se envió archivo"})
    f = request.files["file"]
    ip = request.form.get("ip")
    remote = request.form.get("remote_path", "/sdcard/Download/")
    upload_dir = os.path.abspath(current_app.config["UPLOAD_FOLDER"])
    os.makedirs(upload_dir, exist_ok=True)
    filepath = os.path.abspath(os.path.join(upload_dir, secure_filename(f.filename) or "file"))
    f.save(filepath)
    result = _android_for_ip(ip).push_file(filepath, remote)
    if os.path.isfile(filepath):
        os.remove(filepath)
    return jsonify(result)


@android_bp.route("/api/android/reboot", methods=["POST"])
def android_reboot():
    data = request.json or {}
    power_off = data.get("power_off", False)
    return jsonify(_android_for_ip(data["ip"]).reboot(power_off=power_off))


@android_bp.route("/api/android/scrcpy/<ip>", methods=["POST"])
def android_scrcpy(ip):
    return jsonify(_android_for_ip(ip).start_scrcpy(on_host=True))


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
    if os.path.isfile(img_path) and os.path.getsize(img_path) > 500:
        return send_file(img_path, mimetype="image/png")
    return jsonify({"success": False, "message": "No se pudo capturar. Conecta ADB y autoriza en la TV."}), 500


@android_bp.route("/api/android/remove/<ip>", methods=["DELETE"])
def android_remove(ip):
    remove_device("android", ip)
    return jsonify({"success": True, "message": "Dispositivo eliminado"})


@android_bp.route("/api/android/devices", methods=["GET"])
def android_list_devices():
    return jsonify(AndroidDriver.list_devices())
