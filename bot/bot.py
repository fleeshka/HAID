import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from olama import olama_nlp_generate
import sys
# sys.path.append('/app/src')
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from src.api_handler import get_products
from src.recomender import recommend

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
    if update.message is None or update.message.text is None:
        return

    user_first_name = update.message.from_user.first_name
    await update.message.reply_text(
        f'👋 Привет, {user_first_name}! Я — твой AI помощник по продуктам и рецептам.\n\n'
        'Ты можешь спросить:\n'
        '- Где дешевле купить [продукт]\n'
        '- Что приготовить из [ингредиента]\n'
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
    """Handle incoming messages and generate responses."""
    try:
        logger.info("Received message update.")

        # Extract the user's message and log it
        user_message = update.message.text.lower()
        logger.info(f"User message: {user_message}")

        # Use Cohere NLP to extract structured products
        logger.info("Calling NLP function to generate AI response.")
        ai_response = olama_nlp_generate(user_message)
        logger.info(f"AI response: {ai_response}")

        extracted_products = []
        for line in ai_response.splitlines():
            logger.debug(f"Processing line: {line}")
            if line.lower().startswith("Продукты из сообщения:"):
                extracted = line.split(":", 1)[1].strip()
                extracted_products = [item.strip() for item in extracted.split(",") if item.strip()]
                logger.info(f"Extracted products from user input: {extracted_products}")
                continue
            elif line.lower().startswith("Добавлено:"):
                extracted = line.split(":", 1)[1].strip()
                extracted_products = [item.strip() for item in extracted.split(",") if item.strip()]
                logger.info(f"Extracted products from dishes: {extracted_products}")
                break

        if not extracted_products:
            logger.warning("No products extracted from AI response.")
            await update.message.reply_text("Не удалось извлечь продукты из сообщения.")
            return

        # Get all products from the database
        all_products = get_products(need_unit_price=True, available=True)
        logger.info(f"Retrieved {len(all_products)} available products.")

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
                f"Не удалось найти категорию для следующих товаров, они будут исключены из списка: {', '.join(unknown_products)}")
            logger.info(f"Unknown products: {', '.join(unknown_products)}")
        # todo: say that i see, you want to but bembem bem
        # await update.message.reply_text("Не удалось извлечь продукты из сообщения.")
        # todo: ask about budget constraints for categories
        # todo: ask abt preferred shop and say that products from preferred shop are more likely to be recommended
        # Generate recommendations
        await update.message.reply_text("Сравниваю цены в магазинах, чтоб найти наилучшие предложения для тебя!")
        recommendations = recommend(all_products, extracted_categories, k=2)
        logger.info(f"Generated {len(recommendations)} recommendation categories.")

        # Prepare the response text
        # response_text = f"{ai_response.strip()}\n\nПроанализировав цены в Пятерочке и Магните, я рекомендую тебе:\n"
        # for category, items in recommendations.items():
        #     response_text += f"\n📦 {category}:\n"
        #     for item in items:
        #         response_text += f"• {item['name']} — {item['price']}₽ ({item['store']})\n"
        #         logger.debug(f"Recommendation: {item['name']} — {item['price']}₽ ({item['store']})")
        response_text = f"{ai_response.strip()}\n\nПроанализировав цены в Пятерочке и Магните, рекомендую тебе:\n"
        for category, items in recommendations.items():
            response_text += f"\n📦 {category.capitalize()}:\n"
            for item in items:
                name = item['product_name_ru']
                product_type = item['product_type']
                quantity = item['quantity']
                unit = item['unit']
                price = item['price']
                store = item['store']
                response_text += f"• {name} ({product_type}), {quantity}{unit} — {price}₽ в магазине {store.capitalize()}\n"
                logger.debug(f"Recommendation: {name} ({product_type}), {quantity}{unit} — {price}₽ в {store}")

        # Send the response
        await update.message.reply_text(response_text.strip())
        logger.info("Response sent successfully.")

    except Exception as e:
        logger.error(f"Error during message handling: {str(e)}")
        await update.message.reply_text("Ошибка при обработке сообщения. Попробуйте позже.")



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
