import os
import logging
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
# from cohere_nlp import nlp_generate
from olama import extract_products_with_ai, recomend_recipies, update_products_with_ai
from redis_client import save_context, get_context, reset_context, set_state, get_state, get_extracted_products, get_provided_recipes
import re


# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def send_image(path, update: Update, context: ContextTypes.DEFAULT_TYPE):
    image_path = path
    with open(image_path, "rb") as image:
        await update.message.reply_photo(photo=image)

        
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    image_path = "bot/img/img3.png"  
    with open(image_path, "rb") as image:
        await update.message.reply_photo(photo=image)
    user_first_name = update.message.from_user.first_name
    user_id = update.message.from_user.id
    reset_context(user_id)
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
            # save first origing message 
            save_context(user_id, "from_user", user_message)
            extracted_products = extract_products_with_ai(user_message)
            # save extracted products
            save_context(user_id, "products_extracted", extracted_products)
            set_state(user_id, "waiting_for_confirmation")

            text = f"Хорошо! Я вижу, ты хочешь купить: {extracted_products}. Всё верно?"

            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("Да, всё верно", callback_data="confirm_extracted_list")],
                [InlineKeyboardButton("Хочу изменить список", callback_data="regect_extracted_list")]
            ])
            await update.message.reply_text(text, reply_markup=keyboard)
            return

        elif state == "confirmed":
            provided_recipes = recomend_recipies(get_context(user_id, "products_extracted"))
    

            await update.message.reply_text(provided_recipes)

            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("Добавить новые продукты", callback_data="add_new")],
                [InlineKeyboardButton("Ничего не добавляй", callback_data="no_add")]
            ])
            await update.message.reply_text("Хочешь что-то добавить?", reply_markup=keyboard)

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

        elif state == "additional":
            if "новые продукты" in user_message.lower():
                new_prodcut_list = update_products_with_ai(get_context(user_id, "products_extracted"))
            elif "не добавляй" in user_message.lower():
                set_state(user_id, "price")
                await update.message.reply_text("Хорошо ничего не меняем.")
            else: 
                await update.message.reply_text("Пожалуйста, выбери: 'Да, всё верно' или 'Хочу изменить список'.")
            return

        elif state == "waiting_for_input":
            # update product list 
            save_context(user_id, "from_user", user_message)
            extracted_products = extract_products_with_ai(user_message)
            save_context(user_id, "products_extracted", extracted_products)
            set_state(user_id, "waiting_for_confirmation")

            text = f"Обновлённый список: {extracted_products}. Всё правильно?"
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("Все верно", callback_data="upd_ok")],
                [InlineKeyboardButton("Нет, не так", callback_data="no_upd")]
            ])
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


async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    if query.data == "confirm_extracted_list":
        set_state(user_id, "confirmed")
        products_extracted = get_extracted_products(user_id)
        recepies = get_provided_recipes(user_id)
        await query.edit_message_text(f"Вот твой готовый список:\n {products_extracted}.")

        provided_recipes = recomend_recipies(products_extracted)
        save_context(user_id, "provided_recipes", provided_recipes)
        await query.message.reply_text(provided_recipes)

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("Добавить новые продукты", callback_data="add_new")],
            [InlineKeyboardButton("Ничего не добавляй", callback_data="no_add")]
        ])
        await query.message.reply_text("Хочешь добавим недостающие продкуты в корзину?", reply_markup=keyboard)

    elif query.data == "regect_extracted_list":
        reset_context(user_id)
        set_state(user_id, "start")
        await query.edit_message_reply_markup(reply_markup=None)
        await query.edit_message_text("Хорошо, давай попробуем снова. Отправь список продуктов заново.")

    elif query.data == "add_new":
        set_state(user_id, "additional")

        products_extracted = get_extracted_products(user_id)
        recipes = get_context(user_id).get("provided_recipes")

        fresh_list = update_products_with_ai(products_extracted, recipes)
        result = "\n".join(products_extracted.split(", ") + fresh_list.split(", "))

        await query.edit_message_text(f"Вот твой готовый список:\n {result}.")

    elif query.data == "no_add":
        set_state(user_id, "price")
        await query.edit_message_text("Хорошо,как скажешь, ничего не добавляем")



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
    application.add_handler(CallbackQueryHandler(handle_callback_query))


    application.run_polling(allowed_updates=Update.ALL_TYPES)


    
if __name__ == '__main__':
    main()
