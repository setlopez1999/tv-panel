"""Empaqueta scrcpy portable + launcher en ZIP o .exe (IExpress en Windows)."""
import os
import re
import shutil
import subprocess
import tempfile
import zipfile
from io import BytesIO

IEXPRESS = os.path.join(os.environ.get("SystemRoot", r"C:\Windows"), "System32", "iexpress.exe")

CMD_NAME = "INICIAR_TV.cmd"
TOOLS_DIR = "tools"


def _safe_filename(name: str) -> str:
    return re.sub(r"[^\w\-]+", "_", name or "android")[:28]


def stage_scrcpy_kit(bundle_dir: str, cmd_name: str, cmd_body: str, readme: str) -> str:
    """
    Estructura del paquete:
      INICIAR_TV.cmd   (raíz — lo único que pulsa el usuario)
      LEEME.txt
      tools/           (adb.exe, scrcpy.exe, DLLs…)
    """
    staging = tempfile.mkdtemp(prefix="tv_scrcpy_kit_")
    tools_dest = os.path.join(staging, TOOLS_DIR)
    os.makedirs(tools_dest, exist_ok=True)
    for root, _dirs, files in os.walk(bundle_dir):
        for fname in files:
            if fname.lower() == "readme.txt":
                continue
            full = os.path.join(root, fname)
            rel = os.path.relpath(full, bundle_dir)
            dest = os.path.join(tools_dest, rel)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            shutil.copy2(full, dest)
    with open(os.path.join(staging, cmd_name), "w", encoding="utf-8", newline="\r\n") as f:
        f.write(cmd_body)
    with open(os.path.join(staging, "LEEME.txt"), "w", encoding="utf-8") as f:
        f.write(readme)
    return staging


def build_zip_bytes(staging: str) -> BytesIO:
    buf = BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, _dirs, files in os.walk(staging):
            for fname in files:
                full = os.path.join(root, fname)
                arc = os.path.relpath(full, staging)
                zf.write(full, arc)
    buf.seek(0)
    return buf


def _sed_escape(path: str) -> str:
    return path.replace("\\", "\\\\")


def build_iexpress_exe(staging: str, cmd_name: str, out_exe: str) -> bool:
    """Crea .exe autoextraíble que ejecuta el .cmd al terminar (solo Windows + IExpress)."""
    if not os.path.isfile(IEXPRESS):
        return False
    out_exe = os.path.abspath(out_exe)
    os.makedirs(os.path.dirname(out_exe), exist_ok=True)
    # Ruta del .sed sin espacios (IExpress /N falla si hay espacios en la ruta del SED)
    sed_dir = tempfile.mkdtemp(prefix="tv_sed_")
    sed_path = os.path.join(sed_dir, "build.sed")
    staging = os.path.abspath(staging)
    app_launch = f'cmd.exe /d /c "{cmd_name}"'

    file_lines = []
    for root, _dirs, files in os.walk(staging):
        for fname in sorted(files):
            rel = os.path.relpath(os.path.join(root, fname), staging)
            file_lines.append(f"{rel}=")

    sed_content = "\r\n".join([
        "[Version]",
        "Class=IEXPRESS",
        "SEDVersion=3",
        "[Options]",
        "PackagePurpose=InstallApp",
        "ShowInstallProgramWindow=1",
        "HideExtractAnimation=1",
        "UseLongFileName=1",
        "InsideCompressed=1",
        "CompressionType=MSZIP",
        "PackageInstallSpace(KB)=80000",
        "InstallPrompt=%InstallPrompt%",
        "DisplayLicense=",
        "FinishMessage=%FinishMessage%",
        "TargetName=%TargetName%",
        "FriendlyName=%FriendlyName%",
        "AppLaunched=%AppLaunched%",
        "PostInstallCmd=<None>",
        "AdminQuietInstCmd=",
        "UserQuietInstCmd=",
        "SourceFiles=SourceFiles",
        "[Strings]",
        "InstallPrompt=",
        "FinishMessage=",
        f"TargetName={out_exe}",
        "FriendlyName=TV Panel Scrcpy",
        f"AppLaunched={app_launch}",
        "[SourceFiles]",
        f"SourceFiles0={staging}",
        "[SourceFiles0]",
        *file_lines,
        "",
    ])
    with open(sed_path, "w", encoding="utf-8", newline="\r\n") as f:
        f.write(sed_content)

    try:
        r = subprocess.run(
            [IEXPRESS, "/N", "/Q", sed_path],
            capture_output=True,
            text=True,
            timeout=300,
        )
        ok = os.path.isfile(out_exe) and os.path.getsize(out_exe) > 10000
        return ok and r.returncode == 0
    except Exception:
        return False
    finally:
        try:
            shutil.rmtree(sed_dir, ignore_errors=True)
        except OSError:
            pass


def cleanup_staging(staging: str) -> None:
    try:
        shutil.rmtree(staging, ignore_errors=True)
    except OSError:
        pass


def kit_readme(cmd_name: str, device_code: str, exe_mode: bool) -> str:
    if exe_mode:
        return (
            "TV Control Panel — visor scrcpy\n\n"
            "1. Doble clic en este .exe\n"
            "2. Si Windows avisa: «Más información» → «Ejecutar de todos modos»\n"
            "3. Si el antivirus lo bloquea: descarga el ZIP del panel y usa INICIAR_TV.cmd\n\n"
            f"Dispositivo: {device_code}\n"
        )
    return (
        "TV Control Panel — visor scrcpy (recomendado si el antivirus bloquea el .exe)\n\n"
        "1. Clic derecho en el ZIP → Extraer todo\n"
        f"2. Doble clic en {cmd_name} (en la raíz, junto a la carpeta tools)\n"
        "3. Acepta depuración ADB en la TV si pide\n\n"
        f"Dispositivo: {device_code}\n"
    )


def build_kit_exe_cached(
    bundle_dir: str,
    cache_exe: str,
    cmd_name: str,
    cmd_body: str,
    readme: str,
) -> tuple[bool, str]:
    """Devuelve (ok, mensaje_error). Usa caché si el bundle no cambió."""
    bundle_stamp = _dir_mtime(bundle_dir)
    if os.path.isfile(cache_exe) and os.path.getmtime(cache_exe) >= bundle_stamp:
        return True, ""

    staging = stage_scrcpy_kit(bundle_dir, cmd_name, cmd_body, readme)
    try:
        os.makedirs(os.path.dirname(cache_exe), exist_ok=True)
        if build_iexpress_exe(staging, cmd_name, cache_exe):
            return True, ""
        return False, "No se pudo crear el .exe (IExpress). Usa la descarga ZIP."
    finally:
        cleanup_staging(staging)


def _dir_mtime(path: str) -> float:
    latest = 0.0
    for root, _dirs, files in os.walk(path):
        for fname in files:
            try:
                latest = max(latest, os.path.getmtime(os.path.join(root, fname)))
            except OSError:
                pass
    return latest
