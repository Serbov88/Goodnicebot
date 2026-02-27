import os
import telebot
import replicate
import time
import logging

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.environ.get('BOT_TOKEN')
REPLICATE_TOKEN = os.environ.get('REPLICATE_TOKEN')

if not BOT_TOKEN or not REPLICATE_TOKEN:
    raise ValueError("Токены не найдены!")

os.environ["REPLICATE_API_TOKEN"] = REPLICATE_TOKEN
bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "👋 Привет! Я SceneForgeBot!\nОтправь текст — сделаю видео.")

@bot.message_handler(func=lambda message: True)
def generate(message):
    msg = bot.reply_to(message, "🎥 Генерирую видео...")
    try:
        output = replicate.run(
            "lucataco/animate-diff:beecf59c4aee8d81bf04f0381033dfa10dc16e845b4ae00d281e2fa377e48a9f",
            input={"prompt": message.text}
        )
        bot.delete_message(message.chat.id, msg.message_id)
        bot.send_message(message.chat.id, f"✅ Видео готово!\n{output}")
    except Exception as e:
        bot.edit_message_text(f"❌ Ошибка: {str(e)}", message.chat.id, msg.message_id)

if __name__ == "__main__":
    logging.info("Бот запущен!")
    while True:
        try:
            bot.infinity_polling()
        except Exception as e:
            logging.error(f"Ошибка: {e}")
            time.sleep(5)
