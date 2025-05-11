import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from olama import olama_nlp_generate
import sys
# sys.path.append('/app/src')
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))
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
        user_message = update.message.text.lower()

        # Use Cohere NLP to extract structured products
        ai_response =await  olama_nlp_generate(user_message)
        # await update.message.reply_text(ai_response)
        extracted_products = []
        for line in ai_response.splitlines():
            if line.lower().startswith("продукты из сообщения:"):
                extracted = line.split(":", 1)[1].strip()
                extracted_products = [item.strip() for item in extracted.split(",") if item.strip()]
                break
        if not extracted_products:
            await update.message.reply_text("Не удалось извлечь продукты из сообщения.")
            return
        all_products = get_products(need_unit_price=True, available=True)
        extracted_categories = []
        unknown_products = []

        for product in extracted_products:
            category = product_to_category.get(product)
            if category:
                extracted_categories.append(category)
            else:
                unknown_products.append(product)

        if unknown_products:
            await update.message.reply_text(f"Не удалось найти категорию для следующих товаров: {', '.join(unknown_products)}")

        recommendations = recommend(all_products, extracted_categories)

        response_text = f"{ai_response.strip()}\n\nПроанализировав цены в Пятерочке и Магните, я рекомендую тебе:\n"
        for category, items in recommendations.items():
            response_text += f"\n📦 {category}:\n"
            for item in items:
                response_text += f"• {item['name']} — {item['price']}₽ ({item['store']})\n"

        await update.message.reply_text(response_text.strip())



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
