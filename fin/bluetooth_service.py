from __future__ import annotations

try:
    import serial
    import serial.tools.list_ports
except ImportError:
    serial = None


class BluetoothConnectionError(Exception):
    pass


class ArduinoBluetooth:
    DEFAULT_BAUDRATE = 9600

    def __init__(self) -> None:
        self._connection = None
        self.port: str | None = None

    @staticmethod
    def is_available() -> bool:
        return serial is not None

    def list_ports(self) -> list[str]:
        if not serial:
            return []
        return [port.device for port in serial.tools.list_ports.comports()]

    @property
    def is_connected(self) -> bool:
        return self._connection is not None and self._connection.is_open

    def connect(self, port: str, baudrate: int = DEFAULT_BAUDRATE) -> None:
        if not serial:
            raise BluetoothConnectionError(
                "Установите pyserial: pip install pyserial"
            )
        self.disconnect()
        try:
            self._connection = serial.Serial(port, baudrate, timeout=1)
            self.port = port
        except serial.SerialException as exc:
            raise BluetoothConnectionError(f"Не удалось подключиться: {exc}") from exc

    def disconnect(self) -> None:
        if self._connection and self._connection.is_open:
            self._connection.close()
        self._connection = None
        self.port = None

    def send_mix(self, tea_grams: list[float], sugar_grams: float) -> None:
        if not self.is_connected:
            raise BluetoothConnectionError("Нет подключения к Arduino")
        if len(tea_grams) != 4:
            raise BluetoothConnectionError("Нужно 4 значения веса чая")

        payload = (
            "MIX:"
            + ",".join(f"{g:.2f}" for g in tea_grams)
            + f";SUGAR:{sugar_grams:.2f}\n"
        )
        self._connection.write(payload.encode("utf-8"))
        self._connection.flush()
