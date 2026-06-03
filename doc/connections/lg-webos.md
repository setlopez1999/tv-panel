# Conexión: LG webOS

Dos herramientas complementarias:

| Herramienta | Uso |
|-------------|-----|
| **lgtv** (LGWebOSRemote) | URLs, apps del sistema, apagar/encender |
| **ares** (@webos-tools/cli) | Instalar `.ipk`, listar apps instaladas, lanzar, desinstalar |

## lgtv — control remoto

```bash
pip install git+https://github.com/klattimer/LGWebOSRemote.git
```

Prerrequisito TV: `LG Connect Apps` ON.

```bash
lgtv scan
lgtv --ssl auth 192.168.0.196 tv_lg
lgtv setDefault tv_lg
lgtv --ssl -n tv_lg openBrowserAt https://youtube.com
```

## ares — instalar IPK (Developer Mode)

### Instalar CLI en el PC servidor

```bash
npm install -g @webos-tools/cli
ares -V
```

Documentación: [webOS TV CLI](https://webostv.developer.lge.com/develop/tools/cli-installation)

### En la TV (una vez)

1. Instalar app **Developer Mode**
2. Iniciar sesión
3. **Developer Mode** → ON → reiniciar TV
4. Entrar de nuevo → **Key Server** → ON
5. Anotar la **passphrase** que muestra la TV

### Vincular desde el panel (asistente)

1. **Guardar config**: nombre ares (`lgtv_1`), IP, puerto `9922`, usuario `developer`
2. **Registrar en ares** → `ares-setup-device -a ...`
3. Pegar **passphrase** → **Vincular** → `ares-novacom --getkey`
4. **Verificar** → `ares-device -i`

### Comandos equivalentes (terminal)

```bash
ares-setup-device -a lgtv_1 -i "{'username':'developer','host':'192.168.0.196','port':'9922','default':true}"
ares-novacom --getkey -d lgtv_1
# (introducir passphrase de la TV)
ares-device -i -d lgtv_1

ares-install -d lgtv_1 "C:\ruta\app.ipk"
ares-install -d lgtv_1 -l
ares-launch -d lgtv_1 com.waycom.hosted
ares-install -d lgtv_1 --remove com.waycom.hosted
```

### Resumen rápido

```bash
ares-setup-device --list
ares-novacom --getkey -d lgtv_1
ares-device -i lgtv_1
ares-install -d lgtv_1 C:\app.ipk
ares-launch -d lgtv_1 com.ejemplo.hosted
```

## Campos en `devices.json`

```json
{
  "name": "LG Sala",
  "ip": "192.168.0.196",
  "lgtv_alias": "tv_lg_0_0",
  "ares_device": "lgtv_1",
  "ares_port": 9922,
  "ares_user": "developer",
  "ares_linked": true,
  "cached_ares_packages": []
}
```

## No confundir con Android

- **`.apk`** → solo Android TV (ADB)
- **`.ipk`** → LG webOS (ares)

## Troubleshooting

- **ares no encontrado**: `npm install -g @webos-tools/cli` en el PC donde corre Flask
- **getkey falla**: Key Server ON y passphrase correcta en la TV
- **install falla**: TV vinculada (`ares-device -i` OK) y archivo `.ipk` válido
