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

# Токены
TELEGRAM_TOKEN = "***"
OPENAI_API_KEY = "***"

client = OpenAI(api_key=OPENAI_API_KEY)
logging.basicConfig(level=logging.INFO)

MAX_HISTORY_LEN = 10  # максимальное число сообщений в истории

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я бот на базе ChatGPT. Напиши мне что-нибудь, и я отвечу. "
        "Если хочешь картинку — добавь в запрос фразу 'сгенерируй картинку:'."
    )
    # Инициализируем историю для пользователя
    context.user_data['history'] = []

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Бот остановлен. До встречи!")
    await context.application.stop()

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text.strip()
    history = context.user_data.get('history', [])

    # Добавляем в историю новое сообщение от пользователя
    history.append({"role": "user", "content": user_input})

    # Обрезаем историю, если слишком длинная
    if len(history) > MAX_HISTORY_LEN:
        history = history[-MAX_HISTORY_LEN:]

    try:
        chat_response = client.chat.completions.create(
            model="gpt-4.1-nano",
            messages=history
        )
        reply_text = chat_response.choices[0].message.content.strip()

        # Добавляем ответ в историю
        history.append({"role": "assistant", "content": reply_text})
        if len(history) > MAX_HISTORY_LEN:
            history = history[-MAX_HISTORY_LEN:]

        # Сохраняем обновленную историю
        context.user_data['history'] = history

        await update.message.reply_text(reply_text)
    except Exception as e:
        logging.error(f"Ошибка при обращении к ChatGPT: {e}")
        await update.message.reply_text(f"Ошибка при обращении к ChatGPT:\n{e}")
        return

    # Генерация изображения
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

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logging.info("Бот запущен...")
    app.run_polling()

if __name__ == "__main__":
    main()

