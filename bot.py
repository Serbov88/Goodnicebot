import os
import telebot
import replicate
import openai
import requests
import time
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Токены из переменных окружения
BOT_TOKEN = os.environ.get('BOT_TOKEN')
REPLICATE_TOKEN = os.environ.get('REPLICATE_TOKEN')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')

# Проверка наличия токенов
missing_tokens = []
if not BOT_TOKEN:
    missing_tokens.append('BOT_TOKEN')
if not REPLICATE_TOKEN:
    missing_tokens.append('REPLICATE_TOKEN')
if not OPENAI_API_KEY:
    missing_tokens.append('OPENAI_API_KEY')

if missing_tokens:
    error_msg = f"❌ Отсутствуют токены: {', '.join(missing_tokens)}"
    logger.error(error_msg)
    raise ValueError(error_msg)

# Устанавливаем токены
os.environ["REPLICATE_API_TOKEN"] = REPLICATE_TOKEN
openai.api_key = OPENAI_API_KEY

# Создаем экземпляр бота
bot = telebot.TeleBot(BOT_TOKEN)
logger.info("✅ Бот инициализирован")

@bot.message_handler(commands=['start'])
def start(message):
    """Обработчик команды /start"""
    welcome_text = (
        "👋 Привет! Я SceneForgeBot (полная версия)!\n\n"
        "📸 **Отправь фото** — я оживлю его\n"
        "🎬 **/video текст** — видео из текста\n"
        "💬 **Просто напиши** — я отвечу как ChatGPT\n\n"
        "⚙️ Все функции работают!"
    )
    bot.reply_to(message, welcome_text)
    logger.info(f"Команда /start от пользователя {message.from_user.id}")

@bot.message_handler(commands=['video'])
def generate_video(message):
    """Генерация видео из текста"""
    prompt = message.text.replace('/video', '').strip()
    if not prompt:
        bot.reply_to(message, "❌ Напиши запрос после /video, например: /video робот танцует")
        return
    
    msg = bot.reply_to(message, "🎥 Генерирую видео из текста... (это займет ~30 секунд)")
    logger.info(f"Запрос видео: {prompt} от пользователя {message.from_user.id}")
    
    try:
        output = replicate.run(
            "lucataco/animate-diff:beecf59c4aee8d81bf04f0381033dfa10dc16e845b4ae00d281e2fa377e48a9f",
            input={"prompt": prompt}
        )
        
        bot.delete_message(message.chat.id, msg.message_id)
        video_url = output[0] if isinstance(output, list) else output
        bot.send_message(message.chat.id, f"✅ Видео готово!\n{video_url}")
        logger.info(f"Видео успешно сгенерировано для пользователя {message.from_user.id}")
        
    except Exception as e:
        error_text = f"❌ Ошибка генерации видео: {str(e)}"
        bot.edit_message_text(error_text, message.chat.id, msg.message_id)
        logger.error(f"Ошибка видео для пользователя {message.from_user.id}: {str(e)}")

@bot.message_handler(content_types=['photo'])
def animate_photo(message):
    """Оживление фотографии"""
    msg = bot.reply_to(message, "🎬 Оживляю фото... (это займет ~1 минуту)")
    logger.info(f"Получено фото от пользователя {message.from_user.id}")
    
    try:
        # Скачиваем фото
        file_info = bot.get_file(message.photo[-1].file_id)
        photo = bot.download_file(file_info.file_path)
        logger.info(f"Фото скачано, размер: {len(photo)} байт")
        
        # Сохраняем временно
        temp_filename = f"temp_photo_{message.from_user.id}_{int(time.time())}.jpg"
        with open(temp_filename, 'wb') as f:
            f.write(photo)
        
        # Отправляем в Replicate
        with open(temp_filename, 'rb') as f:
            response = requests.post(
                "https://api.replicate.com/v1/predictions",
                headers={"Authorization": f"Token {REPLICATE_TOKEN}"},
                files={"file": f},
                data={
                    "version": "haiper-ai/haiper-video-2:latest",
                    "input": '{"image": "file", "prompt": "make the person move naturally, subtle animation"}'
                }
            )
        
        # Удаляем временный файл
        os.remove(temp_filename)
        
        if response.status_code == 201:
            data = response.json()
            bot.delete_message(message.chat.id, msg.message_id)
            
            # Отправляем ID предсказания
            bot.send_message(
                message.chat.id, 
                f"✅ Фото отправлено на обработку!\n"
                f"ID: `{data['id']}`\n"
                f"Статус: {data['status']}\n"
                f"Через 1-2 минуты видео будет готово. Ссылка появится в логах."
            )
            logger.info(f"Фото успешно отправлено в Replicate, ID: {data['id']}")
        else:
            error_msg = f"❌ Ошибка Replicate: {response.status_code}\n{response.text[:200]}"
            bot.edit_message_text(error_msg, message.chat.id, msg.message_id)
            logger.error(f"Ошибка Replicate: {response.status_code} - {response.text[:200]}")
            
    except Exception as e:
        bot.edit_message_text(f"❌ Ошибка при оживлении: {str(e)}", message.chat.id, msg.message_id)
        logger.error(f"Ошибка оживления: {str(e)}")

@bot.message_handler(func=lambda message: True)
def chat(message):
    """Обычный чат с OpenAI"""
    bot.send_chat_action(message.chat.id, 'typing')
    logger.info(f"Чат-запрос от пользователя {message.from_user.id}: {message.text[:50]}...")
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Ты дружелюбный помощник по имени SceneForgeBot. Ты умеешь оживлять фото и делать видео из текста."},
                {"role": "user", "content": message.text}
            ],
            max_tokens=500,
            temperature=0.7
        )
        
        answer = response.choices[0].message.content
        bot.reply_to(message, answer)
        logger.info(f"Ответ OpenAI отправлен пользователю {message.from_user.id}")
        
    except Exception as e:
        error_msg = f"❌ Ошибка OpenAI: {str(e)}"
        bot.reply_to(message, error_msg)
        logger.error(f"Ошибка OpenAI для пользователя {message.from_user.id}: {str(e)}")

if __name__ == "__main__":
    logger.info("=" * 50)
    logger.info("🚀 Бот запускается...")
    logger.info(f"🤖 Bot Token: {'✅' if BOT_TOKEN else '❌'}")
    logger.info(f"🔄 Replicate Token: {'✅' if REPLICATE_TOKEN else '❌'}")
    logger.info(f"🤖 OpenAI Key: {'✅' if OPENAI_API_KEY else '❌'}")
    logger.info("=" * 50)
    
    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            logger.error(f"Ошибка в основном цикле: {e}")
            time.sleep(5)
