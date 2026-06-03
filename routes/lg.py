import os
import uuid

from flask import Blueprint, current_app, jsonify, render_template, request
from werkzeug.utils import secure_filename

from config import (
    add_lg_tv,
    find_device,
    legacy_view,
    load_devices,
    remove_device,
    update_device,
    update_lg_ares_config,
)
from modules.lg.ares_driver import AresDriver
from modules.lg.driver import LGDriver

lg_bp = Blueprint("lg", __name__)


def _lg_driver_for_ip(ip: str) -> LGDriver:
    dev = find_device("lg", ip)
    return LGDriver(
        ip,
        name=dev["name"] if dev else "",
        lgtv_alias=dev.get("lgtv_alias", "") if dev else "",
    )


def _ares_for_ip(ip: str) -> AresDriver | None:
    dev = find_device("lg", ip)
    if not dev or not dev.get("ares_device"):
        return None
    return AresDriver(dev["ares_device"])


def _require_ares(ip: str):
    dev = find_device("lg", ip)
    if not dev:
        return None, (jsonify({"success": False, "message": "TV no encontrada"}), 404)
    if not dev.get("ares_device"):
        return None, (
            jsonify({"success": False, "message": "Configura el nombre ares en el asistente"}),
            400,
        )
    return AresDriver(dev["ares_device"]), None


@lg_bp.route("/lg")
def lg_page():
    devices = legacy_view(load_devices())
    return render_template("lg_devices.html", tvs=devices["lg_tvs"])


@lg_bp.route("/api/lg/scan", methods=["POST"])
def lg_scan():
    result = LGDriver.scan_network()
    added = 0
    if result.get("result") == "ok" and result.get("list"):
        for tv in result["list"]:
            name = tv.get("tv_name", "LG TV")
            ip = tv.get("address")
            uuid_val = tv.get("uuid", "")
            if ip and add_lg_tv(name, ip, uuid=uuid_val):
                added += 1
        result["added"] = added
    return jsonify(result)


@lg_bp.route("/api/lg/add", methods=["POST"])
def lg_add():
    data = request.json or {}
    success = add_lg_tv(data.get("name"), data.get("ip"))
    return jsonify({"success": success, "message": "TV agregada" if success else "Ya existe esa IP"})


@lg_bp.route("/api/lg/auth/<ip>", methods=["POST"])
def lg_auth(ip):
    result = _lg_driver_for_ip(ip).auth()
    if result.get("lgtv_alias"):
        update_device("lg", ip, lgtv_alias=result["lgtv_alias"], status="paired")
    return jsonify(result)


@lg_bp.route("/api/lg/open-url", methods=["POST"])
def lg_open_url():
    data = request.json or {}
    result = _lg_driver_for_ip(data["ip"]).open_browser(data["url"])
    return jsonify(result)


@lg_bp.route("/api/lg/open-app", methods=["POST"])
def lg_open_app():
    data = request.json or {}
    result = _lg_driver_for_ip(data["ip"]).open_app(data["app_id"])
    return jsonify(result)


@lg_bp.route("/api/lg/volume", methods=["POST"])
def lg_volume():
    data = request.json or {}
    tv = _lg_driver_for_ip(data["ip"])
    if data.get("action") == "set":
        result = tv.set_volume(data["level"])
    else:
        result = tv.get_volume()
    return jsonify(result)


@lg_bp.route("/api/lg/power", methods=["POST"])
def lg_power():
    data = request.json or {}
    tv = _lg_driver_for_ip(data["ip"])
    if data.get("action") == "on":
        result = tv.turn_on()
    else:
        result = tv.turn_off()
    return jsonify(result)


@lg_bp.route("/api/lg/list-apps", methods=["POST"])
def lg_list_apps():
    data = request.json or {}
    ip = data["ip"]
    result = _lg_driver_for_ip(ip).list_apps()
    if result.get("apps"):
        update_device("lg", ip, cached_apps=result["apps"])
    return jsonify(result)


@lg_bp.route("/api/lg/close-app", methods=["POST"])
def lg_close_app():
    data = request.json or {}
    return jsonify(_lg_driver_for_ip(data["ip"]).close_app(data["app_id"]))


