"""
Адаптированная версия бота для GitHub Actions
Использует ваш существующий код
"""

import asyncio
import logging
from datetime import datetime
import pytz
import requests
from telegram import Bot
from telegram.error import TelegramError
import os

# ========== КОНФИГУРАЦИЯ ==========
# Берем из переменных окружения GitHub
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
USER_ID = int(os.environ.get("USER_ID", "0"))
OPENWEATHER_API_KEY = os.environ.get("OPENWEATHER_API_KEY", "")
LATITUDE = os.environ.get("LATITUDE", "45.22")
LONGITUDE = os.environ.get("LONGITUDE", "36.72")

# ========== ПРОВЕРКА КОНФИГУРАЦИИ ==========
print("=" * 50)
print("🚀 ЗАПУСК БОТА В GITHUB ACTIONS")
print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 50)

if not all([BOT_TOKEN, USER_ID, OPENWEATHER_API_KEY]):
    print("❌ ОШИБКА: Не все секреты настроены в GitHub!")
    print("   Проверьте BOT_TOKEN, USER_ID, OPENWEATHER_API_KEY")
    exit(1)

print("✅ Конфигурация загружена")
print(f"   User ID: {USER_ID}")
print(f"   Координаты: {LATITUDE}, {LONGITUDE}")

# ========== ВАША СУЩЕСТВУЮЩАЯ ЛОГИКА ==========
# (Скопируем из вашего bot.py)

# URL API OpenWeatherMap
WEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"

def get_weather():
    """Получение погоды с OpenWeatherMap API"""
    try:
        params = {
            'lat': LATITUDE,
            'lon': LONGITUDE,
            'appid': OPENWEATHER_API_KEY,
            'units': 'metric',
            'lang': 'ru'
        }
        
        print("🌤️ Запрашиваем погоду для Тамани...")
        response = requests.get(WEATHER_URL, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        city = data.get('name', 'Тамань')
        temp = data['main']['temp']
        desc = data['weather'][0]['description']
        print(f"✅ Погода получена: {city}, {temp}°C, {desc}")
        return data
        
    except Exception as e:
        print(f"❌ Ошибка получения погоды: {e}")
        return None

def format_weather_message(weather_data):
    """Форматирование сообщения о погоде с графиком"""
    if not weather_data:
        return "⚠️ Не удалось получить данные о погоде. Попробуйте позже."
    
    try:
        # Основные данные
        city = weather_data.get('name', 'Тамань')
        temp = weather_data['main']['temp']
        feels_like = weather_data['main']['feels_like']
        temp_min = weather_data['main']['temp_min']
        temp_max = weather_data['main']['temp_max']
        description = weather_data['weather'][0]['description'].capitalize()
        wind_speed = weather_data['wind']['speed']
        
        # Направление ветра
        wind_deg = weather_data['wind'].get('deg', 0)
        directions = ['северный', 'северо-восточный', 'восточный', 
                     'юго-восточный', 'южный', 'юго-западный', 
                     'западный', 'северо-западный']
        wind_dir = directions[int((wind_deg + 22.5) / 45) % 8] if 'deg' in weather_data['wind'] else ''
        
        # Текущая дата
        moscow_tz = pytz.timezone('Europe/Moscow')
        now = datetime.now(moscow_tz)
        days_ru = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 
                  'Пятница', 'Суббота', 'Воскресенье']
        months_ru = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
                    'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря']
        
        date_str = f"{days_ru[now.weekday()]}, {now.day} {months_ru[now.month-1]} {now.year}"
        
        # Получаем прогноз для графика
        forecast = get_forecast()
        chart = create_chart(forecast)
        
        # Форматирование сообщения
        message = f"""🌅 Доброе утро!

📍 {city}
🗓️ {date_str}
⏰ {now.strftime('%H:%M')}

🌤️ Погода сейчас:
• Состояние: {description}
• Температура: {temp:.0f}°C (ощущается как {feels_like:.0f}°C)
• Ветер: 💨 {wind_speed:.1f} м/с, {wind_dir}
• Днём: от {temp_min:.0f}°C до {temp_max:.0f}°C
"""
        
        # Добавляем график если есть
        if chart:
            message += f"\n{chart}\n"
        
        message += "Хорошего дня! 👋"
        
        return message
        
    except Exception as e:
        print(f"❌ Ошибка создания сообщения: {e}")
        return f"🌤️ Погода в Тамани: {weather_data['main']['temp']:.0f}°C"

async def send_weather_message():
    """Отправка сообщения"""
    try:
        bot = Bot(token=BOT_TOKEN)
        weather_data = get_weather()
        message = format_weather_message(weather_data)
        
        print("📨 Отправляем сообщение в Telegram...")
        await bot.send_message(chat_id=USER_ID, text=message)
        print("✅ Сообщение отправлено успешно!")
        return True
        
    except TelegramError as e:
        print(f"❌ Ошибка Telegram: {e}")
        return False
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        return False

# ========== ЗАПУСК ==========
async def main():
    success = await send_weather_message()
    if success:
        print("🎉 Бот успешно выполнил задание!")
    else:
        print("😢 Бот завершился с ошибкой")
    print("=" * 50)

if __name__ == "__main__":

    asyncio.run(main())
