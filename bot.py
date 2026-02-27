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

# Команда /start
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, 
        "👋 Привет! Я SceneForgeBot!\n\n"
        "🎬 **/video** текст — видео из текста\n"
        "🖼️ **/image** текст — картинка\n"
        "💬 **/chat** текст — общение\n"
        "📋 **/help** — список команд"
    )

@bot.message_handler(commands=['help'])
def help(message):
    bot.reply_to(message,
        "📋 **Команды:**\n"
        "/video робот танцует — видео\n"
        "/image кот в космосе — картинка\n"
        "/chat как дела? — общение"
    )

# Генерация видео из текста (Haiper)
@bot.message_handler(commands=['video'])
def generate_video(message):
    prompt = message.text.replace('/video', '').strip()
    if not prompt:
        bot.reply_to(message, "Напиши запрос после /video")
        return
        
    msg = bot.reply_to(message, "🎥 Генерирую видео из текста...")
    try:
        output = replicate.run(
            "haiper-ai/haiper-video-2:latest",
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

# Генерация картинки через OpenAI DALL-E
@bot.message_handler(commands=['image'])
def generate_image(message):
    prompt = message.text.replace('/image', '').strip()
    if not prompt:
        bot.reply_to(message, "Напиши запрос после /image")
        return
        
    msg = bot.reply_to(message, "🎨 Рисую картинку...")
    try:
        response = openai.Image.create(
            prompt=prompt,
            n=1,
            size="1024x1024"
        )
        image_url = response['data'][0]['url']
        bot.delete_message(message.chat.id, msg.message_id)
        bot.send_photo(message.chat.id, image_url, caption=f"✅ Картинка: {prompt}")
        
    except Exception as e:
        bot.edit_message_text(f"❌ Ошибка картинки: {str(e)}", message.chat.id, msg.message_id)

# Обычный диалог через ChatGPT
@bot.message_handler(commands=['chat'])
def chat(message):
    prompt = message.text.replace('/chat', '').strip()
    if not prompt:
        bot.reply_to(message, "Напиши сообщение после /chat")
        return
        
    msg = bot.reply_to(message, "💬 Думаю...")
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        answer = response.choices[0].message.content
        bot.delete_message(message.chat.id, msg.message_id)
        bot.send_message(message.chat.id, f"💬 {answer}")
        
    except Exception as e:
        bot.edit_message_text(f"❌ Ошибка чата: {str(e)}", message.chat.id, msg.message_id)

# Запуск
if __name__ == "__main__":
    print("🚀 Бот запущен с видео (Haiper), фото (DALL-E) и чатом (ChatGPT)!")
    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            print(f"Ошибка: {e}")
            time.sleep(5)
