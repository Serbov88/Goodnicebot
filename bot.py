import os
import telebot
import replicate
import openai
import time
import logging
import requests

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

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, 
        "👋 Привет! Я SceneForgeBot (стабильная версия)!\n\n"
        "📸 **Отправь фото** — я оживлю\n"
        "🎬 **/video текст** — видео из текста\n"
        "💬 **Просто напиши** — отвечу"
    )

# Видео из текста (рабочая версия)
@bot.message_handler(commands=['video'])
def generate_video(message):
    prompt = message.text.replace('/video', '').strip()
    if not prompt:
        bot.reply_to(message, "Напиши запрос после /video")
        return
        
    msg = bot.reply_to(message, "🎥 Генерирую видео...")
    try:
        output = replicate.run(
            "lucataco/animate-diff:beecf59c4aee8d81bf04f0381033dfa10dc16e845b4ae00d281e2fa377e48a9f",
            input={"prompt": prompt}
        )
        bot.delete_message(message.chat.id, msg.message_id)
        
        video_url = output[0] if isinstance(output, list) else output
        bot.send_message(message.chat.id, f"✅ Видео готово!\n{video_url}")
            
    except Exception as e:
        bot.edit_message_text(f"❌ Ошибка: {str(e)}", message.chat.id, msg.message_id)

# Оживление фото (новая функция)
@bot.message_handler(content_types=['photo'])
def animate_photo(message):
    msg = bot.reply_to(message, "🎬 Оживляю фото...")
    
    try:
        # Скачиваем фото
        file_info = bot.get_file(message.photo[-1].file_id)
        photo = bot.download_file(file_info.file_path)
        
        # Сохраняем
        with open('photo.jpg', 'wb') as f:
            f.write(photo)
        
        # Загружаем на Replicate через API напрямую
        with open('photo.jpg', 'rb') as f:
            response = requests.post(
                "https://api.replicate.com/v1/predictions",
                headers={"Authorization": f"Token {REPLICATE_TOKEN}"},
                files={"file": f},
                data={
                    "version": "haiper-ai/haiper-video-2:latest",
                    "input": '{"image": "file", "prompt": "make it move"}'
                }
            )
        
        os.remove('photo.jpg')
        
        if response.status_code == 201:
            data = response.json()
            bot.delete_message(message.chat.id, msg.message_id)
            bot.send_message(message.chat.id, f"✅ Фото оживает! ID: {data['id']}")
        else:
            bot.edit_message_text(f"❌ Ошибка {response.status_code}", message.chat.id, msg.message_id)
            
    except Exception as e:
        bot.edit_message_text(f"❌ Ошибка: {str(e)}", message.chat.id, msg.message_id)

# Общение
@bot.message_handler(func=lambda message: True)
def chat(message):
    bot.send_chat_action(message.chat.id, 'typing')
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": message.text}]
        )
        bot.reply_to(message, response.choices[0].message.content)
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {str(e)}")

if __name__ == "__main__":
    print("🚀 Стабильная версия запущена!")
    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            print(f"Ошибка: {e}")
            time.sleep(5)
