"""Bluetooth для Arduino: список сопряжённых устройств + прямое BLE-подключение."""

from __future__ import annotations

import os
import logging
from dataclasses import dataclass

try:
    import android_ble
except ImportError:
    android_ble = None  # type: ignore[assignment]

DEFAULT_DEVICE_NAME = "ION"
logger = logging.getLogger("tea_mixer.bluetooth_service")


class BluetoothConnectionError(Exception):
    pass


@dataclass(frozen=True)
class BluetoothDevice:
    address: str
    name: str

    @property
    def label(self) -> str:
        marker = " ★" if DEFAULT_DEVICE_NAME.lower() in self.name.lower() else ""
        return f"{self.name} ({self.address}){marker}"


def _mix_line(tea_grams: list[float], sugar_grams: float) -> str:
    return (
        "MIX:"
        + ",".join(f"{g:.2f}" for g in tea_grams)
        + f";SUGAR:{sugar_grams:.2f}\n"
    )


class ArduinoBluetooth:
    def __init__(self) -> None:
        self._link: android_ble.BleLink | None = None

    @staticmethod
    def is_android() -> bool:
        return os.getenv("FLET_PLATFORM") == "android"

    @property
    def is_connected(self) -> bool:
        return self._link is not None and self._link.connected

    @property
    def port(self) -> str | None:
        if self._link is None or not self._link.connected:
            return None
        if self._link.name:
            return f"{self._link.name} ({self._link.address})"
        return self._link.address

    def _require_android(self) -> None:
        if not self.is_android():
            raise BluetoothConnectionError("Bluetooth работает только на Android")
        if android_ble is None or not android_ble.available():
            detail = android_ble.error_text() if android_ble else ""
            raise BluetoothConnectionError(detail or "Bluetooth недоступен")

    def request_permissions(self) -> None:
        logger.info("Requesting Bluetooth permissions")
        self._require_android()
        try:
            android_ble.ensure_permissions()
        except Exception as exc:
            logger.exception("Bluetooth permission request failed")
            raise BluetoothConnectionError(str(exc)) from exc

    def list_devices(self) -> list[BluetoothDevice]:
        logger.info("Listing paired Bluetooth devices")
        self._require_android()
        try:
            found = android_ble.list_paired_devices()
        except Exception as exc:
            logger.exception("Listing Bluetooth devices failed")
            raise BluetoothConnectionError(str(exc)) from exc
        devices = [BluetoothDevice(address=d.address, name=d.name) for d in found]
        preferred = [d for d in devices if DEFAULT_DEVICE_NAME.lower() in d.name.lower()]
        others = [d for d in devices if d not in preferred]
        return preferred + sorted(others, key=lambda d: d.name.lower())

    @staticmethod
    def pick_default(devices: list[BluetoothDevice]) -> str | None:
        if not devices:
            return None
        for device in devices:
            if DEFAULT_DEVICE_NAME.lower() in device.name.lower():
                return device.address
        return devices[0].address

    def connect(self, address: str, name: str | None = None) -> None:
        logger.info("Connecting Bluetooth service: address=%s, name=%s", address, name)
        self._require_android()
        if self._link is not None:
            logger.info("Closing previous Bluetooth link before reconnecting")
            self._link.disconnect()
            self._link = None
        link = android_ble.BleLink()
        try:
            link.connect(address, name=name)
        except Exception as exc:
            logger.exception("Bluetooth service connection failed")
            raise BluetoothConnectionError(str(exc)) from exc
        self._link = link
        logger.info(
            "Bluetooth link stored: connected=%s, address=%s, name=%s",
            self._link.connected,
            self._link.address,
            self._link.name,
        )

    def disconnect(self) -> None:
        logger.info("Disconnecting Bluetooth service")
        if self._link is not None:
            self._link.disconnect()
            self._link = None

    def send_line(self, line: str) -> None:
        if not self.is_connected or self._link is None:
            raise BluetoothConnectionError("Сначала подключитесь к модулю")
        payload = line.rstrip("\r\n").encode("utf-8") + b"\n"
        try:
            logger.debug("Sending Bluetooth line: %s", line.rstrip())
            self._link.write(payload)
        except Exception as exc:
            logger.exception("Bluetooth write failed")
            raise BluetoothConnectionError(str(exc)) from exc

    def send_mix(self, tea_grams: list[float], sugar_grams: float) -> str:
        if len(tea_grams) != 4:
            raise BluetoothConnectionError("Нужно 4 значения чая")
        line = _mix_line(tea_grams, sugar_grams)
        self.send_line(line)
        return line.strip()

    def send_test(self) -> str:
        return self.send_mix([1.0, 1.0, 1.0, 1.0], 0.0)
