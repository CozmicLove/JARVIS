import os
import requests


class Brain:

    def __init__(self, model="gemma3:4b"):
        self.model = model
        self.url = "http://localhost:11434/api/generate"

        base = os.path.dirname(os.path.dirname(__file__))
        self.identity_file = os.path.join(
            base,
            "memory",
            "identity.txt"
        )

    def load_identity(self):
        try:
            with open(self.identity_file, "r", encoding="utf-8") as file:
                return file.read()
        except Exception:
            return ""

    def ask(self, prompt):

        identity = self.load_identity()

        final_prompt = f"""
{identity}

User:
{prompt}

JARVIS:
"""

        payload = {
            "model": self.model,
            "prompt": final_prompt,
            "stream": False,
            "options": {
                "temperature": 0.4,
                "top_p": 0.9,
                "num_predict": 120
            }
        }

        try:

            response = requests.post(
                self.url,
                json=payload,
                timeout=120
            )

            response.raise_for_status()

            data = response.json()

            answer = data.get("response", "").strip()

            if not answer:
                return "I'm ready, Sir."

            return answer

        except Exception as error:

            return f"Brain Error : {error}"