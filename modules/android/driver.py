import os
import subprocess
import time

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
        for attempt in range(5):
            result = self._run(self._adb_args("connect", self.device_code))
            msg = (result.get("message") or "").lower()
            if result.get("success") or "already connected" in msg:
                return result
            if "failed to authenticate" in msg or "unauthorized" in msg or "device offline" in msg:
                if attempt < 4:
                    time.sleep(3)
                    result["message"] = (
                        f"Intento {attempt + 1}/5 — Acepta el popup de depuración en la TV y espera..."
                    )
                    continue
            return result
        return result

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

    @staticmethod
    def _is_valid_png(path: str) -> bool:
        try:
            with open(path, "rb") as f:
                return f.read(8) == b"\x89PNG\r\n\x1a\n"
        except OSError:
            return False

    @staticmethod
    def _fix_png_crlf(path: str) -> None:
        with open(path, "rb") as f:
            data = f.read()
        if not data.startswith(b"\x89PNG") and b"\r\n" in data:
            data = data.replace(b"\r\r\n", b"\n").replace(b"\r\n", b"\n")
            with open(path, "wb") as f:
                f.write(data)

    def get_screenshot(self) -> str:
        """Captura en TV → pull a disco (fiable en Android TV; exec-out a veces devuelve basura)."""
        local_tmp = os.path.abspath(f"tmp_screen_{self.ip.replace('.', '_')}.png")
        tmp_remote = "/sdcard/tv_panel_screen.png"
        self._run(self._adb_device("shell", "screencap", "-p", tmp_remote), timeout=45)
        pull = self._run(self._adb_device("pull", tmp_remote, local_tmp), timeout=60)
        if os.path.isfile(local_tmp):
            self._fix_png_crlf(local_tmp)
            if self._is_valid_png(local_tmp):
                return local_tmp
        # Último intento: exec-out solo si devuelve PNG real
        try:
            result = subprocess.run(
                self._adb_device("exec-out", "screencap", "-p"),
                capture_output=True,
                timeout=30,
                cwd=get_scrcpy_dir() or None,
            )
            if result.returncode == 0 and result.stdout and result.stdout[:8] == b"\x89PNG\r\n\x1a\n":
                with open(local_tmp, "wb") as f:
                    f.write(result.stdout)
                self._fix_png_crlf(local_tmp)
                return local_tmp
        except Exception:
            pass
        if not pull.get("success"):
            return local_tmp
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

    def launcher_cmd_content(self, tools_subdir: str = "tools") -> str:
        """Launcher en raíz del ZIP; bucle de autorización ADB antes de scrcpy."""
        code = self.device_code
        sub = tools_subdir.replace("/", "\\").strip("\\") or "tools"
        return (
            "@echo off\n"
            "setlocal EnableExtensions\n"
            "chcp 65001 >nul\n"
            "cd /d \"%~dp0\"\n"
            f"set \"DEVICE={code}\"\n"
            f"set \"TOOLDIR=%~dp0{sub}\"\n"
            "set \"ADB=%TOOLDIR%\\adb.exe\"\n"
            "set \"SCR=%TOOLDIR%\\scrcpy.exe\"\n"
            "if not exist \"%SCR%\" if exist \"%~dp0scrcpy.exe\" (\n"
            "  set \"TOOLDIR=%~dp0\"\n"
            "  set \"ADB=%~dp0adb.exe\"\n"
            "  set \"SCR=%~dp0scrcpy.exe\"\n"
            ")\n"
            "if not exist \"%SCR%\" (\n"
            "  echo No se encuentra scrcpy.exe en tools\\ ni en la raiz.\n"
            "  echo Extrae el ZIP completo y ejecuta INICIAR_TV.cmd desde la raiz.\n"
            "  pause\n"
            "  exit /b 1\n"
            ")\n"
            "set \"STATUS_FILE=%TEMP%\\tv_panel_adb_%RANDOM%.txt\"\n"
            "\n"
            ":do_connect\n"
            "echo.\n"
            "echo Conectando %DEVICE% ...\n"
            "\"%ADB%\" connect %DEVICE%\n"
            "timeout /t 3 /nobreak >nul\n"
            "goto check_device\n"
            "\n"
            ":force_reset_adb\n"
            "echo.\n"
            "echo Reiniciando ADB en esta PC y reconectando...\n"
            "\"%ADB%\" disconnect %DEVICE% 2>nul\n"
            "\"%ADB%\" kill-server 2>nul\n"
            "timeout /t 2 /nobreak >nul\n"
            "\"%ADB%\" start-server 2>nul\n"
            "timeout /t 1 /nobreak >nul\n"
            "goto do_connect\n"
            "\n"
            ":check_device\n"
            "\"%ADB%\" devices > \"%STATUS_FILE%\"\n"
            "echo.\n"
            "echo --- adb devices ---\n"
            "type \"%STATUS_FILE%\"\n"
            "echo -------------------\n"
            "findstr /C:\"%DEVICE%\" \"%STATUS_FILE%\" | findstr /I \"unauthorized\" >nul\n"
            "if %errorlevel%==0 goto need_tv_auth\n"
            "findstr /C:\"%DEVICE%\" \"%STATUS_FILE%\" | findstr /I \"offline\" >nul\n"
            "if %errorlevel%==0 (\n"
            "  echo Dispositivo offline. Reconectando...\n"
            "  goto force_reset_adb\n"
            ")\n"
            "findstr /C:\"%DEVICE%\" \"%STATUS_FILE%\" | findstr /I \"device\" >nul\n"
            "if %errorlevel%==0 goto launch_scrcpy\n"
            "echo No aparece %DEVICE% en adb devices.\n"
            "goto need_tv_auth\n"
            "\n"
            ":need_tv_auth\n"
            "echo.\n"
            "echo ============================================\n"
            "echo   AUTORIZACION EN LA TV (esta PC nueva)\n"
            "echo ============================================\n"
            "echo   Debe salir popup: Permitir depuracion USB\n"
            "echo.\n"
            "echo   SI NO SALE EL POPUP, en la TV haz ESTO antes de V o R:\n"
            "echo   1. Opciones de desarrollador\n"
            "echo   2. REVOCAR autorizaciones de depuracion USB\n"
            "echo   3. Apaga y enciende \"Depuracion ADB\" y \"ADB por red\"\n"
            "echo   4. Mira la TV unos 10 segundos tras pulsar V\n"
            "echo.\n"
            "echo   V = Forzar reconexion (suele sacar el popup)\n"
            "echo   R = Reintentar comprobacion\n"
            "echo   C = Cancelar\n"
            "echo ============================================\n"
            "set \"OPC=\"\n"
            "set /p OPC=\"Escribe V, R o C y Enter: \"\n"
            "if /i \"%OPC%\"==\"C\" (\n"
            "  echo Cancelado.\n"
            "  del \"%STATUS_FILE%\" 2>nul\n"
            "  exit /b 0\n"
            ")\n"
            "if /i \"%OPC%\"==\"V\" goto force_reset_adb\n"
            "if /i \"%OPC%\"==\"R\" goto do_connect\n"
            "echo Opcion no valida. Usa V, R o C.\n"
            "goto need_tv_auth\n"
            "\n"
            ":launch_scrcpy\n"
            "echo.\n"
            "echo TV autorizada en esta PC. Abriendo scrcpy...\n"
            "del \"%STATUS_FILE%\" 2>nul\n"
            "cd /d \"%TOOLDIR%\"\n"
            "\"%SCR%\" -s %DEVICE%\n"
            "echo.\n"
            "pause\n"
            "endlocal\n"
        )

    @staticmethod
    def scan_network():
        return AndroidDriver.list_devices()
