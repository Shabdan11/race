# Импортируем библиотеки/модули
import telebot
import logging
import sqlite3
import time
import os

from dotenv import load_dotenv
from telebot import types
from db import create_tables, create_playing_table
from state import create_states

# Создаем бота
load_dotenv()  # Загружает переменные окружения из .env файла
TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

PORT = int(os.getenv("PORT", 5000))  # Используется порт из переменной окружения или 5000 по умолчанию



# Настройка логирования
logging.basicConfig(level=logging.INFO)
user_data = {}

rules_text = '''Правила : 🙊
1. Полностью запрещено участие с транспортными средствами из Black Pass. За нарушение данного правила выдаётся наказание в виде дисквалификации 🚗\n
2. Оплата за участие отправляется до турнира, без оплаты вы не являетесь участником 💵\n
3. Абсолютно запрещен DM (DeathMatch – Убийство без причины) и любая другая помеха проведению турнира. За нарушение данного правила выдается наказание в виде дисквалификации 👤\n
4. Выигравших определяет исключительно администрация турнира. Участники не в праве спорить с судьёй о "победившем". За нарушение данного правила выдаётся наказание в виде предупреждения 😌\n
5. Время проведения этапов турнира сообщается исключительно в данном канале. За опоздание участника на турнир более чем на 20 минут, участник получает наказание в виде дисквалификации ⏳\n
6. Запрещено выяснение личных конфликтов во время проведения турнира, также запрещены любые нецензурные выражения. За нарушение данных правил выдаётся предупреждение 🤬\n
'''

@bot.message_handler(commands=['show_player'])
def show_player(message):
    try:
        with sqlite3.connect('example.db') as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM players")
            rows = cursor.fetchall()

            if rows:
                # Создаем текст для вывода всех данных
                result = "<b>Список игроков:</b>\n"
                for row in rows:
                    result += f"ID: {row[0]}, Имя: {row[1]}, Телефон: {row[2]}, Машина: {row[3]}\n"
            else:
                result = "Нет зарегистрированных игроков."

        bot.send_message(message.chat.id, result, parse_mode='html')

    except sqlite3.DatabaseError as e:
        logging.error(f"Database error: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка при получении данных.")

@bot.message_handler(commands=['show_playing'])
def show_playing(message):
    try:
        with sqlite3.connect('example.db') as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM playing")
            rows = cursor.fetchall()

            if rows:
                # Формируем текст для вывода всех данных
                result = "<b>Список участников в турнире:</b>\n"
                for row in rows:
                    result += f"ID: {row[0]}, Имя: {row[1]}, Машина: {row[2]}\n"
            else:
                result = "Нет участников в турнире."

        bot.send_message(message.chat.id, result, parse_mode='html')

    except sqlite3.DatabaseError as e:
        logging.error(f"Database error: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка при получении данных.")

@bot.message_handler(commands=['delete_playing'])
def delete_playing(message):
    user_id = message.chat.id  # ID текущего пользователя
    try:
        with sqlite3.connect('example.db') as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM playing WHERE id = ?", (user_id,))
            if cursor.rowcount > 0:
                bot.send_message(user_id, "Ваши данные успешно удалены из таблицы 'playing'.")
            else:
                bot.send_message(user_id, "В таблице 'playing' данных для удаления не найдено.")
    except sqlite3.DatabaseError as e:
        logging.error(f"Database error: {e}")
        bot.send_message(user_id, "Произошла ошибка при удалении данных из таблицы 'playing'.")

@bot.message_handler(commands=['delete_players'])
def delete_players(message):
    user_id = message.chat.id  # ID текущего пользователя
    try:
        with sqlite3.connect('example.db') as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM players WHERE id = ?", (user_id,))
            if cursor.rowcount > 0:
                bot.send_message(user_id, "Ваши данные успешно удалены из таблицы 'players'.")
            else:
                bot.send_message(user_id, "В таблице 'players' данных для удаления не найдено.")
    except sqlite3.DatabaseError as e:
        logging.error(f"Database error: {e}")
        bot.send_message(user_id, "Произошла ошибка при удалении данных из таблицы 'players'.")


