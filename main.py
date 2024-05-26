import telebot
import json

# Загружаем данные аккаунтов из JSON
with open('accounts.json', 'r') as file:
    accounts_data = json.load(file)

# Количество билетов, которое можно купить
MAX_TICKETS = accounts_data['max_tickets']

# Создаем бота
bot = telebot.TeleBot('7300107124:AAFya7jWcUByISvHdQPu19s_7V_0zqUPALk')

# Словарь для хранения информации о том, кто какой аккаунт взял
user_accounts = {}


# Функция для записи информации о сданном аккаунте в файл
def write_account_info(username, account_login, tickets_bought):
    with open('account_info.txt', 'a') as file:
        file.write(f"Username: {username}, Login: {account_login}, Tickets bought: {tickets_bought}\n")


# Функция для обработки команды /start
@bot.message_handler(commands=['start'])
def start_message(message):
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    get_account_button = telebot.types.InlineKeyboardButton(text="Взять аккаунт", callback_data="get_account")
    markup.add(get_account_button)
    bot.send_message(message.chat.id, "Нажми на кнопку 'Взять аккаунт', чтобы получить аккаунт.",
                     reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == 'get_account')
def get_account(call):
    # Сортируем аккаунты по количеству билетов
    sorted_accounts = sorted(accounts_data['accounts'], key=lambda x: x['tickets'])
    for account in sorted_accounts:
        if account['tickets'] < MAX_TICKETS and account.get('owner') == "":
            available_tickets = MAX_TICKETS - account['tickets']
            account_info = f"Логин: {account['login']}\nПароль: {account['password']}\nДоступно для покупки: {available_tickets} билетов"
            # Отправляем информацию о доступном аккаунте с кнопкой "Сдать аккаунт"
            markup = telebot.types.InlineKeyboardMarkup(row_width=1)
            return_account_button = telebot.types.InlineKeyboardButton(text="Сдать аккаунт", callback_data="return_account")
            markup.add(return_account_button)
            bot.send_message(call.message.chat.id, account_info, reply_markup=markup)
            # Скрываем сообщение о доступном аккаунте
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Вы взяли аккаунт!")
            # Сохраняем информацию о том, кто взял какой аккаунт
            user_accounts[call.message.chat.id] = account['login']
            account['owner'] = str(call.message.chat.id)  # Исправление здесь
            break
    else:
        bot.send_message(call.message.chat.id, "Извините, все аккаунты уже выданы.")



@bot.callback_query_handler(func=lambda call: call.data == 'return_account')
def return_account(call):
    bot.send_message(call.message.chat.id, "Сколько билетов вы купили?")
    bot.register_next_step_handler(call.message, update_tickets)
    # Скрываем сообщение о доступном аккаунте
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Вы сдали аккаунт!")
    # Очищаем поле owner аккаунта
    for account in accounts_data['accounts']:
        if account.get('owner') == str(call.message.chat.id):
            account['owner'] = ""
            break



def update_tickets(message):
    try:
        tickets_bought = int(message.text)
        if tickets_bought < 0:
            raise ValueError
        # Обновляем количество билетов только на аккаунте, который был взят
        for account in accounts_data['accounts']:
            if account['login'] == user_accounts[message.chat.id]:
                account['tickets'] += tickets_bought
                break
        # Сохраняем обновленные данные в JSON
        with open('accounts.json', 'w') as file:
            json.dump(accounts_data, file, indent=4)
        # Записываем информацию о сданном аккаунте в файл
        username = message.from_user.username if message.from_user.username else "Unknown"
        write_account_info(username, user_accounts[message.chat.id], tickets_bought)
        bot.send_message(message.chat.id, f"Спасибо за информацию! Количество билетов успешно обновлено.")
        # После сдачи аккаунта отправляем сообщение с кнопкой "Взять аккаунт"
        markup = telebot.types.InlineKeyboardMarkup(row_width=1)
        get_account_button = telebot.types.InlineKeyboardButton(text="Взять аккаунт", callback_data="get_account")
        markup.add(get_account_button)
        bot.send_message(message.chat.id, "Привет! Нажми на кнопку 'Взять аккаунт', чтобы получить аккаунт.",
                         reply_markup=markup)
    except ValueError:
        bot.send_message(message.chat.id, "Пожалуйста, введите корректное число билетов (целое положительное число).")


# Функция для обработки команды /export
@bot.message_handler(commands=['export'])
def export_data(message):
    # Отправляем файл с данными об аккаунтах
    with open('account_info.txt', 'rb') as file:
        bot.send_document(message.chat.id, file, caption="Файл с данными об аккаунтах")

# Функция для обновления файла accounts.json администратором
@bot.message_handler(commands=['update_accounts'])
def update_accounts(message):
    bot.send_message(message.chat.id, "Пришлите новый файл accounts.json")
    bot.register_next_step_handler(message, process_new_accounts_file)


# Функция для обработки нового файла accounts.json
def process_new_accounts_file(message):
    if message.document:
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        # Сохраняем новый файл accounts.json
        with open('accounts_new.json', 'wb') as new_file:
            new_file.write(downloaded_file)
        # Заменяем старый файл новым
        try:
            with open('accounts_new.json', 'r') as new_file:
                new_accounts_data = json.load(new_file)
                # Проверяем, что файл содержит верный формат данных
                if 'accounts' in new_accounts_data:
                    with open('accounts.json', 'w') as accounts_file:
                        json.dump(new_accounts_data, accounts_file, indent=4)
                    bot.send_message(message.chat.id, "Файл accounts.json успешно обновлен.")
                else:
                    bot.send_message(message.chat.id, "Неверный формат данных в файле accounts.json.")
        except Exception as e:
            bot.send_message(message.chat.id, f"Произошла ошибка при обновлении файла accounts.json: {str(e)}")
    else:
        bot.send_message(message.chat.id, "Пожалуйста, пришлите файл в формате JSON.")

@bot.message_handler(commands=['clear_accounts_info'])
def clear_accounts_info(message):
    try:
        # Очищаем содержимое файла accounts_info.txt
        with open('account_info.txt', 'w'):
            pass
        bot.send_message(message.chat.id, "Файл account_info.txt успешно очищен.")
    except Exception as e:
        bot.send_message(message.chat.id, f"Произошла ошибка при очистке файла accounts_info.txt: {str(e)}")


# Обработчик неизвестных команд и сообщений
@bot.message_handler(func=lambda message: True)
def handle_unknown_message(message):
    bot.send_message(message.chat.id, "Извините, я не понимаю вашего сообщения.")



# Запускаем бота
bot.polling()
