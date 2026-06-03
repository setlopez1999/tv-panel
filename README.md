# TV Control Panel - NOC

Panel web local para TVs **LG webOS** y **Android TV**. Sin auth — solo red local.

Docs: [`doc/`](doc/README.md) · Repo: [github.com/setlopez1999/tv-panel](https://github.com/setlopez1999/tv-panel)

## Clonar e iniciar

```powershell
git clone https://github.com/setlopez1999/tv-panel.git
cd tv-panel
pip install -r requirements.txt
pip install git+https://github.com/klattimer/LGWebOSRemote.git
npm install -g @webos-tools/cli
python app.py
```

La consola muestra la URL, ej: `http://192.168.0.53:5000`. Compártela con el equipo (misma red).

`lgtv` (LG remoto). `ares` (LG instalar `.ipk`, Developer Mode). Android: **adb/scrcpy** en `settings.json`. Comprueba: `GET /api/health`.

## Subir cambios

```powershell
git add .
git commit -m "Descripción del cambio"
git push
```

## Cómo probar

### LG webOS

**Control (lgtv):** Escanear → Emparejar lgtv → YouTube web / Apps del sistema.

**Instalar IPK (ares):** En la TV: Developer Mode + Key Server ON. En el panel: Registrar → Passphrase → Verificar → subir `.ipk` → Apps instaladas (IPK).

Requiere `npm install -g @webos-tools/cli`. Ver [`doc/connections/lg-webos.md`](doc/connections/lg-webos.md).

### Android TV

1. En la TV: **ADB over network** ON.
2. En el **inicio** del panel: tipo **Android TV**, nombre + IP → Agregar.
3. **Android TV** → **Conectar ADB** → APK / scrcpy / Home / Atrás / volumen / etc.

Código dispositivo = `IP:5555` (como `adb devices`). Edita ruta tools en `settings.json` si cambias de PC.

## Seguridad

Solo LAN de confianza. No expongas el puerto 5000 a Internet.
