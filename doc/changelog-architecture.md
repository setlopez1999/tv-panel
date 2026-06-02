# Changelog de arquitectura

Solo cambios **estructurales** (no bugs menores de UI).

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
