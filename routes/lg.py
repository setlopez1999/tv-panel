from flask import Blueprint, jsonify, render_template, request

from config import add_lg_tv, find_device, get_list, legacy_view, load_devices, remove_device, update_device
from modules.lg.driver import LGDriver

lg_bp = Blueprint("lg", __name__)


def _lg_driver_for_ip(ip: str) -> LGDriver:
    dev = find_device("lg", ip)
    return LGDriver(
        ip,
        name=dev["name"] if dev else "",
        lgtv_alias=dev.get("lgtv_alias", "") if dev else "",
    )


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
            uuid = tv.get("uuid", "")
            if ip and add_lg_tv(name, ip, uuid=uuid):
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


@lg_bp.route("/api/lg/remove/<ip>", methods=["DELETE"])
def lg_remove(ip):
    remove_device("lg", ip)
    return jsonify({"success": True, "message": "TV eliminada"})
