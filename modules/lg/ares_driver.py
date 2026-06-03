"""Wrapper para webOS TV CLI (@webos-tools/cli)."""
import os
import re
import shutil
import subprocess


def get_ares_cmd(name: str) -> str:
    """ares, ares-install, ares-setup-device, etc."""
    path = shutil.which(name)
    return path or name


def ares_available() -> bool:
    try:
        r = subprocess.run(
            [get_ares_cmd("ares"), "-V"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return r.returncode == 0 and bool(r.stdout.strip())
    except Exception:
        return False


def ares_version() -> str:
    try:
        r = subprocess.run(
            [get_ares_cmd("ares"), "-V"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return (r.stdout or r.stderr or "").strip()
    except Exception as e:
        return str(e)


class AresDriver:
    def __init__(self, device_name: str):
        self.device = device_name

    def _run(self, cmd_parts: list, *, input_text: str = None, timeout=120):
        try:
            result = subprocess.run(
                cmd_parts,
                capture_output=True,
                text=True,
                timeout=timeout,
                input=input_text,
            )
            stdout = (result.stdout or "").strip()
            stderr = (result.stderr or "").strip()
            ok = result.returncode == 0
            msg = stderr or stdout or ("OK" if ok else "Error en comando ares")
            if ok and not msg:
                msg = "Comando ares ejecutado correctamente"
            return {
                "success": ok,
                "message": msg[:500],
                "stdout": result.stdout,
                "stderr": result.stderr,
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "message": "Tiempo de espera agotado (ares)"}
        except FileNotFoundError:
            return {
                "success": False,
                "message": "ares no encontrado. Ejecuta: npm install -g @webos-tools/cli",
            }
        except Exception as e:
            return {"success": False, "message": str(e)}

    @staticmethod
    def check_cli():
        return {
            "success": ares_available(),
            "message": ares_version() if ares_available() else "Instala: npm install -g @webos-tools/cli",
            "version": ares_version(),
        }

    @staticmethod
    def list_devices():
        return AresDriver("_")._run([get_ares_cmd("ares-setup-device"), "--list"], timeout=30)

    def setup_device(self, ip: str, port: int = 9922, user: str = "developer", description: str = ""):
        """Registra dispositivo vía ares-setup-device -a -i (no interactivo)."""
        desc = (description or f"TV panel {ip}").replace("'", "")
        info = (
            f"{{'username':'{user}', 'host':'{ip}', 'port':'{port}', "
            f"'description':'{desc}', 'default':true}}"
        )
        result = self._run(
            [
                get_ares_cmd("ares-setup-device"),
                "-a",
                self.device,
                "-i",
                info,
            ],
            timeout=60,
        )
        if result.get("success"):
            self._run([get_ares_cmd("ares-setup-device"), "-f", self.device], timeout=15)
        return result

    def get_key(self, passphrase: str):
        if not passphrase or not passphrase.strip():
            return {"success": False, "message": "Escribe la passphrase que muestra la TV"}
        return self._run(
            [get_ares_cmd("ares-novacom"), "--getkey", "-d", self.device],
            input_text=passphrase.strip() + "\n",
            timeout=60,
        )

    def device_info(self):
        result = self._run(
            [get_ares_cmd("ares-device"), "-i", "-d", self.device],
            timeout=30,
        )
        linked = result.get("success", False) or "modelName" in (result.get("stdout") or "")
        if "password" in (result.get("stderr") or "").lower():
            linked = False
            result["message"] = "TV no vinculada. Repite getkey con la passphrase de la TV."
        result["linked"] = linked
        return result

    def install_ipk(self, ipk_path: str):
        ipk_path = os.path.abspath(ipk_path)
        if not os.path.isfile(ipk_path):
            return {"success": False, "message": f"IPK no encontrado: {ipk_path}"}
        if not ipk_path.lower().endswith(".ipk"):
            return {"success": False, "message": "El archivo debe tener extensión .ipk"}
        return self._run(
            [get_ares_cmd("ares-install"), "-d", self.device, ipk_path],
            timeout=300,
        )

    @staticmethod
    def parse_installed_list(stdout: str) -> list:
        packages = []
        for line in (stdout or "").splitlines():
            line = line.strip()
            if not line:
                continue
            # com.package.id or "id": "com..."
            m = re.search(r"(com\.[a-zA-Z0-9_.]+)", line)
            if m:
                pkg = m.group(1)
                title = line
                if pkg not in [p["id"] for p in packages]:
                    packages.append({"id": pkg, "title": title[:80]})
        return sorted(packages, key=lambda x: x["id"])

    def list_installed(self):
        result = self._run(
            [get_ares_cmd("ares-install"), "-d", self.device, "-l"],
            timeout=60,
        )
        packages = self.parse_installed_list(result.get("stdout", ""))
        result["packages"] = packages
        result["count"] = len(packages)
        if packages:
            result["success"] = True
            result["message"] = f"{len(packages)} app(s) instaladas vía ares"
        return result

    def launch(self, package_id: str):
        return self._run(
            [get_ares_cmd("ares-launch"), "-d", self.device, package_id],
            timeout=30,
        )

    def remove(self, package_id: str):
        return self._run(
            [
                get_ares_cmd("ares-install"),
                "-d",
                self.device,
                "--remove",
                package_id,
            ],
            timeout=120,
        )