# --- ares-cli (IPK / Developer Mode) ---


@lg_bp.route("/api/lg/ares/save-config", methods=["POST"])
def lg_ares_save_config():
    data = request.json or {}
    ip = data.get("ip")
    if not ip:
        return jsonify({"success": False, "message": "IP requerida"})
    update_lg_ares_config(
        ip,
        ares_device=data.get("ares_device", "").strip(),
        ares_port=int(data.get("ares_port", 9922)),
        ares_user=data.get("ares_user", "developer").strip(),
    )
    return jsonify({"success": True, "message": "Configuración ares guardada"})


@lg_bp.route("/api/lg/ares/setup", methods=["POST"])
def lg_ares_setup():
    data = request.json or {}
    ip = data["ip"]
    ares, err = _require_ares(ip)
    if err:
        return err
    dev = find_device("lg", ip)
    result = ares.setup_device(
        ip,
        port=dev.get("ares_port", 9922),
        user=dev.get("ares_user", "developer"),
        description=dev.get("name", ""),
    )
    return jsonify(result)


@lg_bp.route("/api/lg/ares/getkey", methods=["POST"])
def lg_ares_getkey():
    data = request.json or {}
    ip = data["ip"]
    ares, err = _require_ares(ip)
    if err:
        return err
    result = ares.get_key(data.get("passphrase", ""))
    if result.get("success"):
        update_lg_ares_config(ip, ares_linked=True)
    return jsonify(result)


@lg_bp.route("/api/lg/ares/verify", methods=["POST"])
def lg_ares_verify():
    data = request.json or {}
    ip = data["ip"]
    ares, err = _require_ares(ip)
    if err:
        return err
    result = ares.device_info()
    if result.get("linked"):
        update_lg_ares_config(ip, ares_linked=True)
        result["message"] = "TV vinculada correctamente con ares"
    else:
        update_lg_ares_config(ip, ares_linked=False)
    return jsonify(result)


@lg_bp.route("/api/lg/ares/install-ipk", methods=["POST"])
def lg_ares_install_ipk():
    if "ipk" not in request.files:
        return jsonify({"success": False, "message": "No se envió archivo IPK"})
    file = request.files["ipk"]
    ip = request.form.get("ip")
    if not file.filename or not file.filename.lower().endswith(".ipk"):
        return jsonify({"success": False, "message": "Archivo .ipk inválido"})
    ares, err = _require_ares(ip)
    if err:
        return err
    upload_dir = os.path.abspath(current_app.config["UPLOAD_FOLDER"])
    os.makedirs(upload_dir, exist_ok=True)
    safe = secure_filename(file.filename) or "app.ipk"
    filepath = os.path.join(upload_dir, f"{uuid.uuid4().hex}_{safe}")
    file.save(filepath)
    try:
        result = ares.install_ipk(filepath)
    finally:
        if os.path.isfile(filepath):
            os.remove(filepath)
    return jsonify(result)


@lg_bp.route("/api/lg/ares/list-installed", methods=["POST"])
def lg_ares_list_installed():
    data = request.json or {}
    ip = data["ip"]
    ares, err = _require_ares(ip)
    if err:
        return err
    result = ares.list_installed()
    if result.get("packages"):
        update_lg_ares_config(ip, cached_ares_packages=result["packages"])
    return jsonify(result)


@lg_bp.route("/api/lg/ares/launch", methods=["POST"])
def lg_ares_launch():
    data = request.json or {}
    ip = data["ip"]
    ares, err = _require_ares(ip)
    if err:
        return err
    return jsonify(ares.launch(data["package_id"]))


@lg_bp.route("/api/lg/ares/remove", methods=["POST"])
def lg_ares_remove_pkg():
    data = request.json or {}
    ip = data["ip"]
    ares, err = _require_ares(ip)
    if err:
        return err
    return jsonify(ares.remove(data["package_id"]))


@lg_bp.route("/api/lg/remove/<ip>", methods=["DELETE"])
def lg_remove(ip):
    remove_device("lg", ip)
    return jsonify({"success": True, "message": "TV eliminada"})
