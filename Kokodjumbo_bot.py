import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from openai import OpenAI

# 🔐 Токены
TELEGRAM_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
OPENAI_API_KEY = "YOUR_OPENAI_API_KEY"

# OpenAI клиент
client = OpenAI(api_key=OPENAI_API_KEY)

# Логирование
logging.basicConfig(level=logging.INFO)

# Максимальная длина истории сообщений
MAX_HISTORY_LEN = 10


# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я бот на базе ChatGPT. Напиши мне что-нибудь, и я отвечу.\n"
        "Хочешь картинку? Напиши: 'сгенерируй картинку: арбуз на пляже'."
    )
    context.user_data["history"] = []


# Команда /stop
async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Бот остановлен. До встречи!")
    await context.application.stop()


# Обработка сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text.strip()

    # Обработка генерации изображения отдельно
    if "сгенерируй картинку:" in user_input.lower():
        prompt_start = user_input.lower().find("сгенерируй картинку:")
        image_prompt = user_input[prompt_start + len("сгенерируй картинку:"):].strip()

        if not image_prompt:
            await update.message.reply_text("Укажи, что нарисовать после 'сгенерируй картинку:'.")
            return

        try:
            image_response = client.images.generate(
                model="dall-e-3",
                prompt=image_prompt,
                size="1024x1024",
                n=1
            )
            image_url = image_response.data[0].url
            await update.message.reply_photo(photo=image_url, caption="Вот твоя картинка:")
        except Exception as e:
            logging.error(f"Ошибка генерации картинки: {e}")
            await update.message.reply_text(f"Ошибка при генерации картинки:\n{e}")
        return  # прекращаем обработку после отправки изображения

    # История чата
    history = context.user_data.get("history", [])
    history.append({"role": "user", "content": user_input})
    history = history[-MAX_HISTORY_LEN:]

    try:
        chat_response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=history
        )
        reply_text = chat_response.choices[0].message.content.strip()

        history.append({"role": "assistant", "content": reply_text})
        context.user_data["history"] = history[-MAX_HISTORY_LEN:]

        await update.message.reply_text(reply_text)
    except Exception as e:
        logging.error(f"Ошибка при обращении к ChatGPT: {e}")
        await update.message.reply_text(f"Ошибка при обращении к ChatGPT:\n{e}")


# Основной запуск
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logging.info("Бот запущен...")
    app.run_polling()


if __name__ == "__main__":
    main()
