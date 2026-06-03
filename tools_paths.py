"""Rutas a adb.exe y scrcpy.exe (bundled o PATH)."""
import json
import os
import shutil

SETTINGS_FILE = "settings.json"

DEFAULT_SCRCPY_DIR = r"C:\Users\PC1\Downloads\scrcpy\scrcpy-win64-v3.3.4"


def _load_settings() -> dict:
    if os.path.isfile(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def get_scrcpy_dir() -> str:
    settings = _load_settings()
    for key in ("scrcpy_dir", "tools_dir"):
        path = settings.get(key, "").strip()
        if path and os.path.isdir(path):
            return os.path.normpath(path)
    env = os.environ.get("TV_SCRCPY_DIR", "").strip()
    if env and os.path.isdir(env):
        return os.path.normpath(env)
    if os.path.isdir(DEFAULT_SCRCPY_DIR):
        return os.path.normpath(DEFAULT_SCRCPY_DIR)
    return ""


def get_adb_path() -> str:
    bundled = get_scrcpy_dir()
    if bundled:
        exe = os.path.join(bundled, "adb.exe")
        if os.path.isfile(exe):
            return exe
    which = shutil.which("adb")
    return which or "adb"


def get_scrcpy_path() -> str:
    bundled = get_scrcpy_dir()
    if bundled:
        exe = os.path.join(bundled, "scrcpy.exe")
        if os.path.isfile(exe):
            return exe
    which = shutil.which("scrcpy")
    return which or "scrcpy"


def get_ares_path() -> str:
    return shutil.which("ares") or "ares"


def _ares_available() -> bool:
    import subprocess

    try:
        r = subprocess.run(
            [get_ares_path(), "-V"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return r.returncode == 0
    except Exception:
        return False


def tools_info() -> dict:
    ares_ok = _ares_available()
    return {
        "scrcpy_dir": get_scrcpy_dir() or None,
        "adb": get_adb_path(),
        "scrcpy": get_scrcpy_path(),
        "adb_bundled": get_adb_path().lower().endswith(".exe"),
        "ares": get_ares_path(),
        "ares_ok": ares_ok,
    }
