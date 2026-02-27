import os
import telebot
import replicate
import time
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Токены из переменных окружения
BOT_TOKEN = os.environ.get('BOT_TOKEN')
REPLICATE_TOKEN = os.environ.get('REPLICATE_TOKEN')

# Проверка токенов
if not BOT_TOKEN:
    raise ValueError("❌ Отсутствует BOT_TOKEN")
if not REPLICATE_TOKEN:
    raise ValueError("❌ Отсутствует REPLICATE_TOKEN")

# Устанавливаем токен Replicate
os.environ["REPLICATE_API_TOKEN"] = REPLICATE_TOKEN

# Создаем бота
bot = telebot.TeleBot(BOT_TOKEN)
logger.info("✅ Бот инициализирован")

# ============================================
# КОМАНДА /start
# ============================================
@bot.message_handler(commands=['start'])
def start(message):
    """Приветствие и инструкции"""
    welcome_text = (
        "👋 Привет! Я SceneForgeBot (финальная версия)!\n\n"
        "📸 **Отправь фото** — я оживлю его\n"
        "🎬 **/video текст** — видео из текста\n\n"
        "⚡ Все функции работают!"
    )
    bot.reply_to(message, welcome_text)
    logger.info(f"Команда /start от пользователя {message.from_user.id}")

# ============================================
# ВИДЕО ИЗ ТЕКСТА
# ============================================
@bot.message_handler(commands=['video'])
def generate_video(message):
    """Генерация видео из текста"""
    prompt = message.text.replace('/video', '').strip()
    if not prompt:
        bot.reply_to(message, "❌ Напиши запрос после /video, например: /video робот танцует")
        return
    
    msg = bot.reply_to(message, "🎥 Генерирую видео из текста... (около 30 секунд)")
    logger.info(f"Запрос видео: {prompt[:50]}... от пользователя {message.from_user.id}")
    
    try:
        output = replicate.run(
            "lucataco/animate-diff:beecf59c4aee8d81bf04f0381033dfa10dc16e845b4ae00d281e2fa377e48a9f",
            input={"prompt": prompt}
        )
        
        bot.delete_message(message.chat.id, msg.message_id)
        
        # Извлекаем ссылку на видео
        if isinstance(output, list):
            video_url = output[0]
        elif isinstance(output, str):
            video_url = output
        else:
            video_url = str(output)
            
        bot.send_message(message.chat.id, f"✅ Видео готово!\n{video_url}")
        logger.info(f"Видео успешно сгенерировано для пользователя {message.from_user.id}")
        
    except Exception as e:
        error_text = f"❌ Ошибка видео: {str(e)}"
        bot.edit_message_text(error_text, message.chat.id, msg.message_id)
        logger.error(f"Ошибка видео: {str(e)}")

# ============================================
# ОЖИВЛЕНИЕ ФОТО ЧЕРЕЗ MINIMAX
# ============================================
@bot.message_handler(content_types=['photo'])
def animate_photo(message):
    """Оживление фотографии через Minimax"""
    msg = bot.reply_to(message, "🎬 Оживляю фото через Minimax... Это займет около минуты")
    logger.info(f"Получено фото от пользователя {message.from_user.id}")
    
    temp_filename = None
    
    try:
        # 1. Скачиваем фото
        file_info = bot.get_file(message.photo[-1].file_id)
        photo = bot.download_file(file_info.file_path)
        logger.info(f"Фото скачано, размер: {len(photo)} байт")
        
        # 2. Сохраняем временно
        temp_filename = f"temp_{message.from_user.id}_{int(time.time())}.jpg"
        with open(temp_filename, 'wb') as f:
            f.write(photo)
        
        # 3. Отправляем в Minimax
        with open(temp_filename, 'rb') as f:
            output = replicate.run(
                "minimax/video-01:latest",
                input={
                    "prompt": "make this photo come alive, natural movement",
                    "image": f
                }
            )
        
        # 4. Удаляем временный файл
        if temp_filename and os.path.exists(temp_filename):
            os.remove(temp_filename)
            logger.info("Временный файл удален")
        
        # 5. Отправляем результат
        bot.delete_message(message.chat.id, msg.message_id)
        
        if isinstance(output, list):
            video_url = output[0]
        else:
            video_url = output
            
        bot.send_message(message.chat.id, f"✅ Фото ожило!\n{video_url}")
        logger.info(f"Фото успешно оживлено для пользователя {message.from_user.id}")
        
    except Exception as e:
        error_text = f"❌ Ошибка оживления: {str(e)}"
        
        # Пробуем отредактировать сообщение, если оно ещё существует
        try:
            bot.edit_message_text(error_text, message.chat.id, msg.message_id)
        except:
            bot.reply_to(message, error_text)
            
        logger.error(f"Ошибка оживления: {str(e)}")
        
        # Пробуем удалить временный файл в случае ошибки
        try:
            if temp_filename and os.path.exists(temp_filename):
                os.remove(temp_filename)
        except:
            pass

# ============================================
# ЗАПУСК БОТА
# ============================================
if __name__ == "__main__":
    logger.info("=" * 50)
    logger.info("🚀 Финальная версия бота запускается...")
    logger.info(f"🤖 Bot Token: {'✅' if BOT_TOKEN else '❌'}")
    logger.info(f"🔄 Replicate Token: {'✅' if REPLICATE_TOKEN else '❌'}")
    logger.info("=" * 50)
    
    # Бесконечный цикл с обработкой ошибок
    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            logger.error(f"Ошибка в основном цикле: {e}")
            time.sleep(5)
