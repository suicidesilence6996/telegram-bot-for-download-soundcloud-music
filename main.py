import os
import time
import telebot
import yt_dlp

BOT_TOKEN = "ТОКЕН-ВАШЕГО-БОТА"
bot = telebot.TeleBot(BOT_TOKEN)

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


@bot.message_handler(commands=["start"])
def send_welcome(message):
    bot.reply_to(
        message,
        "Привет! Отправь мне ссылку на трек из SoundCloud, и я пришлю аудиофайл."
    )


@bot.message_handler(func=lambda message: True)
def handle_soundcloud(message):
    if not message.text:
        bot.reply_to(message, "Пожалуйста, отправь текстовую ссылку на трек с SoundCloud.")
        return

    url = message.text.strip()

    if "soundcloud.com" not in url:
        bot.reply_to(message, "Пожалуйста, отправь корректную ссылку на трек с SoundCloud.")
        return

    status_msg = bot.reply_to(message, "⏳ Ищу и скачиваю трек...")

    unique_id = f"{message.chat.id}_{int(time.time() * 1000)}"
    output_template = os.path.join(DOWNLOAD_DIR, f"{unique_id}.%(ext)s")
    downloaded_file = None

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": output_template,
        "noplaylist": True,
        "quiet": True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            downloaded_file = ydl.prepare_filename(info)
            title = info.get("title", "SoundCloud Track")
            performer = info.get("uploader", "Unknown Artist")

        file_size_mb = os.path.getsize(downloaded_file) / (1024 * 1024)
        if file_size_mb > 49.5:
            bot.edit_message_text(
                f"❌ Файл слишком большой ({file_size_mb:.1f} МБ). Telegram разрешает отправлять до 50 МБ.",
                message.chat.id,
                status_msg.message_id
            )
            return

        bot.edit_message_text("📤 Отправляю аудио в чат...", message.chat.id, status_msg.message_id)

        with open(downloaded_file, "rb") as audio:
            bot.send_audio(
                message.chat.id,
                audio,
                title=title,
                performer=performer
            )

        bot.delete_message(message.chat.id, status_msg.message_id)

    except Exception as e:
        bot.edit_message_text(
            "❌ Не удалось скачать трек. Возможно, он недоступен или ссылка неверна.",
            message.chat.id,
            status_msg.message_id
        )
        print(f"Ошибка: {e}")

    finally:
        if downloaded_file and os.path.exists(downloaded_file):
            os.remove(downloaded_file)


if __name__ == "__main__":
    print("Бот запущен...")
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
