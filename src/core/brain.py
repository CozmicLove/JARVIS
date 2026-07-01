import requests


class Brain:

    def __init__(self, model="qwen3:4b"):
        self.model = model
        self.url = "http://localhost:11434/api/generate"

    def ask(self, prompt):
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False
        }

        try:
            response = requests.post(self.url, json=payload, timeout=120)
            response.raise_for_status()
            data = response.json()
            return data.get("response", "No response from brain.").strip()

        except requests.exceptions.RequestException as error:
            return f"Brain error: {error}"