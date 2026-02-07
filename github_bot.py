"""
Упрощенный бот - только ежедневная отправка
"""

import os
import asyncio
from datetime import datetime
import pytz
import requests
from telegram import Bot

print("=" * 50)
print("🚀 БОТ ПОГОДЫ (ЕЖЕДНЕВНАЯ ОТПРАВКА)")
print("=" * 50)

# Конфигурация
BOT_TOKEN = os.environ["BOT_TOKEN"]
USER_ID = int(os.environ["USER_ID"])
OPENWEATHER_API_KEY = os.environ["OPENWEATHER_API_KEY"]
LATITUDE = os.environ.get("LATITUDE", "45.22")
LONGITUDE = os.environ.get("LONGITUDE", "36.72")

def get_weather():
    """Получаем текущую погоду"""
    try:
        params = {
            'lat': LATITUDE,
            'lon': LONGITUDE,
            'appid': OPENWEATHER_API_KEY,
            'units': 'metric',
            'lang': 'ru'
        }
        
        print("🌤️ Запрашиваем погоду...")
        response = requests.get(
            "https://api.openweathermap.org/data/2.5/weather",
            params=params,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            city = data.get('name', 'Тамань')
            temp = data['main']['temp']
            print(f"✅ Погода: {city}, {temp}°C")
            return data
        return None
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return None

def get_forecast():
    """Получаем прогноз для графика"""
    try:
        url = "https://api.openweathermap.org/data/2.5/forecast"
        params = {
            'lat': LATITUDE,
            'lon': LONGITUDE,
            'appid': OPENWEATHER_API_KEY,
            'units': 'metric',
            'cnt': 6
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()['list']
        
    except Exception:
        return None

def create_chart(forecast_data):
    """Создает ASCII-график"""
    if not forecast_data or len(forecast_data) < 3:
        return ""
    
    try:
        temps = []
        times = []
        
        for item in forecast_data[:5]:
            temp = item['main']['temp']
            dt = datetime.strptime(item['dt_txt'], "%Y-%m-%d %H:%M:%S")
            time_str = dt.strftime("%H:%M")
            temps.append(temp)
            times.append(time_str)
        
        min_temp = min(temps)
        max_temp = max(temps)
        temp_range = max_temp - min_temp if max_temp != min_temp else 1
        
        chart_lines = ["📈 Температура сегодня:"]
        
        for time_str, temp in zip(times, temps):
            normalized = int(((temp - min_temp) / temp_range) * 10)
            bar = "█" * normalized + "░" * (10 - normalized)
            chart_lines.append(f"{time_str} │{bar} {temp:.0f}°C")
        
        chart_lines.append(f" Min │██ {min_temp:.0f}°C")
        chart_lines.append(f" Max │██████████ {max_temp:.0f}°C")
        
        return "\n".join(chart_lines)
        
    except Exception:
        return ""

def get_wind_direction(degrees):
    """Направление ветра"""
    if degrees is None:
        return ""
    
    directions = ["северный", "северо-восточный", "восточный", "юго-восточный",
                  "южный", "юго-западный", "западный", "северо-западный"]
    return directions[int((degrees + 22.5) / 45) % 8]

async def main():
    """Основная функция"""
    try:
        bot = Bot(token=BOT_TOKEN)
        
        # Получаем данные
        current = get_weather()
        forecast = get_forecast()
        
        if not current:
            await bot.send_message(
                chat_id=USER_ID,
                text="⚠️ Не удалось получить данные о погоде."
            )
            return False
        
        # Формируем сообщение
        city = current.get('name', 'Тамань')
        temp = current['main']['temp']
        feels_like = current['main']['feels_like']
        description = current['weather'][0]['description'].capitalize()
        wind_speed = current['wind']['speed']
        wind_dir = get_wind_direction(current['wind'].get('deg'))
        humidity = current['main']['humidity']
        
        # Дата и время
        moscow_tz = pytz.timezone('Europe/Moscow')
        now = datetime.now(moscow_tz)
        days = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 
                'Пятница', 'Суббота', 'Воскресенье']
        months = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
                 'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря']
        
        date_str = f"{days[now.weekday()]}, {now.day} {months[now.month-1]} {now.year}"
        
        # График
        chart = create_chart(forecast)
        
        # Сообщение
        message = f"""🌅 Доброе утро!

📍 {city}
🗓️ {date_str}
⏰ {now.strftime('%H:%M')}

🌤️ Погода сейчас:
• Состояние: {description}
• Температура: {temp:.0f}°C (ощущается как {feels_like:.0f}°C)
• Ветер: 💨 {wind_speed:.1f} м/с{f', {wind_dir}' if wind_dir else ''}
• Влажность: 💧 {humidity}%
"""
        
        if chart:
            message += f"\n{chart}\n"
        
        message += "\nХорошего дня! 👋"
        
        # Отправляем
        await bot.send_message(chat_id=USER_ID, text=message)
        print("✅ Сообщение отправлено!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    
    if success:
        print("🎉 УСПЕХ!")
    else:
        print("😢 ОШИБКА")
    
    print("=" * 50)
