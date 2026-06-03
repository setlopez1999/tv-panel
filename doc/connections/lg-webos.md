# Conexión: LG webOS

## Herramienta

CLI `lgtv` (paquete [LGWebOSRemote](https://github.com/klattimer/LGWebOSRemote)).

```bash
pip install git+https://github.com/klattimer/LGWebOSRemote.git
```

## Prerrequisitos en la TV

`Settings → General → TV Management → LG Connect Apps → ON`

## Flujo verificado (terminal)

```bash
lgtv scan
# {"result":"ok","count":1,"list":[{"tv_name":"[LG] webOS TV ...","address":"192.168.0.196"}]}

lgtv --ssl auth 192.168.0.196 tv_lg
# Aceptar pairing en la TV

lgtv setDefault tv_lg

lgtv --ssl openBrowserAt https://youtube.com
# {"payload":{"returnValue":true}}
```

## Qué hace el panel

| Acción UI | Comando equivalente |
|-----------|---------------------|
| Escanear red | `lgtv scan` + guardar en `devices.json` |
| Autenticar | `lgtv --ssl auth <IP> <alias>` + `lgtv setDefault <alias>` |
| Abrir URL | `lgtv --ssl openBrowserAt <url> <alias>` |
| Abrir app | `lgtv --ssl startApp <id> <alias>` |
| Apagar | `lgtv --ssl off <alias>` |
| Encender | `lgtv --ssl on <IP>` |

## Campos en `devices.json`

```json
{
  "name": "Sala",
  "ip": "192.168.0.196",
  "lgtv_alias": "tv_sala",
  "uuid": "",
  "status": "unknown"
}
```

## Apps (no es Android APK)

- **Listar / abrir / cerrar** apps: `lgtv --ssl listApps`, `startApp <id>`, `closeApp <id>`.
- Las TVs LG usan **webOS**, no instalan `.apk` de Android.
- Para instalar paquetes propios: LG Content Store o [webOS TV CLI](https://webostv.developer.lge.com/develop/tools/cli-dev-guide) (`ares-install` con `.ipk`).
- Desinstalar apps de usuario: normalmente desde la TV (editar lista de apps) o `ares-install --remove`.

## Troubleshooting

- **Pairing**: pulsar Autenticar y aceptar en la TV.
- **Comando falla**: comprobar `lgtv scan` desde el PC servidor (misma red).
- **Varias TVs**: cada una con alias distinto (`tv_sala`, `tv_recepcion`).
