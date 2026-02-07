"""
Телеграм-бот "Утренняя метеосводка с графиком"
Отправляет погоду каждый день в 08:00 по МСК с графиком температуры
"""

import os
import asyncio
from datetime import datetime
import pytz
import requests
from telegram import Bot

print("=" * 50)
print("🚀 БОТ ПОГОДЫ С ГРАФИКОМ ЗАПУЩЕН")
print("=" * 50)

# ========== КОНФИГУРАЦИЯ ==========
# Берем из переменных окружения GitHub
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
USER_ID = int(os.environ.get("USER_ID", "0"))
OPENWEATHER_API_KEY = os.environ.get("OPENWEATHER_API_KEY", "")
LATITUDE = os.environ.get("LATITUDE", "45.22")
LONGITUDE = os.environ.get("LONGITUDE", "36.72")

# ========== ПРОВЕРКА КОНФИГУРАЦИИ ==========
if not all([BOT_TOKEN, USER_ID, OPENWEATHER_API_KEY]):
    print("❌ ОШИБКА: Не все секреты настроены в GitHub!")
    print("   Проверьте BOT_TOKEN, USER_ID, OPENWEATHER_API_KEY")
    exit(1)

print("✅ Конфигурация загружена")
print(f"   Координаты: {LATITUDE}, {LONGITUDE}")

