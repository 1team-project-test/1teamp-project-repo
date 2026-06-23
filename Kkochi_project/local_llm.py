import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "gemma2:9b"


def ask_local_ai(prompt):
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL_NAME,
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_predict": 700,
                "temperature": 0.3,
                "top_p": 0.8,
                "num_ctx": 2048
            }
        },
        timeout=180
    )

    response.raise_for_status()
    return response.json()["response"].strip()


def ask_local_question(prompt):
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL_NAME,
            "prompt": prompt,
            "stream": False,
            "keep_alive": "30m",
            "options": {
            ...
            }
        },
        timeout=120
    )

    response.raise_for_status()
    return response.json()["response"].strip()