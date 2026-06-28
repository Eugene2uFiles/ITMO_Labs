import flet as ft
import logging
from pathlib import Path

from app_logging import configure_logging, get_log_path
from bluetooth_service import (
    ArduinoBluetooth,
    BluetoothConnectionError,
    DEFAULT_DEVICE_NAME,
)
from database import TeaDatabase

APP_DIR = Path(__file__).parent
BACKGROUND_IMAGE = APP_DIR / "assets" / "background.png"
MOBILE_WIDTH = 390
MOBILE_HEIGHT = 844
TEXT_PRIMARY = "#2D2D2D"
TEXT_SECONDARY = "#454545"
PANEL_BG = "#F2F8E4"
GREEN_PRIMARY = "#A8D86B"
GREEN_DARK = "#6F9B37"
GREEN_LIGHT = "#E3F0C8"
GREEN_SOFT = "#F8FCF0"
logger = configure_logging()


def get_background_path() -> str:
    if not BACKGROUND_IMAGE.exists():
        raise FileNotFoundError(f"Фоновое изображение не найдено: {BACKGROUND_IMAGE}")
    return str(BACKGROUND_IMAGE)


def apply_background(page: ft.Page) -> None:
    page.bgcolor = ft.Colors.TRANSPARENT
    page.decoration = ft.BoxDecoration(
        image=ft.DecorationImage(
            src=get_background_path(),
            fit=ft.BoxFit.COVER,
            alignment=ft.Alignment.CENTER,
            filter_quality=ft.FilterQuality.HIGH,
        ),
    )


def configure_app_theme(page: ft.Page) -> None:
    page.theme = ft.Theme(
        color_scheme=ft.ColorScheme(
            primary=GREEN_PRIMARY,
            on_primary=GREEN_SOFT,
            primary_container=GREEN_LIGHT,
            on_primary_container=TEXT_PRIMARY,
            secondary=GREEN_DARK,
            on_secondary=GREEN_SOFT,
            surface=PANEL_BG,
            on_surface=TEXT_PRIMARY,
            on_surface_variant=TEXT_SECONDARY,
            surface_container_highest=GREEN_SOFT,
        ),
        text_theme=ft.TextTheme(
            body_large=ft.TextStyle(color=TEXT_PRIMARY),
            body_medium=ft.TextStyle(color=TEXT_PRIMARY),
            body_small=ft.TextStyle(color=TEXT_SECONDARY),
            title_large=ft.TextStyle(color=TEXT_PRIMARY),
            title_medium=ft.TextStyle(color=TEXT_PRIMARY),
            title_small=ft.TextStyle(color=TEXT_PRIMARY),
            headline_large=ft.TextStyle(color=TEXT_PRIMARY),
            headline_medium=ft.TextStyle(color=TEXT_PRIMARY),
            headline_small=ft.TextStyle(color=TEXT_PRIMARY),
            label_large=ft.TextStyle(color=TEXT_PRIMARY),
            label_medium=ft.TextStyle(color=TEXT_SECONDARY),
            label_small=ft.TextStyle(color=TEXT_SECONDARY),
        ),
    )


def configure_mobile_page(page: ft.Page) -> None:
    page.window.width = MOBILE_WIDTH
    page.window.height = MOBILE_HEIGHT
    page.window.min_width = 360
    page.window.min_height = 640
    page.padding = 0
    page.spacing = 12
    page.scroll = ft.ScrollMode.AUTO
    page.horizontal_alignment = ft.CrossAxisAlignment.STRETCH
    page.vertical_alignment = ft.MainAxisAlignment.START


PERCENT_STEP = 10


def round_percent(value: float) -> int:
    return max(0, min(100, int(round(value / PERCENT_STEP) * PERCENT_STEP)))


