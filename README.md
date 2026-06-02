# TV Control Panel - NOC

Panel web local para TVs **LG webOS** y **Android TV**. Sin auth — solo red local.

Docs: [`doc/`](doc/README.md) · Repo: [github.com/setlopez1999/tv-panel](https://github.com/setlopez1999/tv-panel)

## Clonar e iniciar

```powershell
git clone https://github.com/setlopez1999/tv-panel.git
cd tv-panel
pip install -r requirements.txt
pip install git+https://github.com/klattimer/LGWebOSRemote.git
python app.py
```

La consola muestra la URL, ej: `http://192.168.0.53:5000`. Compártela con el equipo (misma red).

Requisitos en PATH: `lgtv`, `adb`, `scrcpy` (Android). Comprueba con `GET /api/health`.

## Subir cambios

```powershell
git add .
git commit -m "Descripción del cambio"
git push
```

## Cómo probar

### LG webOS

1. Abre **LG webOS** en el panel.
2. **Escanear red y guardar** (o agrega IP manual).
3. **Autenticar** → acepta el popup en la TV.
4. Pulsa **▶ YouTube** o **Abrir URL**.

Si falla, prueba en terminal: `lgtv scan` y `lgtv --ssl openBrowserAt https://youtube.com`.

### Android TV

1. En la TV: activa **ADB over network** (puerto 5555).
2. Abre **Android TV** en el panel → agrega **IP** y código **`IP:5555`**.
3. **Conectar ADB** → **▶ YouTube** o **Instalar APK**.
4. **Ver pantalla**: screenshot en el navegador, o **Abrir en mi PC (.cmd)** si tienes adb/scrcpy instalados.

Si falla: `adb connect 192.168.x.x:5555` en el PC servidor.

## Seguridad

Solo LAN de confianza. No expongas el puerto 5000 a Internet.
