import telebot
import requests
import jsons
from dotenv import load_dotenv
import os
from Class_ModelResponse import ModelResponse

load_dotenv()
# Замените 'YOUR_BOT_TOKEN' на ваш токен от BotFather
API_TOKEN = os.getenv("TG_BOT_API_TOKEN")
bot = telebot.TeleBot(API_TOKEN)

# Контекст
user_contexts = {}

# Команды
@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "Привет! Я ваш Telegram бот.\n"
        "Доступные команды:\n"
        "/start - вывод всех доступных команд\n"
        "/model - выводит название используемой языковой модели\n"
        "/clear - очистить текущий контекст\n"
        "Отправьте любое сообщение, и я отвечу с помощью LLM модели."
    )
    bot.reply_to(message, welcome_text)


@bot.message_handler(commands=['model'])
def send_model_name(message):
    # Отправляем запрос к LM Studio для получения информации о модели
    response = requests.get('http://127.0.0.1:1234/v1/models')

    if response.status_code == 200:
        model_info = response.json()
        model_name = model_info['data'][0]['id']
        bot.reply_to(message, f"Используемая модель: {model_name}")
    else:
        bot.reply_to(message, 'Не удалось получить информацию о модели.')


@bot.message_handler(commands=['clear'])
def sen_clear_context(message):
    user_id = message.from_user.id
    if user_id in user_contexts:
        del user_contexts[user_id]
    bot.reply_to(message, "История диалога очищена. Начнем заново!")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = message.from_user.id
    user_query = message.text

    # Создаём контекст для нового пользователя
    if user_id not in user_contexts:
        user_contexts[user_id] = ""

    # Добавляем сообщение пользователя в контекст
    user_contexts[user_id] += f"role: user\n{user_query}\n"

    request = {
        "messages": [
          {
            "role": "user",
            "content": user_contexts[user_id]
          },
        ]
      }
    response = requests.post(
        'http://127.0.0.1:1234/v1/chat/completions',
        json=request
    )

    if response.status_code == 200:
        model_response: ModelResponse = jsons.loads(response.text, ModelResponse)
        answer = model_response.choices[0].message.content

        # Добавляем ответ модели в контекст
        user_contexts[user_id] += f"role: assistant\n{answer}\n"

        bot.reply_to(message, answer)
    else:
        bot.reply_to(message, 'Произошла ошибка при обращении к модели.')


# Запуск бота
if __name__ == '__main__':
    bot.polling(none_stop=True)
