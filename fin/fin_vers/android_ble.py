"""Связь с BLE на Android через Java-мост."""

from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass

logger = logging.getLogger("tea_mixer.android_ble")
_IMPORT_ERROR: Exception | None = None

# Сначала подключаю pyjnius, чтобы Python мог обращаться к Java.
try:
    from jnius import autoclass
except ImportError as exc:
    autoclass = None  # type: ignore[assignment]
    _IMPORT_ERROR = exc

# Имя Java-класса и состояния Bluetooth-подключения.
JAVA_BRIDGE = "com.tea.mixer.ble.BleBridge"
MAC_RE = re.compile(r"^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$")
STATE_IDLE = 0
STATE_CONNECTING = 1
STATE_DISCOVERING = 2
STATE_CONNECTED = 3
STATE_FAILED = 4


class BleError(Exception):
    pass


# Тут хранится одно найденное BLE-устройство.
@dataclass(frozen=True)
class BleDevice:
    address: str
    name: str


# Проверяю, доступна ли Android BLE-часть.
def available() -> bool:
    return _IMPORT_ERROR is None and autoclass is not None


def error_text() -> str:
    if _IMPORT_ERROR is None:
        return ""
    return f"BLE недоступен: {_IMPORT_ERROR}"


# Получаю Java-класс, который реально работает с Bluetooth.
def _bridge():
    if not available():
        raise BleError(error_text() or "pyjnius не установлен")
    try:
        return autoclass(JAVA_BRIDGE)
    except Exception as exc:
        logger.exception("Java BLE bridge is unavailable")
        raise BleError("Java BLE-мост не найден в APK") from exc


# Проверяю MAC-адрес и привожу его к одному виду.
def normalize_mac(value: str) -> str:
    cleaned = value.strip().upper()
    if not MAC_RE.match(cleaned):
        raise BleError("Неверный MAC-адрес (формат AA:BB:CC:DD:EE:FF)")
    return cleaned


# Перед работой с Bluetooth запрашиваю разрешения Android.
def ensure_permissions(timeout: float = 15.0) -> None:
    bridge = _bridge()
    try:
        if bridge.hasPermissions():
            logger.info("Android Bluetooth permissions already granted")
            return
        logger.info("Requesting Android Bluetooth permissions in Java")
        bridge.requestPermissions()
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if bridge.hasPermissions():
                logger.info("Android Bluetooth permissions granted")
                return
            time.sleep(0.25)
    except Exception as exc:
        logger.exception("Android permission request failed")
        raise BleError(f"Ошибка разрешений Bluetooth: {exc}") from exc
    raise BleError("Разрешите доступ к устройствам поблизости")


# Проверяю, включён ли Bluetooth на телефоне.
def _ensure_adapter() -> None:
    try:
        if not _bridge().isBluetoothEnabled():
            raise BleError("Включите Bluetooth")
    except BleError:
        raise
    except Exception as exc:
        logger.exception("Bluetooth adapter check failed")
        raise BleError(f"Bluetooth недоступен: {exc}") from exc


# Получаю список уже сопряжённых устройств.
def list_paired_devices() -> list[BleDevice]:
    ensure_permissions()
    _ensure_adapter()
    try:
        raw_devices = _bridge().pairedDevices()
        devices = []
        for raw in raw_devices:
            text = str(raw)
            address, separator, name = text.partition("\t")
            if separator:
                devices.append(BleDevice(address=address, name=name or address))
        logger.info("Paired Bluetooth devices received from Java: %d", len(devices))
        return sorted(devices, key=lambda device: device.name.lower())
    except Exception as exc:
        logger.exception("Reading paired devices failed")
        raise BleError(f"Не удалось прочитать устройства: {exc}") from exc


# Один объект этого класса отвечает за одно BLE-подключение.
class BleLink:
    def __init__(self) -> None:
        self.address: str | None = None
        self.name: str | None = None

    @property
    def connected(self) -> bool:
        # Состояние подключения спрашиваю у Java.
        try:
            return _bridge().connectionState() == STATE_CONNECTED
        except Exception:
            return False

    def connect(self, address: str, name: str | None = None, timeout: float = 20.0) -> None:
        # Сначала закрываю старое соединение.
        self.disconnect()
        address = normalize_mac(address)
        ensure_permissions()
        _ensure_adapter()
        bridge = _bridge()
        logger.info("Starting Java GATT connection: %s", address)
        try:
            bridge.connect(address)
            deadline = time.monotonic() + timeout
            while time.monotonic() < deadline:
                # Жду, пока Java закончит подключение.
                state = int(bridge.connectionState())
                if state == STATE_CONNECTED:
                    self.address = address
                    self.name = name or address
                    logger.info("Java GATT connection ready: %s", address)
                    return
                if state == STATE_FAILED:
                    raise BleError(str(bridge.lastError()) or "Ошибка подключения")
                time.sleep(0.1)
        except BleError:
            bridge.disconnect()
            raise
        except Exception as exc:
            logger.exception("Java GATT connection call failed")
            bridge.disconnect()
            raise BleError(f"Ошибка подключения: {exc}") from exc
        bridge.disconnect()
        raise BleError("Таймаут подключения")

    def write(self, data: bytes) -> None:
        # Отправляю данные только если соединение активно.
        if not self.connected:
            raise BleError("Нет подключения")
        try:
            text = data.decode("utf-8")
            if not _bridge().writeUtf8(text):
                detail = str(_bridge().lastError())
                raise BleError(detail or "Не удалось отправить данные")
            time.sleep(0.15)
        except BleError:
            raise
        except Exception as exc:
            logger.exception("Java GATT write failed")
            raise BleError(f"Ошибка отправки: {exc}") from exc

    def disconnect(self) -> None:
        # Закрываю соединение и очищаю данные.
        try:
            _bridge().disconnect()
        except Exception:
            logger.exception("Java GATT disconnect failed")
        self.address = None
        self.name = None
