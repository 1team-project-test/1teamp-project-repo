import requests

def ask_local_ai(prompt):
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "gemma2:9b",
            "prompt": prompt,
            "stream": False
        }
    )

    response.raise_for_status()
    return response.json()["response"]