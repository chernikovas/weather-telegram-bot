"""
Телеграм-бот "Погода" с приветствием и командами
Режимы:
1. Автоматическая отправка в 08:00 (через GitHub Actions)
2. Интерактивные команды: /start, /weather, /help
"""

import os
import asyncio
from datetime import datetime
import pytz
import requests
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, ContextTypes
import logging

print("=" * 50)
print("🤖 БОТ С КОМАНДАМИ И ПРИВЕТСТВИЕМ")
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
            'cnt': 6
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()['list']
        
    except Exception:
        return None

def create_temperature_chart(forecast_data):
    """Создает ASCII-график температуры"""
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
        temp_range = max_temp - min_temp
        
        if temp_range == 0:
            temp_range = 1
        
        chart_lines = []
        chart_lines.append("📈 Температура сегодня:")
        
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
    """Преобразует градусы в направление ветра"""
    if degrees is None:
        return ""
    
    directions = [
        "северный", "северо-восточный", "восточный", "юго-восточный",
        "южный", "юго-западный", "западный", "северо-западный"
    ]
    
    index = int((degrees + 22.5) / 45) % 8
    return directions[index]

# ========== СОЗДАНИЕ СООБЩЕНИЙ ==========
def create_welcome_message():
    """Создает приветственное сообщение"""
    return """👋 Привет! Я бот погоды!

Я буду присылать тебе погоду каждый день в 08:00 утра.

📋 Доступные команды:
/start - это сообщение
/weather - текущая погода прямо сейчас
/help - справка по командам

📍 Сейчас я настроен на погоду в Тамани.

Хорошего дня! ☀️"""

def create_help_message():
    """Создает сообщение справки"""
    return """ℹ️ Справка по командам:

/start - приветственное сообщение
/weather - получить текущую погоду
/help - эта справка

🌤️ Бот автоматически отправляет погоду:
• Каждый день в 08:00 по МСК
• С графиком температуры на день
• С деталями: ветер, влажность, давление

Напиши /weather чтобы проверить прямо сейчас!"""

def create_weather_message(current_data, forecast_data, is_morning=True):
    """Создает сообщение о погоде"""
    if not current_data:
        return "⚠️ Не удалось получить данные о погоде. Попробуйте позже."
    
    try:
        city = current_data.get('name', 'Тамань')
        temp = current_data['main']['temp']
        feels_like = current_data['main']['feels_like']
        temp_min = current_data['main']['temp_min']
        temp_max = current_data['main']['temp_max']
        humidity = current_data['main']['humidity']
        pressure = current_data['main']['pressure'] * 0.750062
        description = current_data['weather'][0]['description'].capitalize()
        wind_speed = current_data['wind']['speed']
        wind_deg = current_data['wind'].get('deg')
        
        wind_dir = get_wind_direction(wind_deg)
        
        # Текущая дата и время
        moscow_tz = pytz.timezone('Europe/Moscow')
        now = datetime.now(moscow_tz)
        
        days = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 
                'Пятница', 'Суббота', 'Воскресенье']
        months = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
                 'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря']
        
        date_str = f"{days[now.weekday()]}, {now.day} {months[now.month-1]} {now.year}"
        
        # Заголовок в зависимости от времени
        if is_morning:
            greeting = "🌅 Доброе утро!"
        elif 12 <= now.hour < 18:
            greeting = "🌞 Добрый день!"
        elif 18 <= now.hour < 23:
            greeting = "🌆 Добрый вечер!"
        else:
            greeting = "🌙 Доброй ночи!"
        
        # Создаем график
        chart = create_temperature_chart(forecast_data)
        
        # Форматируем сообщение
        message = f"""{greeting}

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
        
        if chart:
            message += f"\n{chart}\n"
        
        if is_morning:
            message += "\nХорошего дня! 👋"
        else:
            message += "\nБудьте здоровы! 👋"
        
        return message
        
    except Exception as e:
        print(f"❌ Ошибка создания сообщения: {e}")
        return f"🌤️ Погода в Тамани: {current_data['main']['temp']:.0f}°C"

# ========== ОБРАБОТЧИКИ КОМАНД ==========
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    welcome = create_welcome_message()
    await update.message.reply_text(welcome)

async def weather_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /weather"""
    print(f"📨 Команда /weather от пользователя {update.effective_user.id}")
    
    # Получаем данные
    current = get_current_weather()
    forecast = get_forecast()
    
    if not current:
        await update.message.reply_text("⚠️ Не удалось получить данные о погоде. Попробуйте позже.")
        return
    
    # Создаем сообщение (не утреннее, так как команда вручную)
    message = create_weather_message(current, forecast, is_morning=False)
    await update.message.reply_text(message)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    help_text = create_help_message()
    await update.message.reply_text(help_text)

# ========== ФУНКЦИИ ДЛЯ GITHUB ACTIONS ==========
async def send_daily_weather():
    """Функция для ежедневной отправки (из GitHub Actions)"""
    try:
        print("📡 Отправка ежедневной сводки...")
        
        bot = Bot(token=BOT_TOKEN)
        current = get_current_weather()
        forecast = get_forecast()
        
        if not current:
            await bot.send_message(
                chat_id=USER_ID,
                text="⚠️ Не удалось получить данные о погоде на сегодня."
            )
            return False
        
        message = create_weather_message(current, forecast, is_morning=True)
        await bot.send_message(chat_id=USER_ID, text=message)
        
        print("✅ Ежедневная сводка отправлена!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка отправки: {e}")
        return False

# ========== РЕЖИМ РАБОТЫ ==========
def run_bot_mode():
    """Запуск бота в режиме прослушивания команд"""
    print("🤖 Запуск в режиме бота (прослушивание команд)...")
    print("⚠️ Этот режим не работает на GitHub Actions")
    print("   Используйте только для локального тестирования")
    
    # Создаем приложение
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Добавляем обработчики команд
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("weather", weather_command))
    application.add_handler(CommandHandler("help", help_command))
    
    # Запускаем бота
    application.run_polling(allowed_updates=Update.ALL_TYPES)

async def github_mode():
    """Режим для GitHub Actions (одноразовая отправка)"""
    print("🚀 Запуск в режиме GitHub Actions...")
    success = await send_daily_weather()
    
    if success:
        print("🎉 УСПЕШНО ВЫПОЛНЕНО!")
    else:
        print("😢 ЗАВЕРШЕНО С ОШИБКОЙ")
    
    print("=" * 50)

# ========== ГЛАВНАЯ ФУНКЦИЯ ==========
async def main():
    """Определяем режим работы"""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--bot":
        # Режим интерактивного бота (для локального тестирования)
        run_bot_mode()
    else:
        # Режим GitHub Actions (по умолчанию)
        await github_mode()

if __name__ == "__main__":
    asyncio.run(main())