# Текущий турнир
now = 'Турнир 😈'
txt = f'''Вы выбрали пункт Учавствовать 🏆
Сейчас проходит соревнование - {now}
Будете ли вы в нем участвовать?'''

name_pro = '''Вы выбрали пункт авторизоваться ! 😈
Для регистрации введите ваше игровое имя 👤 :'''

phone_pro = '''Хорошо, теперь нам нужен ваш игровой номер телефона 📱 :'''
car_pro = '''И на последок , на какой машине вы будете учавствовать ? 🚗 :'''

# Функция для установки состояния пользователя
def set_user_state(user_id, state, role):
    try:
        with sqlite3.connect('example.db') as conn:
            cursor = conn.cursor()
            cursor.execute('''INSERT OR REPLACE INTO user_states (user_id, state, role)
                              VALUES (?, ?, ?)''', (user_id, state, role))
            conn.commit()
    except sqlite3.DatabaseError as e:
        logging.error(f"Database error: {e}")

# Функция для получения состояния пользователя
def get_user_state(user_id):
    try:
        with sqlite3.connect('example.db') as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT state FROM user_states WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            return row[0] if row else None
    except sqlite3.DatabaseError as e:
        logging.error(f"Database error: {e}")
        return None


def get_player_name_by_id(user_id):
    try:
        with sqlite3.connect('example.db') as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM players WHERE id = ?", (user_id,))
            result = cursor.fetchone()
            if result:
                return result[0]  # Возвращаем имя
            else:
                return None  # Пользователь не найден
    except sqlite3.DatabaseError as e:
        logging.error(f"Database error: {e}")
        return None

def get_player_car_by_id(user_id):
    try:
        with sqlite3.connect('example.db') as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT car FROM players WHERE id = ?", (user_id,))
            result = cursor.fetchone()
            if result:
                return result[0]  # Возвращаем имя
            else:
                return None  # Пользователь не найден
    except sqlite3.DatabaseError as e:
        logging.error(f"Database error: {e}")
        return None


# Обработчик команды /start
@bot.message_handler(commands=['start'])
def start(message):
    create_tables()
    create_playing_table()
    create_states()
    user_id = message.chat.id

    # Создаем клавиатуру
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    reg_btn = types.KeyboardButton(text='Зарегистрироваться 🤖')
    play_btn = types.KeyboardButton(text='Учавствовать 🏆')
    laws_btn = types.KeyboardButton(text='Правила 📖')
    markup.add(reg_btn, play_btn, laws_btn)

    # Отправляем одно сообщение
    welcome_text = (
        "<b>Добро пожаловать! Выберите пункт ниже:</b>\n"
        "Если вы новичок, пожалуйста, зарегистрируйтесь!"
    )
    bot.send_message(user_id, welcome_text, parse_mode='html', reply_markup=markup)

@bot.message_handler(commands=['change'])
def change(message):
    global now  # Указываем, что мы хотим использовать глобальную переменную
    if now == 'Гонки 🏁':
        now = 'Турнир 😈'
        bot.send_message(message.chat.id, f"Соревнование изменено на: {now}")

    elif now == 'Турнир 😈':
        now = 'Гонки 🏁'
        bot.send_message(message.chat.id, f"Соревнование изменено на: {now}")



# Обработчик для кнопки регистрации
@bot.message_handler(func=lambda message: message.text.strip() in ['Зарегистрироваться 🤖', '/reg'])
def registering(message):
    user_id = message.chat.id
    try:
        state = get_user_state(user_id)
        if state == 'registered':
            bot.send_message(user_id, 'Вы уже зарегистрированы!')
        else:
            msg = bot.send_message(user_id, f'{name_pro}')
            bot.register_next_step_handler(msg, name_process)
    except Exception as e:
        bot.reply_to(message, 'Произошла ошибка. Пожалуйста, попробуйте снова.')
        logging.error(f"Error in registering handler: {e}")

