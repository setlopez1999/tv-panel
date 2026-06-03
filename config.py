import json
import os
import re
import socket

CONFIG_FILE = "devices.json"

DEFAULT_CONFIG = {
    "connections": {
        "lg": [],
        "android": [],
    }
}


def _migrate(data: dict) -> dict:
    if "connections" in data:
        migrated = data
    else:
        migrated = {
            "connections": {
                "lg": data.get("lg_tvs", []),
                "android": data.get("android_devices", []),
            }
        }
    changed = "connections" not in data
    for tv in migrated["connections"].get("lg", []):
        if "lgtv_alias" not in tv:
            tv["lgtv_alias"] = _lg_alias_from_name(tv.get("name", "lg"))
            changed = True
        if "ares_device" not in tv:
            tv["ares_device"] = _ares_device_from_name(tv.get("name", "lg"))
            changed = True
        for key, default in _LG_ARES_DEFAULTS.items():
            if key not in tv:
                tv[key] = default
                changed = True
    if changed:
        save_devices(migrated)
    return migrated


def load_devices():
    if not os.path.exists(CONFIG_FILE):
        save_devices(DEFAULT_CONFIG.copy())
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return _migrate(data)


def save_devices(data):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_list(conn_type: str) -> list:
    return load_devices()["connections"].get(conn_type, [])


def find_device(conn_type: str, ip: str):
    return next((d for d in get_list(conn_type) if d["ip"] == ip), None)


def add_device(conn_type: str, entry: dict) -> bool:
    devices = load_devices()
    lst = devices["connections"].setdefault(conn_type, [])
    if any(d["ip"] == entry["ip"] for d in lst):
        return False
    lst.append(entry)
    save_devices(devices)
    return True


def remove_device(conn_type: str, ip: str):
    devices = load_devices()
    devices["connections"][conn_type] = [
        d for d in devices["connections"].get(conn_type, []) if d["ip"] != ip
    ]
    save_devices(devices)


def update_device(conn_type: str, ip: str, **fields):
    devices = load_devices()
    for d in devices["connections"].get(conn_type, []):
        if d["ip"] == ip:
            d.update(fields)
            break
    save_devices(devices)


def add_lg_tv(name, ip, uuid=None):
    return add_device("lg", lg_device_defaults(name, ip, uuid))


def add_android_device(name, ip, device_code=None):
    code = device_code or f"{ip}:5555"
    return add_device(
        "android",
        {
            "name": name,
            "ip": ip,
            "device_code": code,
            "status": "unknown",
        },
    )


def _lg_alias_from_name(name: str) -> str:
    safe = re.sub(r"[^a-zA-Z0-9_]", "_", (name or "lg").lower())[:30]
    return f"tv_{safe}" if safe else "tv_lg"


def _ares_device_from_name(name: str) -> str:
    safe = re.sub(r"[^a-zA-Z0-9_]", "_", (name or "lg").lower())[:24]
    return f"lgtv_{safe}" if safe else "lgtv_1"


_LG_ARES_DEFAULTS = {
    "ares_port": 9922,
    "ares_user": "developer",
    "ares_linked": False,
    "cached_ares_packages": [],
}


def lg_device_defaults(name: str, ip: str, uuid: str = "") -> dict:
    return {
        "name": name,
        "ip": ip,
        "lgtv_alias": _lg_alias_from_name(name),
        "uuid": uuid or "",
        "status": "unknown",
        "ares_device": _ares_device_from_name(name),
        "ares_port": 9922,
        "ares_user": "developer",
        "ares_linked": False,
        "cached_ares_packages": [],
    }


def update_lg_ares_config(ip: str, **fields):
    update_device("lg", ip, **fields)


def get_server_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except OSError:
        return "127.0.0.1"


def legacy_view(devices: dict) -> dict:
    """Compatibilidad con templates que usan lg_tvs / android_devices."""
    c = devices["connections"]
    return {
        **devices,
        "lg_tvs": c.get("lg", []),
        "android_devices": c.get("android", []),
    }
