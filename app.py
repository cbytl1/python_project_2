from flask import Flask, render_template, request
import requests
import json
import random
import socket

api_key = '7hAXZQ5NIBRpmhG9JdFRJ2MAfYCJ6wta'

app = Flask(__name__)

def check_bad_weather(conditions):
    if 0 <= conditions['temp'] <= 35 and conditions['wind'] <= 50 and conditions['rain_chance'] < 50:
        positive_responses = [
            'Погода вполне подходящая!',
            'Можно смело выходить!',
            'Отличный день для прогулки!',
            'На улице супер!'
        ]
        return random.choice(positive_responses)
    else:
        negative_responses = [
            'Погода не очень.',
            'Лучше остаться дома.',
            'На улице плохие условия.',
            'Сегодня не время для прогулок.'
        ]
        return random.choice(negative_responses)


def is_connected():
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=2)
        return True
    except OSError:
        return False


def fetch_location_key(city_name):
    url = f'http://dataservice.accuweather.com/locations/v1/cities/search?apikey={api_key}&q={city_name}'
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return data[0]['Key'] if data else None
    except requests.exceptions.RequestException as ex:
        print(f"Ошибка при запросе данных для города '{city_name}': {ex}")
        return None


def fetch_current_weather(location_id):
    url = f'http://dataservice.accuweather.com/currentconditions/v1/{location_id}?apikey={api_key}&details=true'
    try:
        response = requests.get(url)
        response.raise_for_status()
        weather = response.json()
        return weather[0] if weather else None
    except requests.exceptions.RequestException as ex:
        print(f"Ошибка получения текущей погоды: {ex}")
        return None


def fetch_daily_forecast(location_id):
    url = f"http://dataservice.accuweather.com/forecasts/v1/daily/1day/{location_id}?apikey={api_key}&details=true&metric=true"
    try:
        response = requests.get(url)
        response.raise_for_status()
        forecast = response.json()
        return forecast['DailyForecasts'][0] if 'DailyForecasts' in forecast else None
    except requests.exceptions.RequestException as ex:
        print(f"Ошибка получения прогноза: {ex}")
        return None


def gather_weather_details(city_name):
    loc_key = fetch_location_key(city_name)
    if not loc_key:
        return None
    current_weather = fetch_current_weather(loc_key)
    daily_forecast = fetch_daily_forecast(loc_key)
    if not current_weather or not daily_forecast:
        return None
    rain_probability = daily_forecast['Day'].get('PrecipitationProbability')

    return {
        'temp': current_weather['Temperature']['Metric']['Value'],
        'wind': current_weather['Wind']['Speed']['Metric']['Value'],
        'rain_chance': rain_probability,
        'humidity': current_weather['RelativeHumidity'],
        'status': check_bad_weather({
            'temp': current_weather['Temperature']['Metric']['Value'],
            'wind': current_weather['Wind']['Speed']['Metric']['Value'],
            'rain_chance': rain_probability
        })
    }


@app.route('/', methods=['GET', 'POST'])
def home():
    output = None
    error_msg = None
    if request.method == 'POST':
        first_city = request.form.get('first_city')
        second_city = request.form.get('second_city')
        if not first_city or not second_city:
            error_msg = "Введите названия обоих городов."
        else:
            if not is_connected():
                error_msg = "Нет подключения к интернету. Проверьте сеть."
            else:
                weather_first = gather_weather_details(first_city)
                weather_second = gather_weather_details(second_city)
                with open('weather_first.json', 'w') as file:
                    json.dump(weather_first, file)
                with open('weather_second.json', 'w') as file:
                    json.dump(weather_second, file)
                if weather_first is None:
                    error_msg = f"Не удалось получить данные для города: {first_city}"
                elif weather_second is None:
                    error_msg = f"Не удалось получить данные для города: {second_city}"
                else:
                    output = {
                        'first_city': {'name': first_city, **weather_first},
                        'second_city': {'name': second_city, **weather_second}
                    }
    return render_template('index.html', result=output, error_message=error_msg)


if __name__ == '__main__':
    app.run(debug=True)
