import json
import re
import subprocess


class LGDriver:
    connection_type = "lg"
    display_name = "LG webOS"
    icon = "📺"

    def __init__(self, ip: str, name: str = "", lgtv_alias: str = ""):
        self.ip = ip
        self.name = name
        self.lgtv_alias = lgtv_alias

    def _alias(self) -> str:
        if self.lgtv_alias:
            return self.lgtv_alias
        safe = re.sub(r"[^a-zA-Z0-9_]", "_", (self.name or "lg").lower())[:30]
        return f"tv_{safe}" if safe else "tv_lg"

    def _target(self) -> str:
        return self.lgtv_alias or self._alias()

    def _run(self, command: str, *, append_target: bool = True):
        cmd = f"lgtv --ssl {command}"
        if append_target:
            cmd += f" {self._target()}"
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30,
            )
            stdout = result.stdout.strip()
            stderr = result.stderr.strip()
            combined = stdout + stderr
            success = result.returncode == 0
            if '"returnValue": true' in combined or "Wrote config" in combined:
                success = True
            return {
                "success": success,
                "message": _friendly_lg(stdout, stderr),
                "stdout": stdout,
                "stderr": result.stderr,
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "message": "Tiempo de espera agotado con la TV LG"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def _run_plain(self, command: str):
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=15,
            )
            return {
                "success": result.returncode == 0,
                "message": result.stdout.strip() or result.stderr.strip(),
                "stdout": result.stdout,
                "stderr": result.stderr,
            }
        except Exception as e:
            return {"success": False, "message": str(e)}

    def auth(self):
        alias = self._alias()
        result = self._run(f"auth {self.ip} {alias}", append_target=False)
        out = (result.get("stdout") or "") + (result.get("stderr") or "")
        if result.get("success") or "Wrote config" in out:
            default_result = self._run_plain(f"lgtv setDefault {alias}")
            result["lgtv_alias"] = alias
            result["message"] = (
                f"Emparejamiento OK. Alias: {alias}. "
                + (default_result.get("message") or "Acepta el popup en la TV si aún no lo hiciste.")
            )
            result["success"] = True
        return result

    def open_browser(self, url: str):
        return self._run(f"openBrowserAt {url}")

    def open_app(self, app_id: str):
        return self._run(f"startApp {app_id}")

    def get_volume(self):
        return self._run("getVolume")

    def set_volume(self, level: int):
        return self._run(f"setVolume {level}")

    def turn_off(self):
        return self._run("off")

    def turn_on(self):
        return self._run(f"on {self.ip}", append_target=False)

    def get_apps(self):
        return self._run("getApps")

    @staticmethod
    def scan_network():
        try:
            result = subprocess.run(
                "lgtv scan",
                shell=True,
                capture_output=True,
                text=True,
                timeout=30,
            )
            output = result.stdout.strip()
            json_match = re.search(r"\{.*\}", output, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                return data
            return {"result": "error", "message": "No se encontraron TVs LG en la red"}
        except Exception as e:
            return {"result": "error", "message": str(e)}


def _friendly_lg(stdout: str, stderr: str) -> str:
    if '"returnValue": true' in stdout:
        return "Comando ejecutado correctamente en la TV LG"
    if "pairing" in stderr.lower() or "pairing" in stdout.lower():
        return "Acepta la solicitud de emparejamiento en la TV"
    if stdout:
        return stdout[:200]
    if stderr:
        return stderr[:200]
    return "Operación LG finalizada"
