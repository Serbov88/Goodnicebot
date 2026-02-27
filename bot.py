@bot.message_handler(content_types=['photo'])
def animate_photo(message):
    """Оживление фотографии через прямой API-запрос"""
    msg = bot.reply_to(message, "🎬 Оживляю фото... Это займет около минуты")
    logger.info(f"Получено фото от пользователя {message.from_user.id}")
    
    try:
        # 1. Скачиваем фото
        file_info = bot.get_file(message.photo[-1].file_id)
        photo = bot.download_file(file_info.file_path)
        logger.info(f"Фото скачано, размер: {len(photo)} байт")
        
        # 2. Сохраняем временно
        temp_filename = f"temp_{message.from_user.id}_{int(time.time())}.jpg"
        with open(temp_filename, 'wb') as f:
            f.write(photo)
        
        # 3. Отправляем через прямой API-запрос
        import requests
        
        with open(temp_filename, 'rb') as f:
            # Сначала загружаем файл
            files = {'file': f}
            upload_response = requests.post(
                "https://api.replicate.com/v1/files",
                headers={"Authorization": f"Token {REPLICATE_TOKEN}"},
                files=files
            )
            
            if upload_response.status_code == 201:
                file_url = upload_response.json()['urls']['get']
                
                # Создаём предсказание с правильными параметрами
                prediction_response = requests.post(
                    "https://api.replicate.com/v1/predictions",
                    headers={
                        "Authorization": f"Token {REPLICATE_TOKEN}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "version": "stability-ai/stable-video-diffusion:3f0457e4619daac51203dedb472816fd4af51f3149fa7a9e0b5ffcf1b8172438",
                        "input": {
                            "input_image": file_url,
                            "video_length": "14_frames_with_svd",
                            "sizing_strategy": "maintain_aspect_ratio",
                            "frames_per_second": 6
                        }
                    }
                )
                
                if prediction_response.status_code == 201:
                    data = prediction_response.json()
                    bot.delete_message(message.chat.id, msg.message_id)
                    bot.send_message(
                        message.chat.id, 
                        f"✅ Фото в обработке!\n"
                        f"ID: {data['id']}\n"
                        f"Статус: {data['status']}\n"
                        f"Через минуту видео будет готово, ссылка: {data['urls']['get']}"
                    )
                else:
                    bot.edit_message_text(
                        f"❌ Ошибка создания предсказания: {prediction_response.status_code}\n{prediction_response.text}", 
                        message.chat.id, msg.message_id
                    )
            else:
                bot.edit_message_text(
                    f"❌ Ошибка загрузки фото: {upload_response.status_code}\n{upload_response.text}", 
                    message.chat.id, msg.message_id
                )
        
        # 4. Удаляем временный файл
        os.remove(temp_filename)
        
    except Exception as e:
        error_text = f"❌ Ошибка оживления: {str(e)}"
        bot.edit_message_text(error_text, message.chat.id, msg.message_id)
        logger.error(f"Ошибка оживления: {str(e)}")
        
        try:
            os.remove(temp_filename)
        except:
            pass
