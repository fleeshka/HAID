import os
import logging
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
import sys
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from src.api_handler import get_products
from src.recomender import recommend
from olama import extract_products_with_ai, recomend_recipies, update_products_with_ai
from redis_client import save_context, get_context, reset_context, set_state, get_state, get_extracted_products, get_provided_recipes
import re


load_dotenv()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def send_image(image_path: str, update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if update.message:
            with open(image_path, "rb") as image:
                await update.message.reply_photo(photo=image)
        elif update.callback_query:
            with open(image_path, "rb") as image:
                await update.callback_query.message.reply_photo(photo=image)
    except Exception as e:
        logger.error(f"Ошибка при отправке изображения: {str(e)}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    if update.message is None or update.message.text is None:
        return

    user_first_name = update.message.from_user.first_name
    user_id = update.message.from_user.id
    reset_context(user_id)
    set_state(user_id, "start")
    
    await send_image("bot/img/img3.png", update, context)

    await update.message.reply_text(
        f'👋 Привет, {user_first_name}! Я — твой AI помощник по продуктам и рецептам.\n\n'

        'Ты можешь спросить:\n'
        '- Где дешевле купить продукты\n'
        '- Что приготовить из твоих ингредиентов\n'
        '- Или просто отправить список: "Хочу сделать блины, купить молоко и хлеб"'
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /help is issued."""
    if update.message is None or update.message.text is None:
        return

    await update.message.reply_text(
        '📌 Команды:\n'
        '/start — запуск бота\n'
        '/help — помощь\n\n'
        'Примеры запросов:\n'
        '- "Где купить сыр?"\n'
        '- "Что приготовить из картошки?"\n'
        '- "Хочу сделать борщ и купить молоко"'
    )

product_to_category = {
    "молоко": "молочка",
    "сметана": "молочка",
    "творог": "молочка",
    "сыр": "молочка",
    "яйца": "яйцо",
    "фарш": "мясо",
    "азу": "мясо",
    "филе": "птица",
    "печень": "птица",
    "грудка": "птица",
    "крылья": "птица",
    "колбаса": "колбаса",
    "рис": "бакалея",
    "макароны": "бакалея",
    "гречка": "бакалея",
    "майонез": "соусы",
    "соус": "соусы",
    "кетчуп": "соусы",
    "кофе": "кофе и чай",
    "чай": "кофе и чай",
    "сахар": "специи",
    "какао": "бакалея",
    "соль": "бакалея",
    "шоколад": "сладкое",
    "печенье": "сладкое",
    "яблоки": "фрукты",
    "бананы": "фрукты",
    "картофель": "овощи",
    "огурцы": "овощи",
    "батон": "хлеб",
    "ржаной хлеб": "хлеб",
    "пельмени": "заморозка",
    "овощи": "заморозка",
    "сок": "напитки",
    "вода": "напитки"
}


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
                await update.message.reply_text("Я не понял, произошла ошибка, попробуй снова")
            return

        elif state == "waiting_for_input":
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
          
        elif state == "price":
          extracted_products = get_context(user_id, "products_extracted")
          if not extracted_products:
              await update.message.reply_text("Кажется, твой список продуктов пустой, начнем сначала.")
              return

          all_products = get_products(need_unit_price=True, available=True)
          extracted_categories = []
          unknown_products = []

          for product in extracted_products:
            logger.debug(f"Matching product: {product}")
            category = product_to_category.get(product)
            if category:
                extracted_categories.append(category)
                logger.info(f"Found category for {product}: {category}")
            else:
                unknown_products.append(product)
                logger.warning(f"Unknown product: {product}")

          if unknown_products:
              await update.message.reply_text(
                  f"Не удалось найти категории для: {', '.join(unknown_products)}")

          if extracted_categories:
              await update.message.reply_text(f"Вижу, ты хочешь купить: {', '.join(set(extracted_categories))}")

          await update.message.reply_text("Сравниваю цены в магазинах, чтоб найти наилучшие предложения для тебя!")
          recommendations = recommend(all_products, extracted_categories, k=2)

          response_text = "\nРекомендую:\n"
          for category, items in recommendations.items():
              response_text += f"\n📦 {category.capitalize()}:\n"
              for item in items:
                  response_text += f"• {item['product_name_ru']} ({item['product_type']}), {item['quantity']}{item['unit']} — {item['price']}₽ в магазине {item['store'].capitalize()}\n"

          await update.message.reply_text(response_text.strip())
          return

        else:
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
        
        await query.edit_message_text(f"Вот твой готовый список:\n {products_extracted}.")

        await send_image("bot/img/img1.png", update, context)  # Отправляем изображение

        provided_recipes = recomend_recipies(products_extracted)
        save_context(user_id, "provided_recipes", provided_recipes)
        await query.message.reply_text(provided_recipes)

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("Добавить новые продукты", callback_data="add_new")],
            [InlineKeyboardButton("Ничего не добавляй", callback_data="no_add")]
        ])
        await query.message.reply_text("Хочешь добавим недостающие продукты в корзину?", reply_markup=keyboard)

    elif query.data == "regect_extracted_list":
        reset_context(user_id)
        set_state(user_id, "start")
        await query.edit_message_reply_markup(reply_markup=None)
        await query.edit_message_text("Хорошо, давай попробуем снова. Отправь список продуктов заново.")

    elif query.data == "add_new":
        set_state(user_id, "start")
        await send_image("bot/img/img2.png", update, context) 

        products_extracted = get_extracted_products(user_id)
        recipes = get_context(user_id).get("provided_recipes")

        fresh_list = update_products_with_ai(products_extracted, recipes)

        result = "\n• ".join(products_extracted.split(", ") + fresh_list.split(", "))
        formatted_result = "• " + result 

        await query.edit_message_text(f"Вот твой готовый список:\n{formatted_result}")

    elif query.data == "no_add":
        set_state(user_id, "start")
        await send_image("bot/img/img2.png", update, context) 

        products_extracted = get_extracted_products(user_id)
        result = "\n• ".join(products_extracted.split(", "))
        await query.edit_message_text(f"Вот твой готовый список:\n {result}.")


def main():
    """Start the bot."""
    token = os.getenv('TELEGRAM_TOKEN')
    if not token:
        raise ValueError("TELEGRAM_TOKEN не найден в переменных окружения")

    application = Application.builder().token(token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(handle_callback_query))

    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
