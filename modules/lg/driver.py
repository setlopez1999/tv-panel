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

    def _run(self, command: str, *, use_alias: bool = True, timeout=30):
        target = self._target()
        if use_alias:
            cmd = f'lgtv --ssl -n {target} {command}'
        else:
            cmd = f"lgtv --ssl {command}"
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
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
                "stdout": result.stdout,
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
        result = self._run(f"auth {self.ip} {alias}", use_alias=False)
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

    def close_app(self, app_id: str):
        return self._run(f"closeApp {app_id}")

    def get_volume(self):
        return self._run("getVolume")

    def set_volume(self, level: int):
        return self._run(f"setVolume {level}")

    def turn_off(self):
        return self._run("off")

    def turn_on(self):
        return self._run(f"on {self.ip}", use_alias=False)

    @staticmethod
    def parse_list_apps_output(stdout: str) -> list:
        """Parsea salida NDJSON de `lgtv listApps`."""
        apps = []
        for line in (stdout or "").splitlines():
            line = line.strip()
            if not line.startswith("{"):
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            payload = obj.get("payload") or obj
            raw = payload.get("apps") if isinstance(payload, dict) else None
            if not raw and isinstance(obj.get("apps"), list):
                raw = obj["apps"]
            if not raw:
                continue
            for app in raw:
                if not isinstance(app, dict) or not app.get("id"):
                    continue
                apps.append({
                    "id": app["id"],
                    "title": app.get("title") or app["id"],
                    "removable": bool(app.get("removable", False)),
                    "visible": app.get("visible", True),
                })
            break
        # dedupe by id
        seen = set()
        unique = []
        for a in apps:
            if a["id"] not in seen:
                seen.add(a["id"])
                unique.append(a)
        return sorted(unique, key=lambda x: x["title"].lower())

    def list_apps(self):
        result = self._run("listApps", timeout=60)
        apps = self.parse_list_apps_output(result.get("stdout", ""))
        result["apps"] = apps
        result["count"] = len(apps)
        if apps:
            result["success"] = True
            result["message"] = f"{len(apps)} apps en la TV LG"
        elif not result.get("message"):
            result["message"] = "No se pudo leer la lista. ¿Emparejaste la TV?"
        return result

    def get_apps(self):
        return self.list_apps()

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
                return json.loads(json_match.group())
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
