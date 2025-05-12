# List2Grocery - HAID Project

A Telegram bot with machine learning capabilities, powered by Ollama and Redis for data management.

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