# Шаг обработки имени
def name_process(message):
    user_id = message.chat.id
    try:
        name = message.text
        user_data[user_id] = {'id': user_id, 'name': name}
        msg = bot.send_message(user_id, f'{phone_pro}')
        bot.register_next_step_handler(msg, phone_process)
    except Exception as e:
        bot.reply_to(message, 'Произошла ошибка. Пожалуйста, попробуйте снова.')
        logging.error(f"Error in name_process: {e}")


@bot.message_handler(commands=['delete'])
def delete_self(message):
    user_id = message.chat.id  # Получаем ID пользователя из сообщения
    try:
        with sqlite3.connect('example.db') as conn:
            cursor = conn.cursor()

            # Проверяем, существует ли запись с таким ID
            cursor.execute("SELECT * FROM players WHERE id = ?", (user_id,))
            result = cursor.fetchone()

            if result:
                # Удаляем запись
                cursor.execute("DELETE FROM players WHERE id = ?", (user_id,))
                conn.commit()
                bot.send_message(message.chat.id, f"Ваш профиль успешно удален из базы данных.")
                set_user_state(user_id, 'unreg', 'player')
            else:
                # Если пользователя нет в базе
                bot.send_message(message.chat.id, f"Ваш профиль не найден в базе данных.")
    except Exception as e:
        logging.error(f"Error in delete_self: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка при удалении профиля. Попробуйте снова.")


# Шаг обработки номера телефона
def phone_process(message):
    user_id = message.chat.id
    try:
        phone = int(message.text)
        user_data[user_id]['phone'] = phone
        msg = bot.send_message(user_id, 'И на последок , на какой машине вы будете учавствовать ? 🚗 :\n')
        bot.register_next_step_handler(msg, car_process)
    except ValueError:
        bot.reply_to(message, 'Пожалуйста, введите корректный номер телефона.')
        name_process(message)
    except Exception as e:
        bot.reply_to(message, 'Произошла ошибка. Пожалуйста, попробуйте снова.')
        logging.error(f"Error in phone_process: {e}")

# Шаг обработки машины
def car_process(message):
    user_id = message.chat.id
    try:
        car = message.text
        user_data[user_id]['car'] = car

        with sqlite3.connect('example.db') as conn:
            cursor = conn.cursor()
            cursor.execute('''INSERT OR REPLACE INTO players(id, name, phone, car)
                              VALUES (?, ?, ?, ?)''', (user_data[user_id]['id'],
                                                       user_data[user_id]['name'],
                                                       user_data[user_id]['phone'],
                                                       user_data[user_id]['car']))
            conn.commit()

        set_user_state(user_id, 'registered', 'player')
        bot.send_message(user_id, '<b>Вы успешно зарегистрировались на гонку ! ❤️</b>', parse_mode='html')
        logging.info('New player')

    except Exception as e:
        bot.reply_to(message, 'Произошла ошибка. Пожалуйста, попробуйте снова.')
        logging.error(f"Error in car_process: {e}")

@bot.message_handler(commands=['help'])
def help_command(message):
    help_text = """
<b>Список доступных команд:</b>
/start - Начать взаимодействие с ботом
/reg или Зарегистрироваться 🤖 - Зарегистрироваться в системе
/delete - Удалить ваш профиль из базы данных
/help - Посмотреть список доступных команд
Учавствовать 🏆 - Принять участие в текущем соревновании
Правила 📖 - Узнать правила соревнований
    """
    bot.send_message(message.chat.id, help_text, parse_mode='html')


@bot.message_handler(func=lambda message: message.text.strip() in ['Учавствовать 🏆', '/play'])
def play_handler(message):
    user_id = message.chat.id
    markup = types.InlineKeyboardMarkup()
    back_btn = types.InlineKeyboardButton('Назад ⬅️', callback_data="back")
    race_btn = types.InlineKeyboardButton('Гонки 🏁', callback_data='race')
    tournire = types.InlineKeyboardButton('Турнир 😈', callback_data='tournament')
    markup.add(race_btn, tournire)
    state = get_user_state(user_id)

    if state == 'registered':
        bot.send_message(user_id, txt, reply_markup=markup)

    else:
        bot.send_message(user_id, 'Пожалуйста зарегестрируйтесь!')

