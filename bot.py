import os
import telebot
import replicate
import openai
import time
import logging

logging.basicConfig(level=logging.INFO)

# Токены
BOT_TOKEN = os.environ.get('BOT_TOKEN')
REPLICATE_TOKEN = os.environ.get('REPLICATE_TOKEN')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')

if not BOT_TOKEN or not REPLICATE_TOKEN or not OPENAI_API_KEY:
    raise ValueError("Токены не найдены!")

os.environ["REPLICATE_API_TOKEN"] = REPLICATE_TOKEN
openai.api_key = OPENAI_API_KEY
bot = telebot.TeleBot(BOT_TOKEN)

# Системный промпт для OpenAI
SYSTEM_PROMPT = """
Ты — дружелюбный ИИ-ассистент по имени SceneForgeBot.
Твоя задача — общаться с пользователем, отвечать на вопросы.
Ты также умеешь оживлять фото — для этого пользователь должен просто отправить фотку.
"""

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, 
        "👋 Привет! Я SceneForgeBot!\n\n"
        "📸 **Отправь фото** — я оживлю его\n"
        "💬 **Напиши сообщение** — я отвечу как ChatGPT"
    )

# Обработка фото
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    msg = bot.reply_to(message, "🎬 Оживляю фото... Это займет около минуты")
    
    try:
        # Получаем фото
        file_id = message.photo[-1].file_id
        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        # Сохраняем временно
        with open('input.jpg', 'wb') as new_file:
            new_file.write(downloaded_file)
        
        # Отправляем в Replicate
        with open('input.jpg', 'rb') as image_file:
            output = replicate.run(
                "haiper-ai/haiper-video-2:latest",
                input={
                    "image": image_file,
                    "prompt": "make the person move naturally"
                }
            )
        
        # Удаляем временный файл
        os.remove('input.jpg')
        
        bot.delete_message(message.chat.id, msg.message_id)
        
        if output and isinstance(output, list):
            video_url = output[0]
        else:
            video_url = output
            
        bot.send_message(message.chat.id, f"✅ Фото ожило!\n{video_url}")
        
    except Exception as e:
        bot.edit_message_text(f"❌ Ошибка: {str(e)}", message.chat.id, msg.message_id)

# Обработка текста (общение через OpenAI)
@bot.message_handler(func=lambda message: True)
def chat(message):
    bot.send_chat_action(message.chat.id, 'typing')
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": message.text}
            ]
        )
        
        answer = response.choices[0].message.content
        bot.reply_to(message, answer)
        
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {str(e)}")

if __name__ == "__main__":
    print("🚀 Бот для оживления фото и общения запущен!")
    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            print(f"Ошибка: {e}")
            time.sleep(5)
