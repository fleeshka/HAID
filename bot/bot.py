import os
import logging
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
# from cohere_nlp import nlp_generate
from olama import extract_products_with_ai, recomend_recipies
from redis_client import save_context, get_context, reset_context, set_state, get_state 
import re


# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    user_first_name = update.message.from_user.first_name
    user_id = update.message.from_user.id
    set_state(user_id, "start")
    await update.message.reply_text(
        f'Привет, {user_first_name}! Я — твой AI помощник по продуктам и рецептам.\n\n'
        'Ты можешь спросить:\n'
        '- Где дешевле купить проудкты\n'
        '- Что приготовить из твоих ингредиентов\n'
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
    try:
        user_id = update.message.from_user.id
        user_message = update.message.text.strip()
        state = get_state(user_id)

        if state == "start":
            save_context(user_id, "from_user", user_message)
            extracted_products = extract_products_with_ai(user_message)
            save_context(user_id, "products_extracted", extracted_products)
            set_state(user_id, "waiting_for_confirmation")

            text = f"Хорошо! Я вижу, ты хочешь купить: {extracted_products}. Правильно?"
            keyboard = ReplyKeyboardMarkup(
                [["Да, всё верно", "Хочу изменить список"]],
                one_time_keyboard=True,
                resize_keyboard=True
            )
            await update.message.reply_text(text, reply_markup=keyboard)
            return

        elif state == "waiting_for_confirmation":
            if "да" in user_message.lower():
                set_state(user_id, "confirmed")
                await update.message.reply_text("Отлично! Переходим к следующему шагу...")
                
            elif "изменить список" in user_message.lower():
                reset_context(user_id)
                set_state(user_id, "start")
                await update.message.reply_text("Хорошо, отправь список продуктов заново.")
            else:
                await update.message.reply_text("Пожалуйста, выбери: 'Да, всё верно' или 'Хочу изменить список'.")
            return

        elif state == "confirmed":
            provided_recipes = recomend_recipies(get_context(user_id, "products_extracted"))
            await update.message.reply_text(provided_recipes)
            set_state(user_id, "done")
            return

        elif state == "waiting_for_input":
            # update product list 
            save_context(user_id, "from_user", user_message)
            extracted_products = extract_products_with_ai(user_message)
            save_context(user_id, "products_extracted", extracted_products)
            set_state(user_id, "waiting_for_confirmation")

            text = f"Обновлённый список: {extracted_products}. Всё правильно?"
            keyboard = ReplyKeyboardMarkup(
                [["Да, всё верно", "Хочу изменить список"]],
                one_time_keyboard=True,
                resize_keyboard=True
            )
            await update.message.reply_text(text, reply_markup=keyboard)
            return

        else:
            # unknown state 
            reset_context(user_id)
            set_state(user_id, "start")
            await update.message.reply_text("Что-то пошло не так. Давай начнём сначала. Напиши список продуктов.")
            return

    except Exception as e:
        logger.error(f"Ошибка: {str(e)}")
        await update.message.reply_text("❌ Ошибка при обработке сообщения. Попробуй ещё раз.")



def main():
    """Start the bot."""
    token = os.getenv('TELEGRAM_TOKEN')
    if not token:
        raise ValueError("TELEGRAM_TOKEN не найден в переменных окружения")

    application = Application.builder().token(token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))

    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        handle_message
    ))

    application.run_polling(allowed_updates=Update.ALL_TYPES)


    
if __name__ == '__main__':
    main()
