import requests

OLLAMA_API = "http://localhost:11434/api/chat"

def olama_nlp_generate(prompt, temperature=0.7, max_tokens=400):
    system_prompt = (
        "Ты — помощник покупателя. Пользователь отправил список покупок или блюдо. "
        "Выдели только названия продуктов в виде строки, разделённой запятыми. "
        "Не добавляй объяснений.\n"
        f"Вот сообщение пользователя: {prompt.strip()}"
    )

    payload = {
        "model": "llama3:instruct",  
        "messages": [
            {"role": "user", "content": system_prompt}
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False
    }

    try:
        response = requests.post(OLLAMA_API, json=payload)
        status = response.raise_for_status()
        return response.json()["message"]["content"]
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при запросе к Ollama API: {e}")
        return f"Ошибка при запросе к Ollama API: {e} \n STATUS {status}\n Sorry, I encountered an error while processing your request."