# Обработчик коллбэков
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    car = get_player_car_by_id(call.message.chat.id)
    name = get_player_name_by_id(call.message.chat.id)

    if call.data == 'back':
        user_id = call.message.chat.id
        markup = types.InlineKeyboardMarkup()
        race_btn = types.InlineKeyboardButton('Гонки 🏁', callback_data='race')
        tournire = types.InlineKeyboardButton('Турнир 😈', callback_data='tournament')
        markup.add(race_btn, tournire)
        bot.send_message(call.message.chat.id, 'Вы вернулись назад.', reply_markup=markup)


    elif call.data == 'race':
        if now == 'Гонки 🏁':
            markup = types.InlineKeyboardMarkup()
            no = types.InlineKeyboardButton('Нет', callback_data='no')
            yes = types.InlineKeyboardButton('Верно!', callback_data='yes')
            back_btn = types.InlineKeyboardButton('Назад ⬅️', callback_data="back")

            markup.add(yes, no, back_btn)

            bot.send_message(call.message.chat.id, 'Вы успешно участвуете в "Гонки 🏁"\n'
                                                   'Оплатите за участие в турнире,\n'
                                                   'без оплаты вы не являетесь участником 💵\n\n'
                                                   f'Ваше имя: {name}, А ваша машина - {car}\n'
                                                   'Верно?\n', reply_markup=markup)
        else:
            bot.send_message(call.message.chat.id, 'На данный момент проходит - "Турнир 😈"')

    elif call.data == 'tournament':
        if now == 'Турнир 😈':
            markup = types.InlineKeyboardMarkup()
            no = types.InlineKeyboardButton('Нет', callback_data='no')
            yes = types.InlineKeyboardButton('Верно!', callback_data='yes')
            back_btn = types.InlineKeyboardButton('Назад ⬅️', callback_data="back")

            markup.add(yes, no, back_btn)

            bot.send_message(call.message.chat.id, 'Вы успешно участвуете в "Турнир 😈"\n'
                                                   'Оплатите участие в турнире на банковский счёт "516734" 🏦 ,\n'
                                                   'цену за участие вы можете узнать в нашем телеграмм – канале\n'
                                                   '@cherryracing 💵\n\n'
                                                   f'Ваше имя: {name}, А ваша машина - {car}\n'
                                                   'Верно?\n', reply_markup=markup)
        else:
            bot.send_message(call.message.chat.id, 'На данный момент проходит - "Гонки 🏁"')

    if call.data == 'yes':
        user_id = call.message.chat.id
        try:
            with sqlite3.connect('example.db') as conn:
                cursor = conn.cursor()
                cursor.execute('''INSERT OR REPLACE INTO playing(id, name, car)
                                  VALUES (?, ?, ?)''', (user_id,
                                                           name,
                                                           car))
                conn.commit()

            bot.send_message(call.message.chat.id, 'Вы успешно участвуете в соревновании!')
            logging.info('New player in competition!')

        except Exception as e:
            bot.reply_to(call.message, 'Произошла ошибка. Пожалуйста, попробуйте снова.')
            logging.error(f"Error in playing: {e}")

    if call.data == 'no':
        bot.send_message(call.message.chat.id, 'Вы отказались!')

@bot.message_handler(commands=['help'])
def help_message(message):
    help_text = (
        "Доступные команды:\n"
        "/start - Начать взаимодействие с ботом\n"
        "/reg - Зарегистрироваться в игре\n"
        "🎯 Участвовать 🏆 - Принять участие в турнире\n"
        "📖 Правила - Просмотреть правила турнира\n"
        "/help - Показать список доступных команд"
    )
    bot.send_message(message.chat.id, help_text)


@bot.message_handler(func=lambda message: message.text == 'Правила 📖')
def rule(message):
    bot.send_message(message.chat.id, f'{rules_text}')

# Бесконечный цикл для работы бота
while True:
    try:
        logging.info("Starting bot polling")
        bot.polling(none_stop=True, timeout=60, interval=0, port=PORT)
    except Exception as e:
        logging.error(f"Error occurred: {e}")
        time.sleep(15)
