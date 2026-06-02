import os
import subprocess


class AndroidDriver:
    connection_type = "android"
    display_name = "Android TV"
    icon = "🤖"

    def __init__(self, ip: str, device_code: str | None = None):
        self.ip = ip
        self.device_code = device_code or f"{ip}:5555"

    def _adb(self, command: str):
        try:
            result = subprocess.run(
                f"adb {command}",
                shell=True,
                capture_output=True,
                text=True,
                timeout=120,
            )
            ok = result.returncode == 0
            msg = result.stderr.strip() or result.stdout.strip()
            if ok:
                msg = msg or "Comando ADB ejecutado correctamente"
            elif "device offline" in msg.lower():
                msg = "Dispositivo offline. Pulsa «Conectar ADB» primero."
            elif "unauthorized" in msg.lower():
                msg = "No autorizado. Acepta la depuración USB/red en la TV."
            return {
                "success": ok,
                "message": msg[:300],
                "stdout": result.stdout,
                "stderr": result.stderr,
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "message": "Tiempo de espera agotado (ADB)"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def connect(self):
        return self._adb(f"connect {self.device_code}")

    def disconnect(self):
        return self._adb(f"disconnect {self.device_code}")

    def install_apk(self, apk_path: str):
        if not os.path.exists(apk_path):
            return {"success": False, "message": "APK no encontrado en el servidor"}
        return self._adb(f'-s {self.device_code} install -r "{apk_path}"')

    def open_url(self, url: str):
        return self._adb(
            f'-s {self.device_code} shell am start -a android.intent.action.VIEW -d "{url}"'
        )

    def open_app(self, package_name: str):
        return self._adb(
            f"-s {self.device_code} shell monkey -p {package_name} "
            "-c android.intent.category.LAUNCHER 1"
        )

    def get_screenshot(self) -> str:
        tmp_path = "/sdcard/screen.png"
        self._adb(f"-s {self.device_code} shell screencap -p {tmp_path}")
        local_tmp = f"tmp_screen_{self.ip.replace('.', '_')}.png"
        self._adb(f"-s {self.device_code} pull {tmp_path} {local_tmp}")
        return local_tmp

    def reboot(self):
        return self._adb(f"-s {self.device_code} reboot")

    def start_scrcpy(self, on_host: bool = True):
        if not on_host:
            return {
                "success": True,
                "message": "Usa «Abrir en mi PC» o descarga el launcher .cmd (Fase cliente)",
                "device_code": self.device_code,
            }
        try:
            subprocess.Popen(
                f'scrcpy -s {self.device_code}',
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return {
                "success": True,
                "message": "scrcpy abierto en el PC servidor (solo visible ahí)",
            }
        except Exception as e:
            return {"success": False, "message": str(e)}

    @staticmethod
    def list_devices():
        try:
            result = subprocess.run(
                "adb devices",
                shell=True,
                capture_output=True,
                text=True,
                timeout=10,
            )
            return {"success": True, "message": result.stdout.strip(), "output": result.stdout}
        except Exception as e:
            return {"success": False, "message": str(e)}

    @staticmethod
    def scan_network():
        return AndroidDriver.list_devices()

    def launcher_cmd_content(self) -> str:
        return (
            "@echo off\n"
            f"echo Conectando a {self.device_code}...\n"
            f"adb connect {self.device_code}\n"
            f"scrcpy -s {self.device_code}\n"
            "pause\n"
        )
