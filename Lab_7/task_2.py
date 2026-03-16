import json
import requests
import csv


API = '3f568a7e-8954-447b-a379-754072316369'
word = 'kidney'
dictionary = 'medical'  

API_URL = f"https://www.dictionaryapi.com/api/v3/references/{dictionary}/json/{word}?key={API}"
response = requests.get(API_URL)

try:
    response = requests.get(f"{API_URL}")
    data = response.json()[0] 

    result = [ ['word', data['meta']['stems']], 
              ['dictionary', dictionary], 
              ['section',  data['meta']['section']], 
              ['info', data['shortdef'][0]] 
              ]  
    
    with open('dictionary_data.csv', 'w', newline='', encoding='utf-8-sig') as file:
        writer = csv.writer(file, delimiter=';')
        writer.writerow(['Поле', 'Значение'])
        writer.writerows(result)
    
except requests.exceptions.HTTPError as http_err:
    print(f"HTTP ошибка: {http_err}")
    print("Ошибка Api ключа или названия города")
except requests.exceptions.ConnectionError as conn_err:
    print(f"Ошибка соединения: {conn_err}")
except requests.exceptions.Timeout as timeout_err:
    print(f"Время ожидания истекло: {timeout_err}")
except json.JSONDecodeError as json_err:
    print(f"Ошибка обработки JSON: {json_err}")

