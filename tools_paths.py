"""Rutas a adb.exe y scrcpy.exe (data/scrcpy, settings.json o PATH)."""
import json
import os
import shutil

SETTINGS_FILE = "settings.json"
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_SCRCPY_DIR = os.path.join(PROJECT_ROOT, "data", "scrcpy")

DEFAULT_SCRCPY_DIR = r"C:\Users\PC1\Downloads\scrcpy\scrcpy-win64-v3.3.4"


def _load_settings() -> dict:
    if os.path.isfile(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def _dir_has_scrcpy(path: str) -> bool:
    return bool(path) and os.path.isfile(os.path.join(path, "scrcpy.exe"))


def _settings_scrcpy_dir() -> str:
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


def ensure_scrcpy_data_bundle() -> str:
    """Copia scrcpy portable a data/scrcpy si aún no está (para ZIP de descarga)."""
    os.makedirs(DATA_SCRCPY_DIR, exist_ok=True)
    if _dir_has_scrcpy(DATA_SCRCPY_DIR):
        return DATA_SCRCPY_DIR
    src = _settings_scrcpy_dir()
    if not _dir_has_scrcpy(src):
        return DATA_SCRCPY_DIR
    for name in os.listdir(src):
        sp = os.path.join(src, name)
        dp = os.path.join(DATA_SCRCPY_DIR, name)
        if os.path.isdir(sp):
            if os.path.exists(dp):
                shutil.rmtree(dp, ignore_errors=True)
            shutil.copytree(sp, dp)
        else:
            shutil.copy2(sp, dp)
    return DATA_SCRCPY_DIR


def get_scrcpy_dir() -> str:
    if _dir_has_scrcpy(DATA_SCRCPY_DIR):
        return DATA_SCRCPY_DIR
    path = _settings_scrcpy_dir()
    return path if path else ""


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
    data_ready = _dir_has_scrcpy(DATA_SCRCPY_DIR)
    ares_ok = _ares_available()
    return {
        "scrcpy_dir": get_scrcpy_dir() or None,
        "scrcpy_data_dir": DATA_SCRCPY_DIR,
        "scrcpy_data_ready": data_ready,
        "adb": get_adb_path(),
        "scrcpy": get_scrcpy_path(),
        "adb_bundled": get_adb_path().lower().endswith(".exe"),
        "ares": get_ares_path(),
        "ares_ok": ares_ok,
    }
