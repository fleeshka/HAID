# List2Grocery - HAID Project

This project presents a Telegram bot designed to make grocery shopping easier and more efficient. By understanding natural language input from users, the bot helps create smart shopping lists tailored to individual needs. It uses advanced natural language processing to identify relevant products and employs a machine learning algorithm to recommend the best options based on price and store availability.

Our approach is grounded in human-centered AI interaction principles, ensuring that users remain in control, receive clear explanations, and enjoy a simple, intuitive experience. The backend leverages Ollama for AI model serving and Redis for fast and reliable data management.

## Prerequisites

- Docker and Docker Compose installed
- NVIDIA GPU with CUDA support (required for Ollama) (optional)
- Telegram Bot Token (get it from [@BotFather](https://t.me/BotFather))

## Quick Start with Docker Compose

1. Clone the repository:
```bash
git clone git@github.com:fleeshka/HAID.git
cd HAID
```

2. Create a `.env` file in the project root:
```bash
echo "TELEGRAM_BOT_TOKEN=your_bot_token_here" > .env
```

3. Start the services:
```bash
docker-compose up -d --build
```

The command will start three services:
- Redis server (port 6379)
- Ollama service (port 11434)
- Telegram bot

## Docker Services Details

### Redis
- Port: 6379
- Purpose: Data caching and management
- Container name: redis

### Ollama
- Port: 11434
- Purpose: AI/ML model serving
- Model: llama3:instruct
- Container name: ollama
- GPU Requirements: NVIDIA GPU with CUDA support
- Memory Limit: 2GB

### Telegram Bot
- Container name: telegram-bot
- Depends on: Ollama and Redis
- Environment: Loads from .env file
- Volumes:
  - ./data:/app/data
  - ./src:/app/src


## Troubleshooting


1. If Ollama fails to start:
   - Ensure NVIDIA drivers are installed
   - Check GPU availability: `nvidia-smi`
   - Verify CUDA support

2. If Redis connection fails:
   - Check if port 6379 is available
   - Ensure Redis container is running: `docker ps`

3. If bot doesn't respond:
   - Verify TELEGRAM_BOT_TOKEN in .env
   - Check bot logs: `docker logs telegram-bot`
    ```bash
    docker-compose logs -f
    ```

## User Guide
1. Find the bot in Telegram:
    Search for the bot by its username, e.g., @YourBotUsername (replace with the actual bot username).

2. Start interaction:
    Send /start to initiate the conversation. The bot will greet you and provide instructions.

3. Create your shopping list:
    Type your shopping list in natural language. For example:
    “I want to buy milk, eggs, and bread” or “Ingredients for pancakes”.

4. Bot processes your input:
    The bot uses NLP to extract relevant product names and may suggest additional ingredients if you mention dishes.

5. Receive recommendations:
    The bot will recommend products with prices and stores, optimized using the KNN algorithm.

6. Edit or confirm list:
    You can add or remove items via buttons or text commands before finalizing your list.

Use commands:
```
        /help - get help on how to use the bot

        /reset - clear the current list and start over
```
## Human-AI Interaction Design Principles

This project incorporates key human-centered AI interaction principles to enhance user experience and trust:

-  Visibility: The bot provides clear feedback at each step, showing system status and next actions.
-  User Control: Users can easily edit, add, or remove items from their shopping list, maintaining full control.
-  Transparency: Recommendations are explained and justified by showing prices and stores, helping users understand the AI’s decisions.
-  Simplicity: The conversational interface uses natural language and intuitive buttons to reduce cognitive load.
-  Assistive AI: The bot acts as an assistant, supporting rather than replacing user decision-making.

These principles are inspired by established guidelines in human-AI interaction research (e.g., Amershi et al., Miller, Shneiderman) to ensure the bot is both effective and user-friendly.

## Project Structure

```
.
├── bot/            # Bot-specific code
├── data/           # Data storage
├── src/            # Source code
├── Dockerfile      # Docker configuration
├── docker-compose.yml
├── requirements.txt
└── .env           # Environment variables
```
