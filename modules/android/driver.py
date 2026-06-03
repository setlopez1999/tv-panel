import os
import subprocess

from tools_paths import get_adb_path, get_scrcpy_dir, get_scrcpy_path, tools_info


class AndroidDriver:
    connection_type = "android"
    display_name = "Android TV"
    icon = "🤖"

    def __init__(self, ip: str, device_code: str | None = None):
        self.ip = ip
        self.device_code = device_code or f"{ip}:5555"
        self._adb_exe = get_adb_path()
        self._scrcpy_exe = get_scrcpy_path()

    def _run(self, args: list, timeout=120):
        try:
            result = subprocess.run(
                args,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=get_scrcpy_dir() or None,
            )
            ok = result.returncode == 0
            msg = (result.stderr or result.stdout or "").strip()
            if ok:
                msg = msg or "Comando ADB ejecutado correctamente"
            elif "device offline" in msg.lower():
                msg = "Dispositivo offline. Pulsa «Conectar ADB» primero."
            elif "unauthorized" in msg.lower() or "authenticate" in msg.lower():
                msg = "No autorizado. En la TV acepta «Permitir depuración» y pulsa Conectar de nuevo."
            elif "not found" in msg.lower() or "no devices" in msg.lower():
                msg = "Sin dispositivo. Conecta con: adb connect " + self.device_code
            return {
                "success": ok,
                "message": msg[:500],
                "stdout": result.stdout,
                "stderr": result.stderr,
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "message": "Tiempo de espera agotado (ADB)"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def _adb_args(self, *parts: str) -> list:
        return [self._adb_exe, *parts]

    def _adb_device(self, *parts: str) -> list:
        return self._adb_args("-s", self.device_code, *parts)

    def connect(self):
        return self._run(self._adb_args("connect", self.device_code))

    def disconnect(self):
        return self._run(self._adb_args("disconnect", self.device_code))

    @staticmethod
    def list_devices():
        adb = get_adb_path()
        try:
            result = subprocess.run(
                [adb, "devices"],
                capture_output=True,
                text=True,
                timeout=10,
                cwd=get_scrcpy_dir() or None,
            )
            return {
                "success": True,
                "message": result.stdout.strip(),
                "output": result.stdout,
                "tools": tools_info(),
            }
        except Exception as e:
            return {"success": False, "message": str(e)}

    def install_apk(self, apk_path: str):
        apk_path = os.path.abspath(apk_path)
        if not os.path.isfile(apk_path):
            return {"success": False, "message": f"APK no encontrado: {apk_path}"}
        return self._run(
            self._adb_device("install", "-r", apk_path),
            timeout=300,
        )

    def open_url(self, url: str):
        return self._run(
            self._adb_device(
                "shell", "am", "start",
                "-a", "android.intent.action.VIEW",
                "-d", url,
            )
        )

    def open_app(self, package_name: str):
        return self._run(
            self._adb_device(
                "shell", "monkey", "-p", package_name,
                "-c", "android.intent.category.LAUNCHER", "1",
            )
        )

    @staticmethod
    def parse_packages(stdout: str) -> list:
        packages = []
        for line in (stdout or "").splitlines():
            line = line.strip()
            if line.startswith("package:"):
                packages.append(line.split("package:", 1)[1].strip())
        return sorted(set(packages))

    def list_packages(self):
        result = self._run(self._adb_device("shell", "pm", "list", "packages", "-3"))
        packages = self.parse_packages(result.get("stdout", ""))
        result["packages"] = packages
        result["count"] = len(packages)
        if packages:
            result["message"] = f"{len(packages)} aplicaciones encontradas"
        return result

    def uninstall(self, package_name: str):
        return self._run(self._adb_device("uninstall", package_name))

    def push_file(self, local_path: str, remote_path: str):
        local_path = os.path.abspath(local_path)
        if not os.path.isfile(local_path):
            return {"success": False, "message": "Archivo local no encontrado"}
        return self._run(
            self._adb_device("push", local_path, remote_path),
            timeout=300,
        )

    def keyevent(self, key_code: int):
        return self._run(self._adb_device("shell", "input", "keyevent", str(key_code)))

    def input_text(self, text: str):
        safe = text.replace(" ", "%s")
        return self._run(self._adb_device("shell", "input", "text", safe))

    def reboot(self, power_off: bool = False):
        args = self._adb_device("shell", "reboot")
        if power_off:
            args.append("-p")
        return self._run(args)

    def get_screenshot(self) -> str:
        """Captura vía exec-out (evita rutas relativas y corrupción en Windows)."""
        local_tmp = os.path.abspath(f"tmp_screen_{self.ip.replace('.', '_')}.png")
        try:
            result = subprocess.run(
                self._adb_device("exec-out", "screencap", "-p"),
                capture_output=True,
                timeout=30,
            )
            if result.returncode == 0 and result.stdout and len(result.stdout) > 100:
                with open(local_tmp, "wb") as f:
                    f.write(result.stdout)
                return local_tmp
        except Exception:
            pass
        # Fallback: pull clásico con ruta absoluta
        tmp_remote = "/sdcard/tv_panel_screen.png"
        self._run(self._adb_device("shell", "screencap", "-p", tmp_remote))
        self._run(self._adb_device("pull", tmp_remote, local_tmp))
        return local_tmp

    def start_scrcpy(self, on_host: bool = True):
        if not on_host:
            return {
                "success": True,
                "message": "Descarga el .cmd «Abrir en mi PC»",
                "device_code": self.device_code,
            }
        try:
            subprocess.Popen(
                [self._scrcpy_exe, "-s", self.device_code],
                cwd=get_scrcpy_dir() or None,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return {
                "success": True,
                "message": f"scrcpy abierto ({self.device_code}) en este PC",
            }
        except Exception as e:
            return {"success": False, "message": str(e)}

    def launcher_cmd_content(self) -> str:
        adb_q = f'"{self._adb_exe}"'
        scrcpy_q = f'"{self._scrcpy_exe}"'
        return (
            "@echo off\n"
            f"echo Conectando {self.device_code}...\n"
            f"{adb_q} connect {self.device_code}\n"
            f"{scrcpy_q} -s {self.device_code}\n"
            "pause\n"
        )

    @staticmethod
    def scan_network():
        return AndroidDriver.list_devices()
