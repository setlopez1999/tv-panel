from modules.lg.driver import LGDriver
from modules.android.driver import AndroidDriver

CONNECTION_TYPES = {
    "lg": {
        "driver": LGDriver,
        "display_name": LGDriver.display_name,
        "icon": LGDriver.icon,
        "route_prefix": "/lg",
        "api_prefix": "/api/lg",
        "template": "lg_devices.html",
        "list_key": "lg",
    },
    "android": {
        "driver": AndroidDriver,
        "display_name": AndroidDriver.display_name,
        "icon": AndroidDriver.icon,
        "route_prefix": "/android",
        "api_prefix": "/api/android",
        "template": "android_devices.html",
        "list_key": "android",
    },
}


def get_connection_meta(conn_type: str):
    return CONNECTION_TYPES.get(conn_type)


def list_connection_types():
    return [
        {"id": k, "display_name": v["display_name"], "icon": v["icon"], "route": v["route_prefix"]}
        for k, v in CONNECTION_TYPES.items()
    ]
