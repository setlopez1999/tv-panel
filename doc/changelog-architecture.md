# Changelog de arquitectura

Solo cambios **estructurales** (no bugs menores de UI).

## 2026-06-01 — LG ares-cli (IPK / Developer Mode)

**Qué cambió**

- Nuevo [`modules/lg/ares_driver.py`](../modules/lg/ares_driver.py) para `@webos-tools/cli`.
- API `/api/lg/ares/*`: setup, getkey, verify, install-ipk, list-installed, launch, remove.
- `devices.json` LG: campos `ares_device`, `ares_port`, `ares_user`, `ares_linked`, `cached_ares_packages`.
- UI asistente 3 pasos + modal apps IPK en `lg_devices.html` (separado de apps lgtv).
- Health check incluye `ares`.

**Por qué**

- Instalar y gestionar paquetes `.ipk` en LG webOS (flujo Developer Mode del equipo).

**Archivos tocados**

- `modules/lg/ares_driver.py`, `routes/lg.py`, `config.py`, `templates/lg_devices.html`, `tools_paths.py`, `app.py`, `doc/connections/lg-webos.md`

## 2026-06-01 — Drivers + registry + blueprints

**Qué cambió**

- `modules/lg_controller.py` y `modules/android_controller.py` → `modules/lg/driver.py` y `modules/android/driver.py`.
- Nuevo `modules/registry.py` para registrar tipos de conexión.
- Rutas movidas a `routes/lg.py` y `routes/android.py` (Flask blueprints).
- `devices.json`: esquema `connections.{lg,android}` con migración desde `lg_tvs` / `android_devices`.
- Carpeta `doc/` creada con reglas de mantenimiento.

**Por qué**

- Permitir añadir nuevos tipos de dispositivo sin reescribir `app.py`.
- Corregir integración LG (`lgtv`) y preparar documentación viva.

**Archivos tocados**

- `app.py`, `config.py`, `modules/`, `routes/`, `templates/`, `doc/`
