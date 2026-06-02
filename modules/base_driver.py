"""Interfaz base para tipos de conexión (LG, Android, futuros)."""
from abc import ABC, abstractmethod


class BaseDeviceDriver(ABC):
    connection_type: str = ""
    display_name: str = ""
    icon: str = ""

    @staticmethod
    @abstractmethod
    def scan_network():
        pass

    def open_url(self, url: str):
        raise NotImplementedError

    def open_app(self, app_id: str):
        raise NotImplementedError
