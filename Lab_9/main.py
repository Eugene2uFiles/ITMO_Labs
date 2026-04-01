from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime
import json
import os

app = Flask(__name__)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
REVIEWS_FILE = os.path.join(BASE_DIR, 'reviews.json')

# Загрузка отзывов из файла
def load_reviews():
    if os.path.exists(REVIEWS_FILE):
        try:
            with open(REVIEWS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, PermissionError):
            return []
    return []

# Сохранение отзывов в файл
def save_reviews(reviews):
    with open(REVIEWS_FILE, 'w', encoding='utf-8') as f:
        json.dump(reviews, f, ensure_ascii=False, indent=2)
    



@app.route('/')
def index():
    reviews = load_reviews()
    reviews = sorted(reviews, key=lambda x: x['date'], reverse=True)
    return render_template('index.html', reviews=reviews)

@app.route('/add_review', methods=['POST'])
def add_review():
    name = request.form.get('name', 'Аноним')
    rating = int(request.form.get('rating', 0))
    text = request.form.get('review', '')
    
    if name and rating and text:
        reviews = load_reviews()
        reviews.append({
            'name': name,
            'rating': rating,
            'text': text,
            'date': datetime.now().strftime('%d.%m.%Y %H:%M')
        })
        if save_reviews(reviews):
            print("Done!")
        else:
            print("Noooo")
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)