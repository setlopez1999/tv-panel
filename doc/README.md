# Documentación — TV Control Panel

Índice de documentación del proyecto. **Léelo antes de cambiar la arquitectura.**

## Archivos

| Archivo | Contenido |
|---------|-----------|
| [architecture.md](architecture.md) | Capas, drivers, flujo de datos |
| [changelog-architecture.md](changelog-architecture.md) | Cambios estructurales (obligatorio actualizar) |
| [notes.md](notes.md) | Notas sueltas, límites, tips NOC |
| [connections/lg-webos.md](connections/lg-webos.md) | Conexión LG webOS (`lgtv`) |
| [connections/android-adb.md](connections/android-adb.md) | Conexión Android (ADB / scrcpy) |

## Reglas de mantenimiento

1. **Cambio de arquitectura** (nuevo driver, rutas, `devices.json`, capas) → entrada fechada en `changelog-architecture.md`.
2. **Cambio de comportamiento de una conexión** → actualizar `connections/<tipo>.md`.
3. **Cambio de carpetas o flujo** → actualizar `architecture.md`.
4. **Apuntes informales** → `notes.md` (no sustituye el changelog).
5. Tras cada cambio grande, revisar que `doc/` coincida con el código.

## Añadir un nuevo tipo de conexión

1. Crear `modules/<tipo>/driver.py` (ver `modules/lg/driver.py` como plantilla).
2. Registrar en `modules/registry.py`.
3. Crear `routes/<tipo>.py` y registrar blueprint en `app.py`.
4. Template `templates/<tipo>_devices.html` y entrada en navbar (automática vía registry).
5. Documentar en `doc/connections/<tipo>.md`.
6. Entrada en `changelog-architecture.md`.
