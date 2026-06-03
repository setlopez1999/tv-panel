# Conexión: Android TV (ADB)

## Herramientas

- `adb` y `scrcpy` — ruta en [`settings.json`](../../settings.json) (`scrcpy_dir`), por defecto bundle scrcpy-win64 en Downloads.
- Si no hay bundle, usa PATH del sistema.

## Prerrequisitos en la TV

`Settings → Device Preferences → About` → 7 clics en Build →  
`Developer Options → ADB debugging` + **ADB over network** ON.

## Código de dispositivo (`device_code`)

Es el identificador que muestra `adb devices`, normalmente:

```
192.168.0.50:5555
```

Uso en terminal:

```bash
adb connect 192.168.0.50:5555
adb -s 192.168.0.50:5555 shell am start -a android.intent.action.VIEW -d "https://youtube.com"
scrcpy -s 192.168.0.50:5555
```

## Qué hace el panel

| Acción UI | Comando equivalente |
|-----------|---------------------|
| Conectar ADB | `adb connect <device_code>` |
| Abrir URL | `adb -s <code> shell am start -a VIEW -d <url>` |
| Instalar APK | `adb -s <code> install -r <apk>` |
| Screenshot | `screencap` + `pull` → imagen en navegador |
| scrcpy (servidor) | `scrcpy -s <code>` en PC anfitrión |
| Abrir en mi PC | Descarga `.cmd` con connect + scrcpy |

## Campos en `devices.json`

```json
{
  "name": "TV Sala",
  "ip": "192.168.0.50",
  "device_code": "192.168.0.50:5555",
  "status": "unknown"
}
```

## Troubleshooting

- **unauthorized**: aceptar depuración en la TV.
- **offline**: pulsar Conectar ADB; revisar firewall y misma red.
- **scrcpy no visible en otro PC**: usar Screenshot o el `.cmd` en el PC del operador.
