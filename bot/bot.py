import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
# from cohere_nlp import nlp_generate
from olama import olama_nlp_generate


# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize product manager

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    user_first_name = update.message.from_user.first_name
    await update.message.reply_text(
        '👋 Привет, {user_first_name}! Я — твой AI помощник по продуктам и рецептам.\n\n'
        'Ты можешь спросить:\n'
        '- Где дешевле купить [продукт]\n'
        '- Что приготовить из [ингредиента]\n'
        '- Или просто отправить список: "Хочу сделать блины, купить молоко и хлеб"'
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /help is issued."""
    await update.message.reply_text(
        '📌 Команды:\n'
        '/start — запуск бота\n'
        '/help — помощь\n\n'
        'Примеры запросов:\n'
        '- "Где купить сыр?"\n'
        '- "Что приготовить из картошки?"\n'
        '- "Хочу сделать борщ и купить молоко"'
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming messages and generate responses."""
    try:
        user_message = update.message.text.lower()

        # Use Cohere NLP to extract structured products
        ai_response = olama_nlp_generate(user_message)
        await update.message.reply_text(ai_response)

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        await update.message.reply_text(
            " Ошибка при обработке сообщения. Попробуйте позже."
        )

def main():
    """Start the bot."""
    token = os.getenv('TELEGRAM_TOKEN')
    if not token:
        raise ValueError(" TELEGRAM_TOKEN не найден в переменных окружения")

    application = Application.builder().token(token).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.run_polling(allowed_updates=Update.ALL_TYPES)


    
if __name__ == '__main__':
    main()
