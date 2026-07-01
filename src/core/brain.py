import requests


class Brain:

    def __init__(self, model="qwen3:4b"):
        self.model = model
        self.url = "http://localhost:11434/api/generate"

    def ask(self, prompt):

        system_prompt = """
You are JARVIS, Alfred's personal AI assistant.
Never introduce yourself as Qwen, an AI language model, or any other model name.
Always speak as JARVIS.
Answer in natural English.
Keep your answers concise, calm, professional, and helpful.
"""

        final_prompt = f"""
{system_prompt}

User:
{prompt}

JARVIS:
"""

        payload = {
            "model": self.model,
            "prompt": final_prompt,
            "stream": False
        }

        try:
            response = requests.post(
                self.url,
                json=payload,
                timeout=120
            )

            response.raise_for_status()
            data = response.json()

            return data.get("response", "No response from brain.").strip()

        except requests.exceptions.RequestException as error:
            return f"Brain error: {error}"