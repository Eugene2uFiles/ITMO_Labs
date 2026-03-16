import json
import requests

def info():
    api='9fcfc971a2fb1b49873c059fc34966d2'
    city='Budapest'
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api}&units=metric&lang=ru" 

    try:
        response = requests.get(url)
        response.raise_for_status()

        data = response.json()
        main_data = data.get('main', {})
        temp = main_data.get('temp')
        hum = main_data.get('humidity')
        pres = main_data.get('pressure')
        
        print(f'temperature - {temp}*C')
        print(f'humidity - {hum}%')
        print(f'pressure - {pres} millibars')
        

    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP ошибка: {http_err}")
        print("Ошибка Api ключа или названия города")
    except requests.exceptions.ConnectionError as conn_err:
        print(f"Ошибка соединения: {conn_err}")
    except requests.exceptions.Timeout as timeout_err:
        print(f"Время ожидания истекло: {timeout_err}")
    except json.JSONDecodeError as json_err:
        print(f"Ошибка обработки JSON: {json_err}")
    print("Done!")

info()