def split_percent_evenly(count: int, total: int) -> list[int]:
    if count <= 0:
        return []
    base = (total // count // PERCENT_STEP) * PERCENT_STEP
    values = [base] * count
    leftover = total - sum(values)
    index = 0
    while leftover > 0:
        values[index % count] += PERCENT_STEP
        leftover -= PERCENT_STEP
        index += 1
    return values


def redistribute_mix_percentages(
    values: list[int], changed_idx: int, new_value: float
) -> list[int]:
    result = values[:]
    result[changed_idx] = round_percent(new_value)
    others = [i for i in range(len(result)) if i != changed_idx]
    remaining = 100 - result[changed_idx]

    if remaining <= 0:
        result[changed_idx] = 100
        for index in others:
            result[index] = 0
        return result

    others_sum = sum(result[i] for i in others)
    if others_sum == 0:
        distributed = split_percent_evenly(len(others), remaining)
        for index, value in zip(others, distributed):
            result[index] = value
        return result

    raw_shares = [result[i] * remaining / others_sum for i in others]
    floored = [int(share // PERCENT_STEP) * PERCENT_STEP for share in raw_shares]
    for index, value in zip(others, floored):
        result[index] = value

    leftover = remaining - sum(result[i] for i in others)
    remainders = sorted(
        ((raw_shares[i] - floored[i], others[i]) for i in range(len(others))),
        reverse=True,
    )
    guard = 0
    while leftover > 0 and guard < 20:
        for _, index in remainders:
            if leftover <= 0:
                break
            if result[index] + PERCENT_STEP <= 100:
                result[index] += PERCENT_STEP
                leftover -= PERCENT_STEP
        guard += 1

    return result


def main(page: ft.Page):
    logger.info("Flet session started")
    page.on_error = lambda e: logger.error(
        "Flet page error: %s",
        getattr(e, "data", repr(e)),
    )
    try:
        _run_app(page)
    except Exception as exc:
        logger.exception("Application startup failed")
        page.title = "Ошибка запуска"
        page.add(
            ft.SafeArea(
                content=ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Text("Не удалось запустить приложение", size=22, weight=ft.FontWeight.BOLD),
                            ft.Text(str(exc), selectable=True),
                        ],
                        spacing=12,
                    ),
                    padding=16,
                )
            )
        )
        page.update()


