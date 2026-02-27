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

# Системный промпт для OpenAI (как ты)
SYSTEM_PROMPT = """
Ты — дружелюбный ИИ-ассистент по имени SceneForgeBot.
Твоя задача — общаться с пользователем, отвечать на вопросы и выполнять запросы.
Если пользователь просит нарисовать что-то — отвечай: '/image запрос'
Если пользователь просит видео — отвечай: '/video запрос'
Если просто болтает — общайся как человек.
Ты — точная копия моего друга, который помогает мне с кодом и жизнью.
"""

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "👋 Привет! Я SceneForgeBot! Просто пиши что хочешь — сделаю.")

@bot.message_handler(commands=['video'])
def generate_video(message):
    prompt = message.text.replace('/video', '').strip()
    if not prompt:
        bot.reply_to(message, "Что именно хочешь увидеть в видео?")
        return
        
    msg = bot.reply_to(message, "🎥 Генерирую видео...")
    try:
        output = replicate.run(
            "lucataco/animate-diff:beecf59c4aee8d81bf04f0381033dfa10dc16e845b4ae00d281e2fa377e48a9f",
            input={"prompt": prompt}
        )
        bot.delete_message(message.chat.id, msg.message_id)
        
        if output and isinstance(output, list):
            bot.send_message(message.chat.id, f"✅ Видео готово!\n{output[0]}")
        elif output:
            bot.send_message(message.chat.id, f"✅ Видео готово!\n{output}")
        else:
            bot.send_message(message.chat.id, "❌ Не удалось получить видео")
            
    except Exception as e:
        bot.edit_message_text(f"❌ Ошибка видео: {str(e)}", message.chat.id, msg.message_id)

@bot.message_handler(commands=['image'])
def generate_image(message):
    prompt = message.text.replace('/image', '').strip()
    if not prompt:
        bot.reply_to(message, "Что именно нарисовать?")
        return
        
    msg = bot.reply_to(message, "🎨 Рисую...")
    try:
        response = openai.Image.create(
            prompt=prompt,
            n=1,
            size="1024x1024"
        )
        image_url = response['data'][0]['url']
        bot.delete_message(message.chat.id, msg.message_id)
        bot.send_photo(message.chat.id, image_url, caption=f"✅ {prompt}")
        
    except Exception as e:
        bot.edit_message_text(f"❌ Ошибка: {str(e)}", message.chat.id, msg.message_id)

# Главный умный обработчик
@bot.message_handler(func=lambda message: True)
def smart_handler(message):
    # Показываем что печатает
    bot.send_chat_action(message.chat.id, 'typing')
    
    try:
        # Отправляем запрос в OpenAI
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": message.text}
            ]
        )
        
        answer = response.choices[0].message.content.strip()
        
        # Если OpenAI предлагает команду — выполняем
        if answer.startswith('/video'):
            # Извлекаем запрос и вызываем функцию видео
            prompt = answer.replace('/video', '').strip()
            generate_video_with_text(message, prompt)
        elif answer.startswith('/image'):
            # Извлекаем запрос и вызываем функцию картинки
            prompt = answer.replace('/image', '').strip()
            generate_image_with_text(message, prompt)
        else:
            # Просто отвечаем
            bot.reply_to(message, answer)
            
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {str(e)}")

# Вспомогательные функции для вызова из умного обработчика
def generate_video_with_text(message, prompt):
    msg = bot.reply_to(message, "🎥 Делаю видео...")
    try:
        output = replicate.run(
            "lucataco/animate-diff:beecf59c4aee8d81bf04f0381033dfa10dc16e845b4ae00d281e2fa377e48a9f",
            input={"prompt": prompt}
        )
        bot.delete_message(message.chat.id, msg.message_id)
        
        if output and isinstance(output, list):
            bot.send_message(message.chat.id, f"✅ Вот видео: {output[0]}")
        elif output:
            bot.send_message(message.chat.id, f"✅ Вот видео: {output}")
        else:
            bot.send_message(message.chat.id, "❌ Не вышло")
    except Exception as e:
        bot.edit_message_text(f"❌ Ошибка: {str(e)}", message.chat.id, msg.message_id)

def generate_image_with_text(message, prompt):
    msg = bot.reply_to(message, "🎨 Рисую...")
    try:
        response = openai.Image.create(
            prompt=prompt,
            n=1,
            size="1024x1024"
        )
        image_url = response['data'][0]['url']
        bot.delete_message(message.chat.id, msg.message_id)
        bot.send_photo(message.chat.id, image_url, caption=f"✅ {prompt}")
    except Exception as e:
        bot.edit_message_text(f"❌ Ошибка: {str(e)}", message.chat.id, msg.message_id)

if __name__ == "__main__":
    print("🚀 Умный бот запущен!")
    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            print(f"Ошибка: {e}")
            time.sleep(5)
