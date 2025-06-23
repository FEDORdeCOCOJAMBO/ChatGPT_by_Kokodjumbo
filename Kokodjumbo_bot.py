import logging
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
from openai import OpenAI

# Токены (замени на свои)
TELEGRAM_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
OPENAI_API_KEY = "YOUR_OPENAI_API_KEY"

# Инициализация OpenAI клиента
client = OpenAI(api_key=OPENAI_API_KEY)

# Логирование
logging.basicConfig(level=logging.INFO)

# Список доступных моделей для переключения
AVAILABLE_MODELS = ["gpt-3.5-turbo", "gpt-4", "gpt-4o-mini"]

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Установим модель по умолчанию для пользователя, если не установлена
    if "model" not in context.user_data:
        context.user_data["model"] = "gpt-3.5-turbo"

    await update.message.reply_text(
        f"Привет! Сейчас используется модель: {context.user_data['model']}\n"
        "Напиши что-нибудь, и я отвечу.\n"
        "Чтобы сменить модель, введи /model"
    )

# Команда /model - показать кнопки выбора модели
async def model_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton(model, callback_data=model)] for model in AVAILABLE_MODELS
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Выбери модель:", reply_markup=reply_markup)

# Обработчик нажатия кнопок выбора модели
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    selected_model = query.data
    context.user_data["model"] = selected_model

    await query.edit_message_text(text=f"Модель успешно переключена на: {selected_model}")

# Обработка текстовых сообщений с учётом выбранной модели
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text.strip()
    model = context.user_data.get("model", "gpt-3.5-turbo")

    try:
        chat_response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": user_input}]
        )
        reply_text = chat_response.choices[0].message.content.strip()
        await update.message.reply_text(f"[{model}]: {reply_text}")
    except Exception as e:
        logging.error(f"Ошибка при обращении к ChatGPT: {e}")
        await update.message.reply_text(f"Ошибка при обращении к ChatGPT:\n{e}")

# Главная функция
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("model", model_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logging.info("Бот запущен...")
    app.run_polling()

if __name__ == "__main__":
    main()