def _run_app(page: ft.Page):
    page.title = "Конструктор чайной смеси"
    configure_mobile_page(page)
    configure_app_theme(page)
    apply_background(page)

    user_name = ""
    teas = []
    last_grams: list[float] = []
    last_sugar: float | None = None
    arduino = ArduinoBluetooth()
    db = TeaDatabase()
    saved_profile = db.get_last_profile()
    saved_name = saved_profile["user_name"] if saved_profile else ""
    name_input = ft.TextField(label="Введите ваше имя", value=saved_name)

    # --- Общие UI-хелперы ---

    def show_screen(*controls, on_back=None):
        screen_controls = []
        if on_back is not None:
            screen_controls.append(
                ft.Row(
                    controls=[
                        ft.TextButton(
                            content=ft.Row(
                                controls=[
                                    ft.Icon(ft.Icons.ARROW_BACK, color=GREEN_DARK),
                                    ft.Text("Назад", color=GREEN_DARK),
                                ],
                                tight=True,
                                spacing=4,
                            ),
                            on_click=on_back,
                        )
                    ],
                    alignment=ft.MainAxisAlignment.START,
                )
            )
        screen_controls.extend(controls)
        page.controls.clear()
        page.add(
            ft.SafeArea(
                expand=True,
                content=ft.Container(
                    content=ft.Column(
                        controls=screen_controls,
                        spacing=12,
                        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                    ),
                    padding=16,
                    margin=ft.Margin.symmetric(horizontal=12, vertical=8),
                    border_radius=16,
                    bgcolor=ft.Colors.with_opacity(0.92, PANEL_BG),
                    border=ft.Border.all(1, GREEN_LIGHT),
                ),
            )
        )
        page.update()

    def screen_title(text: str, size: int = 22) -> ft.Text:
        return ft.Text(
            text,
            size=size,
            weight=ft.FontWeight.BOLD,
            text_align=ft.TextAlign.CENTER,
            color=TEXT_PRIMARY,
        )

    def body_text(text: str, size: int = 16, secondary: bool = False) -> ft.Text:
        return ft.Text(
            text,
            size=size,
            text_align=ft.TextAlign.CENTER,
            color=TEXT_SECONDARY if secondary else TEXT_PRIMARY,
        )

    def primary_button(text: str, on_click, disabled: bool = False) -> ft.ElevatedButton:
        return ft.ElevatedButton(
            content=ft.Text(text),
            on_click=on_click,
            height=48,
            disabled=disabled,
        )

    def tea_name_label(name: str) -> ft.Text:
        return ft.Text(
            name,
            size=20,
            weight=ft.FontWeight.BOLD,
            color=TEXT_PRIMARY,
        )

    # --- Экран 1: ввод имени ---

    def next_screen(e):
        nonlocal user_name

        if not name_input.value.strip():
            return

        user_name = name_input.value.strip()
        db.save_user_name(user_name)
        if arduino.is_android():
            show_bluetooth_screen()
        else:
            show_tea_form()

    def show_name_screen():
        logger.info("Opening name screen")
        if user_name:
            name_input.value = user_name

        start_hint = (
            body_text("Загружены сохранённые данные", size=13, secondary=True)
            if saved_profile
            else None
        )

        show_screen(
            screen_title("Конструктор чайной смеси", size=26),
            *([start_hint] if start_hint else []),
            name_input,
            primary_button("Начать", next_screen),
        )

    # --- Экран 2: Bluetooth ---

    def show_bluetooth_screen():
        logger.info("Opening Bluetooth screen; log_file=%s", get_log_path())
        device_dropdown = ft.Dropdown(
            label="Сопряжённые Bluetooth-устройства",
            options=[],
            hint_text="Загрузка списка...",
        )
        mac_field = ft.TextField(
            label="Или MAC-адрес модуля",
            hint_text="AA:BB:CC:DD:EE:FF",
        )
        status = ft.Text(
            "Загрузка списка устройств...",
            text_align=ft.TextAlign.CENTER,
            color=TEXT_SECONDARY,
        )
        continue_btn = primary_button("Продолжить", lambda e: show_tea_form(), disabled=True)
        test_btn = primary_button("Проверить связь", lambda e: None, disabled=True)
        busy = {"value": False}
        devices_cache = {"items": []}

        def set_status(text: str, color=TEXT_PRIMARY) -> None:
            status.value = text
            status.color = color
            page.update()

        def set_busy(on: bool) -> None:
            busy["value"] = on
            refresh_btn.disabled = on
            connect_btn.disabled = on
            test_btn.disabled = on or not arduino.is_connected
            page.update()

        def selected_address() -> str | None:
            if device_dropdown.value:
                return device_dropdown.value
            mac = mac_field.value.strip()
            return mac or None

        def selected_name(address: str) -> str | None:
            for device in devices_cache["items"]:
                if device.address == address:
                    return device.name
            return None

        def apply_devices(devices) -> None:
            devices_cache["items"] = devices
            device_dropdown.options = [
                ft.dropdown.Option(key=d.address, text=d.label) for d in devices
            ]
            device_dropdown.value = ArduinoBluetooth.pick_default(devices)
            if devices:
                set_status(
                    f"Выберите {DEFAULT_DEVICE_NAME} и нажмите «Подключиться».\n"
                    "Если модуля нет — сопрягите его в настройках Bluetooth телефона.",
                    GREEN_DARK,
                )
            else:
                set_status(
                    f"Сопряжённых устройств нет.\n"
                    f"В настройках Bluetooth сопрягите модуль {DEFAULT_DEVICE_NAME} "
                    "или введите MAC ниже.",
                    ft.Colors.ORANGE,
                )

        def load_devices():
            if busy["value"]:
                return
            set_busy(True)
            set_status("Читаю список Bluetooth...", ft.Colors.ORANGE)

            def worker():
                try:
                    logger.info("Loading paired Bluetooth devices")
                    devices = arduino.list_devices()
                except BluetoothConnectionError as exc:
                    logger.exception("Failed to load paired Bluetooth devices")
                    set_status(str(exc), ft.Colors.RED)
                except Exception as exc:
                    logger.exception("Unexpected error while loading Bluetooth devices")
                    set_status(f"Неожиданная ошибка: {exc}", ft.Colors.RED)
                else:
                    logger.info("Loaded %d paired Bluetooth devices", len(devices))
                    apply_devices(devices)
                set_busy(False)

            page.run_thread(worker)

        def connect_click(e):
            address = selected_address()
            if not address:
                set_status("Выберите устройство или введите MAC", ft.Colors.RED)
                return
            set_busy(True)
            set_status("Подключение...", ft.Colors.ORANGE)

            def worker():
                try:
                    logger.info("Connecting to Bluetooth device: %s", address)
                    arduino.connect(address, name=selected_name(address))
                except BluetoothConnectionError as exc:
                    logger.exception("Bluetooth connection failed: %s", address)
                    set_status(str(exc), ft.Colors.RED)
                    continue_btn.disabled = True
                    test_btn.disabled = True
                except Exception as exc:
                    logger.exception("Unexpected Bluetooth connection error: %s", address)
                    set_status(f"Неожиданная ошибка: {exc}", ft.Colors.RED)
                    continue_btn.disabled = True
                    test_btn.disabled = True
                else:
                    logger.info("Bluetooth connected: %s", arduino.port)
                    set_status(f"Подключено: {arduino.port}", GREEN_DARK)
                    continue_btn.disabled = False
                    test_btn.disabled = False
                set_busy(False)

            page.run_thread(worker)

        def test_click(e):
            set_busy(True)
            set_status("Отправка...", ft.Colors.ORANGE)

            def worker():
                try:
                    logger.info("Sending Bluetooth test payload")
                    payload = arduino.send_test()
                except BluetoothConnectionError as exc:
                    logger.exception("Bluetooth test failed")
                    set_status(str(exc), ft.Colors.RED)
                except Exception as exc:
                    logger.exception("Unexpected Bluetooth test error")
                    set_status(f"Неожиданная ошибка: {exc}", ft.Colors.RED)
                else:
                    logger.info("Bluetooth test sent: %s", payload)
                    set_status(
                        f"Отправлено: {payload}\nПроверьте Serial Monitor (9600).",
                        GREEN_DARK,
                    )
                set_busy(False)

            page.run_thread(worker)

        test_btn.on_click = test_click

        def disconnect_click(e):
            logger.info("Disconnect requested")
            arduino.disconnect()
            continue_btn.disabled = True
            test_btn.disabled = True
            set_status("Отключено", ft.Colors.RED)

        def skip_click(e):
            show_tea_form()

        refresh_btn = primary_button("Обновить список", lambda e: load_devices())
        connect_btn = primary_button("Подключиться", connect_click)

        show_screen(
            screen_title(f"{user_name}, подключите Arduino"),
            body_text(
                f"Список сопряжённых устройств Bluetooth. Модуль {DEFAULT_DEVICE_NAME} "
                "должен быть сопряжён в настройках телефона.",
                size=14,
            ),
            device_dropdown,
            mac_field,
            refresh_btn,
            connect_btn,
            test_btn,
            primary_button("Отключиться", disconnect_click),
            status,
            continue_btn,
            ft.TextButton(
                content=ft.Text("Пропустить", color=GREEN_DARK),
                on_click=skip_click,
            ),
            on_back=show_name_screen,
        )

        def initialize_bluetooth():
            logger.info("Bluetooth initialization started")
            set_busy(True)
            set_status("Запрашиваю разрешения Bluetooth...", ft.Colors.ORANGE)
            try:
                arduino.request_permissions()
            except BluetoothConnectionError as exc:
                logger.exception("Bluetooth permission initialization failed")
                set_status(str(exc), ft.Colors.RED)
                set_busy(False)
            except Exception as exc:
                logger.exception("Unexpected Bluetooth initialization error")
                set_status(f"Неожиданная ошибка: {exc}", ft.Colors.RED)
                set_busy(False)
            else:
                logger.info("Bluetooth permissions granted")
                set_busy(False)
                load_devices()

        page.run_thread(initialize_bluetooth)

    # --- Экран 3: названия чаёв ---

    def show_tea_form():
        logger.info("Opening tea form")
        if teas:
            saved_teas = teas
        else:
            profile = db.get_profile(user_name)
            saved_teas = profile["teas"] if profile else ["", "", "", ""]

        tea1 = ft.TextField(label="Название чая №1", value=saved_teas[0])
        tea2 = ft.TextField(label="Название чая №2", value=saved_teas[1])
        tea3 = ft.TextField(label="Название чая №3", value=saved_teas[2])
        tea4 = ft.TextField(label="Название чая №4", value=saved_teas[3])

        def save_teas(e):
            nonlocal teas

            teas = [
                tea1.value.strip(),
                tea2.value.strip(),
                tea3.value.strip(),
                tea4.value.strip(),
            ]

            if any(t == "" for t in teas):
                return

            db.save_profile(user_name, teas)
            show_mix_screen()

        show_screen(
            screen_title(f"Здравствуйте, {user_name}!"),
            body_text("Введите названия четырёх чаёв"),
            tea1,
            tea2,
            tea3,
            tea4,
            primary_button("Продолжить", save_teas),
            on_back=show_bluetooth_screen if arduino.is_android() else show_name_screen,
        )

    # --- Экран 4: настройка смеси ---

    def show_mix_screen():
        logger.info("Opening mix screen")
        total_weight = ft.Slider(
            min=1,
            max=15,
            divisions=14,
            value=5,
            label="{value} г",
        )

        sliders = [
            ft.Slider(min=0, max=100, divisions=10, value=25, label="{value}%")
            for _ in range(4)
        ]
        slider1, slider2, slider3, slider4 = sliders

        percent_summary = ft.Text(
            "Итого: 100%",
            text_align=ft.TextAlign.CENTER,
            weight=ft.FontWeight.W_500,
            color=TEXT_PRIMARY,
        )

        updating_sliders = {"active": False}

        def apply_slider_values(new_values: list[int]) -> None:
            updating_sliders["active"] = True
            for slider, value in zip(sliders, new_values):
                slider.value = value
            percent_summary.value = f"Итого: {sum(new_values)}%"
            updating_sliders["active"] = False

        def on_slider_change(changed_idx: int):
            def handler(e):
                if updating_sliders["active"]:
                    return
                current_values = [round_percent(slider.value) for slider in sliders]
                new_values = redistribute_mix_percentages(
                    current_values,
                    changed_idx,
                    e.control.value,
                )
                apply_slider_values(new_values)
                page.update()

            return handler

        for index, slider in enumerate(sliders):
            slider.on_change = on_slider_change(index)

        sugar_slider = ft.Slider(
            min=0,
            max=5,
            divisions=10,
            value=0,
            label="{value} г",
        )

        result = ft.Text(size=16, text_align=ft.TextAlign.CENTER, color=TEXT_PRIMARY)
        send_status = ft.Text(size=14, text_align=ft.TextAlign.CENTER, color=TEXT_PRIMARY)

        def calculate(e):
            nonlocal last_grams, last_sugar

            total = total_weight.value

            p1 = round_percent(slider1.value)
            p2 = round_percent(slider2.value)
            p3 = round_percent(slider3.value)
            p4 = round_percent(slider4.value)

            total_percent = p1 + p2 + p3 + p4

            if total_percent == 0:
                result.value = "Укажите хотя бы одну пропорцию"
                send_status.value = ""
                page.update()
                return

            g1 = round(total * p1 / total_percent, 2)
            g2 = round(total * p2 / total_percent, 2)
            g3 = round(total * p3 / total_percent, 2)
            g4 = round(total * p4 / total_percent, 2)
            sugar = round(sugar_slider.value, 1)
            last_grams = [g1, g2, g3, g4]
            last_sugar = sugar

            result.value = (
                f"Общий вес смеси: {total} г\n\n"
                f"{teas[0]}: {g1} г ({p1}%)\n"
                f"{teas[1]}: {g2} г ({p2}%)\n"
                f"{teas[2]}: {g3} г ({p3}%)\n"
                f"{teas[3]}: {g4} г ({p4}%)\n\n"
                f"Сахар: {sugar} г"
            )
            send_status.value = ""
            page.update()

        def send_to_arduino(e):
            if not last_grams or last_sugar is None:
                send_status.value = "Сначала рассчитайте смесь"
                send_status.color = ft.Colors.RED
                page.update()
                return

            try:
                payload = arduino.send_mix(last_grams, round(sugar_slider.value, 1))
            except BluetoothConnectionError as exc:
                send_status.value = str(exc)
                send_status.color = ft.Colors.RED
            else:
                send_status.value = f"Отправлено: {payload}"
                send_status.color = GREEN_DARK
            page.update()

        show_screen(
            screen_title("Настрой твое настроение"),
            ft.Divider(height=1, color=TEXT_SECONDARY),
            body_text("Общий вес"),
            total_weight,
            ft.Divider(height=1, color=TEXT_SECONDARY),
            body_text("Доли чая от общего"),
            percent_summary,
            tea_name_label(teas[0]),
            slider1,
            tea_name_label(teas[1]),
            slider2,
            tea_name_label(teas[2]),
            slider3,
            tea_name_label(teas[3]),
            slider4,
            ft.Divider(height=1, color=TEXT_SECONDARY),
            body_text("Сахар (граммы)"),
            sugar_slider,
            primary_button("Рассчитать", calculate),
            result,
            primary_button(
                "Отправить на Arduino",
                send_to_arduino,
                disabled=not arduino.is_connected,
            ),
            send_status,
            on_back=show_tea_form,
        )

    show_name_screen()


ft.run(main)
