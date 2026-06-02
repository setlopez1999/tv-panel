# Notas del proyecto

Apuntes informales (no sustituyen el changelog de arquitectura).

## scrcpy y monitoreo

- **scrcpy en el servidor**: la ventana solo aparece en el PC donde corre `python app.py`.
- **Screenshot en el navegador**: cualquier NOC en la red puede ver la pantalla vía `/api/android/screenshot/<ip>`.
- **Abrir en mi PC**: descarga `scrcpy_<nombre>.cmd` que hace `adb connect` + `scrcpy -s <device_code>`. Requiere adb/scrcpy en el PC del operador.
- El navegador **no puede** lanzar `.exe` directamente por seguridad; hace falta script o protocolo registrado (fase futura: `tvcontrol://`).

## LG webOS

- Tras `auth`, el panel ejecuta `lgtv setDefault <alias>` como en la terminal.
- Config global de lgtv: `%USERPROFILE%/.config/lgtv/config.json` (Windows).

## Red

- Sin auth: usar solo en LAN de confianza.
- Al cambiar de red: actualizar IPs o vaciar `devices.json`.

## Equipo NOC

- Mensajes del log priorizan campo `message` en español.
- Botones rápidos YouTube en tarjetas LG y Android.