# ========== ФУНКЦИИ ДЛЯ ПОЛУЧЕНИЯ ДАННЫХ ==========
def get_current_weather():
    """Получаем текущую погоду"""
    try:
        params = {
            'lat': LATITUDE,
            'lon': LONGITUDE,
            'appid': OPENWEATHER_API_KEY,
            'units': 'metric',
            'lang': 'ru'
        }
        
        print("🌤️ Запрашиваем текущую погоду...")
        response = requests.get(
            "https://api.openweathermap.org/data/2.5/weather",
            params=params,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            city = data.get('name', 'Тамань')
            temp = data['main']['temp']
            print(f"✅ Текущая погода: {city}, {temp}°C")
            return data
        else:
            print(f"❌ Ошибка API: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Ошибка получения погоды: {e}")
        return None

def get_forecast():
    """Получаем прогноз на день для графика"""
    try:
        url = "https://api.openweathermap.org/data/2.5/forecast"
        params = {
            'lat': LATITUDE,
            'lon': LONGITUDE,
            'appid': OPENWEATHER_API_KEY,
            'units': 'metric',
            'cnt': 6  # 6 точек = 18 часов прогноза
        }
        
        print("📊 Запрашиваем прогноз для графика...")
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        print(f"✅ Прогноз получен: {len(data['list'])} точек")
        return data['list']
        
    except Exception as e:
        print(f"⚠️ Прогноз не получен (будет только текущая погода): {e}")
        return None

def create_temperature_chart(forecast_data):
    """Создает ASCII-график температуры"""
    if not forecast_data or len(forecast_data) < 3:
        return ""
    
    try:
        # Берем 5 точек через равные интервалы
        temps = []
        times = []
        
        for i, item in enumerate(forecast_data[:5]):
            temp = item['main']['temp']
            # Преобразуем время из "2024-11-20 09:00:00" в "09:00"
            dt = datetime.strptime(item['dt_txt'], "%Y-%m-%d %H:%M:%S")
            time_str = dt.strftime("%H:%M")
            temps.append(temp)
            times.append(time_str)
        
        # Рассчитываем график
        min_temp = min(temps)
        max_temp = max(temps)
        temp_range = max_temp - min_temp
        
        if temp_range == 0:
            temp_range = 1  # избегаем деления на ноль
        
        # Создаем строки графика
        chart_lines = []
        chart_lines.append("📈 Температура сегодня:")
        
        for time_str, temp in zip(times, temps):
            # Нормализуем от 0 до 10
            normalized = int(((temp - min_temp) / temp_range) * 10)
            bar = "█" * normalized + "░" * (10 - normalized)
            chart_lines.append(f"{time_str} │{bar} {temp:.0f}°C")
        
        # Добавляем min и max
        chart_lines.append(f" Min │██ {min_temp:.0f}°C")
        chart_lines.append(f" Max │██████████ {max_temp:.0f}°C")
        
        return "\n".join(chart_lines)
        
    except Exception as e:
        print(f"❌ Ошибка создания графика: {e}")
        return ""

def get_wind_direction(degrees):
    """Преобразует градусы в направление ветра"""
    if degrees is None:
        return ""
    
    directions = [
        "северный", "северо-восточный", "восточный", "юго-восточный",
        "южный", "юго-западный", "западный", "северо-западный"
    ]
    
    index = int((degrees + 22.5) / 45) % 8
    return directions[index]

# ========== СОЗДАНИЕ СООБЩЕНИЯ ==========
def create_weather_message(current_data, forecast_data):
    """Создает полное сообщение с графиком"""
    if not current_data:
        return "⚠️ Не удалось получить данные о погоде. Попробуйте позже."
    
    try:
        # Основные данные
        city = current_data.get('name', 'Тамань')
        temp = current_data['main']['temp']
        feels_like = current_data['main']['feels_like']
        temp_min = current_data['main']['temp_min']
        temp_max = current_data['main']['temp_max']
        humidity = current_data['main']['humidity']
        pressure = current_data['main']['pressure'] * 0.750062  # в мм рт.ст.
        description = current_data['weather'][0]['description'].capitalize()
        wind_speed = current_data['wind']['speed']
        wind_deg = current_data['wind'].get('deg')
        
        # Направление ветра
        wind_dir = get_wind_direction(wind_deg)
        
        # Текущая дата и время
        moscow_tz = pytz.timezone('Europe/Moscow')
        now = datetime.now(moscow_tz)
        
        # Русские названия
        days = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 
                'Пятница', 'Суббота', 'Воскресенье']
        months = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
                 'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря']
        
        date_str = f"{days[now.weekday()]}, {now.day} {months[now.month-1]} {now.year}"
        
        # Создаем график
        chart = create_temperature_chart(forecast_data)
        
        # Форматируем сообщение
        message = f"""🌅 Доброе утро!

📍 {city}
🗓️ {date_str}
⏰ {now.strftime('%H:%M')}

🌤️ Погода сейчас:
• Состояние: {description}
• Температура: {temp:.0f}°C (ощущается как {feels_like:.0f}°C)
• Ветер: 💨 {wind_speed:.1f} м/с{f', {wind_dir}' if wind_dir else ''}
• Влажность: 💧 {humidity}%
• Давление: ⏱️ {pressure:.0f} мм рт.ст.
• Днём: от {temp_min:.0f}°C до {temp_max:.0f}°C
"""
        
        # Добавляем график если есть
        if chart:
            message += f"\n{chart}\n"
        
        message += "\nХорошего дня! 👋"
        
        return message
        
    except Exception as e:
        print(f"❌ Ошибка создания сообщения: {e}")
        # Фолбэк на простое сообщение
        return f"""🌤️ Погода в Тамани: {current_data['main']['temp']:.0f}°C
{current_data['weather'][0]['description'].capitalize()}"""

# ========== ОСНОВНАЯ ФУНКЦИЯ ==========
async def send_weather():
    """Основная функция отправки"""
    try:
        bot = Bot(token=BOT_TOKEN)
        
        # Получаем данные
        print("📡 Получаем данные о погоде...")
        current = get_current_weather()
        forecast = get_forecast()
        
        if not current:
            await bot.send_message(
                chat_id=USER_ID,
                text="⚠️ Не удалось получить данные о погоде. Попробуйте позже."
            )
            return False
        
        # Создаем сообщение
        message = create_weather_message(current, forecast)
        
        # Отправляем
        print("📨 Отправляем сообщение в Telegram...")
        await bot.send_message(chat_id=USER_ID, text=message)
        print("✅ Сообщение с графиком отправлено!")
        return True
        
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        return False

# ========== ЗАПУСК ==========
async def main():
    success = await send_weather()
    
    if success:
        print("🎉 БОТ УСПЕШНО ВЫПОЛНИЛ ЗАДАНИЕ!")
    else:
        print("😢 БОТ ЗАВЕРШИЛСЯ С ОШИБКОЙ")
    
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(main())
