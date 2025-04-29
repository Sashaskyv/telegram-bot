import telebot
from telebot import types
import sqlite3
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()
bot = telebot.TeleBot(os.getenv('BOT_TOKEN'))

def create_calendar(year=None, month=None):
    if year is None:
        year = datetime.now().year
    if month is None:
        month = datetime.now().month
    
    markup = types.InlineKeyboardMarkup()
    # Заголовок с месяцем и годом
    markup.row(types.InlineKeyboardButton(f"{month}/{year}", callback_data="ignore"))
    
    # Дни недели
    week_days = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    row = []
    for day in week_days:
        row.append(types.InlineKeyboardButton(day, callback_data="ignore"))
    markup.row(*row)
    
    # Дни месяца
    first_day = datetime(year, month, 1)
    last_day = (datetime(year, month + 1, 1) - timedelta(days=1)).day
    current_day = 1
    week = []
    
    # Заполняем первую неделю
    for _ in range(first_day.weekday()):
        week.append(types.InlineKeyboardButton(" ", callback_data="ignore"))
    
    while current_day <= last_day:
        if len(week) == 7:
            markup.row(*week)
            week = []
        week.append(types.InlineKeyboardButton(str(current_day), callback_data=f"date_{year}_{month}_{current_day}"))
        current_day += 1
    
    if week:
        while len(week) < 7:
            week.append(types.InlineKeyboardButton(" ", callback_data="ignore"))
        markup.row(*week)
    
    # Кнопки навигации
    prev_month = month - 1 if month > 1 else 12
    prev_year = year - 1 if month == 1 else year
    next_month = month + 1 if month < 12 else 1
    next_year = year + 1 if month == 12 else year
    
    markup.row(
        types.InlineKeyboardButton("◀️", callback_data=f"calendar_{prev_year}_{prev_month}"),
        types.InlineKeyboardButton("▶️", callback_data=f"calendar_{next_year}_{next_month}")
    )
    
    return markup

@bot.callback_query_handler(func=lambda call: call.data.startswith('calendar_'))
def calendar_callback(call):
    _, year, month = call.data.split('_')
    bot.edit_message_reply_markup(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=create_calendar(int(year), int(month))
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith('date_'))
def date_callback(call):
    _, year, month, day = call.data.split('_')
    date = f"{day}.{month}.{year}"
    
    conn = sqlite3.connect('test_base.sql')
    cur = conn.cursor()
    cur.execute('UPDATE users SET date = ? WHERE user_id = ?', (date, call.from_user.id))
    conn.commit()
    cur.close()
    conn.close()
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for hour in range(18, 23):
        markup.add(types.KeyboardButton(f'{hour}:00'))
    
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=f'Вы выбрали дату: {date}\nТеперь выберите время (с 18:00 до 22:00):'
    )
    bot.send_message(call.message.chat.id, 'Выберите время:', reply_markup=markup)
    bot.register_next_step_handler(call.message, get_time)

@bot.message_handler(commands=['start'])
def start(message):
    conn = sqlite3.connect('test_base.sql')   
    cur = conn.cursor()                   

    cur.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        name TEXT,
        course INTEGER,
        sport TEXT,
        level TEXT,
        date TEXT,
        time TEXT
    )''')
    conn.commit()  
    cur.close()     
    conn.close() 

    bot.send_message(message.chat.id, 'Введите ваше ФИО')
    bot.register_next_step_handler(message, get_name)

def get_name(message):
    name = message.text
    conn = sqlite3.connect('test_base.sql')
    cur = conn.cursor()
    cur.execute('INSERT INTO users (user_id, name) VALUES (?, ?)', (message.from_user.id, name))
    conn.commit()
    cur.close()
    conn.close()
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for i in range(1, 7):
        markup.add(types.KeyboardButton(str(i)))
    
    bot.send_message(message.chat.id, 'Выберите курс обучения (1-6):', reply_markup=markup)
    bot.register_next_step_handler(message, get_course)

def get_course(message):
    course = message.text
    if not course.isdigit() or int(course) not in range(1, 7):
        bot.send_message(message.chat.id, 'Пожалуйста, выберите курс от 1 до 6')
        bot.register_next_step_handler(message, get_course)
        return
    
    conn = sqlite3.connect('test_base.sql')
    cur = conn.cursor()
    cur.execute('UPDATE users SET course = ? WHERE user_id = ?', (course, message.from_user.id))
    conn.commit()
    cur.close()
    conn.close()
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton('Футбол'))
    markup.add(types.KeyboardButton('Баскетбол'))
    markup.add(types.KeyboardButton('Волейбол'))
    markup.add(types.KeyboardButton('Теннис'))
    
    bot.send_message(message.chat.id, 'Выберите вид спорта:', reply_markup=markup)
    bot.register_next_step_handler(message, get_sport)

def get_sport(message):
    sport = message.text
    conn = sqlite3.connect('test_base.sql')
    cur = conn.cursor()
    cur.execute('UPDATE users SET sport = ? WHERE user_id = ?', (sport, message.from_user.id))
    conn.commit()
    cur.close()
    conn.close()
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton('Новичок'))
    markup.add(types.KeyboardButton('Любитель'))
    markup.add(types.KeyboardButton('Профессионал'))
    
    bot.send_message(message.chat.id, 'Выберите ваш уровень:', reply_markup=markup)
    bot.register_next_step_handler(message, get_level)

def get_level(message):
    level = message.text
    if level not in ['Новичок', 'Любитель', 'Профессионал']:
        bot.send_message(message.chat.id, 'Пожалуйста, выберите один из предложенных уровней')
        bot.register_next_step_handler(message, get_level)
        return
    
    conn = sqlite3.connect('test_base.sql')
    cur = conn.cursor()
    cur.execute('UPDATE users SET level = ? WHERE user_id = ?', (level, message.from_user.id))
    conn.commit()
    cur.close()
    conn.close()
    
    bot.send_message(message.chat.id, 'Выберите дату:', reply_markup=create_calendar())

def get_time(message):
    time = message.text
    if not any(f'{hour}:00' == time for hour in range(18, 23)):
        bot.send_message(message.chat.id, 'Пожалуйста, выберите время с 18:00 до 22:00')
        bot.register_next_step_handler(message, get_time)
        return
    
    conn = sqlite3.connect('test_base.sql')
    cur = conn.cursor()
    cur.execute('UPDATE users SET time = ? WHERE user_id = ?', (time, message.from_user.id))
    conn.commit()
    cur.close()
    conn.close()
    
    bot.send_message(message.chat.id, 'Спасибо за регистрацию! Ваши данные сохранены.')

@bot.message_handler(commands=['myinfo'])
def show_info(message):
    conn = sqlite3.connect('test_base.sql')
    cur = conn.cursor()
    cur.execute('SELECT * FROM users WHERE user_id = ?', (message.from_user.id,))
    user = cur.fetchone()
    cur.close()
    conn.close()
    
    if user:
        bot.send_message(message.chat.id, f'''
Ваши данные:
ФИО: {user[2]}
Курс: {user[3]}
Вид спорта: {user[4]}
Уровень: {user[5]}
Дата: {user[6]}
Время: {user[7]}
''')
    else:
        bot.send_message(message.chat.id, 'Вы еще не зарегистрированы. Используйте команду /start')

bot.polling(none_stop=True)
    