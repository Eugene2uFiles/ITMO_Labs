import flet as ft


def main(page: ft.Page):
    page.title = "Конструктор чайной смеси"
    page.padding = 20

    user_name = ""
    teas = []

    def show_mix_screen():
        total_weight = ft.Slider(
            min=1,
            max=15,
            divisions=14,
            value=5,
        )

        slider1 = ft.Slider(min=0, max=100, value=25)
        slider2 = ft.Slider(min=0, max=100, value=25)
        slider3 = ft.Slider(min=0, max=100, value=25)
        slider4 = ft.Slider(min=0, max=100, value=25)

        result = ft.Text(size=18)

        def calculate(e):
            total = total_weight.value

            p1 = slider1.value
            p2 = slider2.value
            p3 = slider3.value
            p4 = slider4.value

            total_percent = p1 + p2 + p3 + p4

            if total_percent == 0:
                result.value = "Укажите хотя бы одну пропорцию"
                page.update()
                return

            g1 = round(total * p1 / total_percent, 2)
            g2 = round(total * p2 / total_percent, 2)
            g3 = round(total * p3 / total_percent, 2)
            g4 = round(total * p4 / total_percent, 2)

            result.value = (
                f"Общий вес смеси: {total} г\n\n"
                f"{teas[0]}: {g1} г\n"
                f"{teas[1]}: {g2} г\n"
                f"{teas[2]}: {g3} г\n"
                f"{teas[3]}: {g4} г"
            )

            page.update()

        page.controls.clear()

        page.add(
            ft.Text(
                f"{user_name}, настройте вашу смесь",
                size=24,
                weight=ft.FontWeight.BOLD,
            ),

            ft.Divider(),

            ft.Text("Общий вес смеси (граммы)"),
            total_weight,

            ft.Divider(),

            ft.Text(teas[0]),
            slider1,

            ft.Text(teas[1]),
            slider2,

            ft.Text(teas[2]),
            slider3,

            ft.Text(teas[3]),
            slider4,

            ft.ElevatedButton(
                content=ft.Text("Рассчитать"),
                on_click=calculate
            ),

            result
        )

        page.update()

    def show_tea_form():
        tea1 = ft.TextField(label="Название чая №1")
        tea2 = ft.TextField(label="Название чая №2")
        tea3 = ft.TextField(label="Название чая №3")
        tea4 = ft.TextField(label="Название чая №4")

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

            show_mix_screen()

        page.controls.clear()

        page.add(
            ft.Text(
                f"Здравствуйте, {user_name}!",
                size=24,
                weight=ft.FontWeight.BOLD,
            ),

            ft.Text("Введите названия четырёх чаёв"),

            tea1,
            tea2,
            tea3,
            tea4,

            ft.ElevatedButton(
                content=ft.Text("Продолжить"),
                on_click=save_teas
            )
        )

        page.update()

    name_input = ft.TextField(
        label="Введите ваше имя",
        width=300
    )

    def next_screen(e):
        nonlocal user_name

        if not name_input.value.strip():
            return

        user_name = name_input.value.strip()

        show_tea_form()

    page.add(
        ft.Text(
            "Конструктор чайной смеси",
            size=30,
            weight=ft.FontWeight.BOLD,
        ),

        name_input,

        ft.ElevatedButton(
            content=ft.Text("Начать"),
            on_click=next_screen
        )
    )

    page.update()

ft.app(target=main)
