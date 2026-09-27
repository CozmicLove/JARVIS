import os
import json
import requests


class Brain:

    def __init__(self):
        base = os.path.dirname(os.path.dirname(__file__))
        project_root = os.path.dirname(base)
        self.identity_file = os.path.join(
            base,
            "memory",
            "identity.txt"
        )
        self.settings_file = os.path.join(
            project_root,
            "config",
            "settings.json"
        )
        self.env_file = os.path.join(project_root, ".env")
        self.load_env_file()

        settings = self.load_settings()
        brain_settings = settings.get("brain", {})
        local_settings = brain_settings.get("local", {})
        nvidia_settings = brain_settings.get("nvidia", {})
        openrouter_settings = brain_settings.get("openrouter", {})

        self.provider = brain_settings.get("provider", "hybrid")
        self.local_model = local_settings.get("model", "gemma3:4b")
        self.local_url = local_settings.get(
            "url",
            "http://localhost:11434/api/generate"
        )
        self.nvidia_model = nvidia_settings.get(
            "model",
            "deepseek-ai/deepseek-v4-flash"
        )
        self.nvidia_fallback_model = nvidia_settings.get(
            "fallback_model",
            "meta/llama-3.1-8b-instruct"
        )
        self.nvidia_url = nvidia_settings.get(
            "url",
            "https://integrate.api.nvidia.com/v1/chat/completions"
        )
        self.nvidia_api_key = os.getenv("NVIDIA_API_KEY", "").strip()
        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
        self.nvidia_timeout = nvidia_settings.get("timeout", 60)
        self.local_timeout = local_settings.get("timeout", 120)
        self.max_tokens = nvidia_settings.get("max_tokens", 600)
        self.thinking = nvidia_settings.get("thinking", False)
        self.reasoning_effort = nvidia_settings.get("reasoning_effort", "medium")
        self.openrouter_model = openrouter_settings.get(
            "model",
            "openrouter/free"
        )
        self.openrouter_fallback_model = openrouter_settings.get(
            "fallback_model",
            "nvidia/nemotron-3-super-120b-a12b:free"
        )
        self.openrouter_url = openrouter_settings.get(
            "url",
            "https://openrouter.ai/api/v1/chat/completions"
        )
        self.openrouter_timeout = openrouter_settings.get("timeout", 45)
        self.openrouter_max_tokens = openrouter_settings.get("max_tokens", 500)

    def load_env_file(self):
        if not os.path.exists(self.env_file):
            return

        try:
            with open(self.env_file, "r", encoding="utf-8-sig") as file:
                for line in file:
                    line = line.strip()

                    if not line or line.startswith("#") or "=" not in line:
                        continue

                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")

                    if key and key not in os.environ:
                        os.environ[key] = value
        except Exception:
            pass

    def load_settings(self):
        try:
            with open(self.settings_file, "r", encoding="utf-8") as file:
                return json.load(file)
        except Exception:
            return {}

    def load_identity(self):
        try:
            with open(self.identity_file, "r", encoding="utf-8") as file:
                return file.read()
        except Exception:
            return ""

    def build_messages(self, prompt, language=None):
        identity = self.load_identity()
        language_instruction = (
            "Keep the answer short, natural, and useful. "
            "Use plain text only, no markdown formatting. "
            "Answer stable general knowledge questions directly. "
            "Do not refuse general knowledge questions just because you cannot browse. "
            "Only mention lack of live internet access for current, real-time, or rapidly changing facts."
        )

        if language == "id":
            language_instruction = (
                "Answer in Indonesian. Do not add English honorifics like Sir. "
                "Use plain text only, no markdown formatting. "
                "Answer stable general knowledge questions directly. "
                "Do not refuse general knowledge questions just because you cannot browse. "
                "Only mention lack of live internet access for current, real-time, or rapidly changing facts."
            )
        elif language == "en":
            language_instruction = "Answer in English. Use plain text only, no markdown formatting."

        system_prompt = f"""
{identity}

{language_instruction}
"""

        return [
            {
                "role": "system",
                "content": system_prompt.strip()
            },
            {
                "role": "user",
                "content": prompt
            }
        ]

    def ask(self, prompt, language=None):
        if self.provider == "openrouter":
            return self.ask_openrouter(prompt, language)

        if self.provider == "nvidia":
            return self.ask_nvidia(prompt, language)

        if self.provider == "local":
            return self.ask_local(prompt, language)

        answer = self.ask_openrouter(prompt, language, allow_error=True)

        if answer:
            return answer

        answer = self.ask_nvidia(prompt, language, allow_error=True)

        if answer:
            return answer

        return self.ask_local(prompt, language)

    def ask_stream(self, prompt, language=None):
        if self.provider in ("openrouter", "hybrid") and self.openrouter_api_key:
            streamed = False

            for chunk in self.ask_openrouter_stream_model(
                self.openrouter_model,
                prompt,
                language,
                allow_error=True
            ):
                streamed = True
                yield chunk

            if streamed:
                return

            if self.openrouter_fallback_model != self.openrouter_model:
                for chunk in self.ask_openrouter_stream_model(
                    self.openrouter_fallback_model,
                    prompt,
                    language,
                    allow_error=True
                ):
                    streamed = True
                    yield chunk

            if streamed:
                return

        if self.provider in ("nvidia", "hybrid") and self.nvidia_api_key:
            streamed = False

            for chunk in self.ask_nvidia_stream_model(
                self.nvidia_model,
                prompt,
                language,
                allow_error=True
            ):
                streamed = True
                yield chunk

            if streamed:
                return

            if self.nvidia_fallback_model != self.nvidia_model:
                for chunk in self.ask_nvidia_stream_model(
                    self.nvidia_fallback_model,
                    prompt,
                    language,
                    allow_error=True
                ):
                    streamed = True
                    yield chunk

            if streamed:
                return

        yield self.ask_local(prompt, language)

    def ask_openrouter(self, prompt, language=None, allow_error=False):
        if not self.openrouter_api_key:
            if allow_error:
                return ""

            return "OPENROUTER_API_KEY belum diset."

        answer = self.ask_openrouter_model(
            self.openrouter_model,
            prompt,
            language,
            allow_error=True
        )

        if answer:
            return answer

        if self.openrouter_fallback_model != self.openrouter_model:
            answer = self.ask_openrouter_model(
                self.openrouter_fallback_model,
                prompt,
                language,
                allow_error=True
            )

            if answer:
                return answer

        if allow_error:
            return ""

        return "Saya belum mendapat jawaban dari OpenRouter brain."

    def openrouter_headers(self):
        return {
            "Authorization": f"Bearer {self.openrouter_api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://127.0.0.1:8888",
            "X-Title": "NOVA Desktop Assistant",
        }

    def ask_openrouter_model(self, model, prompt, language=None, allow_error=False):
        payload = {
            "model": model,
            "messages": self.build_messages(prompt, language),
            "temperature": 0.45,
            "top_p": 0.9,
            "max_tokens": self.openrouter_max_tokens,
            "stream": False,
        }

        try:
            response = requests.post(
                self.openrouter_url,
                json=payload,
                headers=self.openrouter_headers(),
                timeout=self.openrouter_timeout
            )
            response.raise_for_status()
            data = response.json()
            message = data["choices"][0]["message"]
            return (message.get("content") or "").strip()
        except Exception as error:
            if allow_error:
                return ""

            return f"OpenRouter Brain Error : {error}"

    def ask_openrouter_stream_model(self, model, prompt, language=None, allow_error=False):
        payload = {
            "model": model,
            "messages": self.build_messages(prompt, language),
            "temperature": 0.45,
            "top_p": 0.9,
            "max_tokens": self.openrouter_max_tokens,
            "stream": True,
        }

        try:
            with requests.post(
                self.openrouter_url,
                json=payload,
                headers=self.openrouter_headers(),
                timeout=self.openrouter_timeout,
                stream=True
            ) as response:
                response.raise_for_status()

                for line in response.iter_lines(decode_unicode=True):
                    if not line:
                        continue

                    if line.startswith("data:"):
                        line = line[5:].strip()

                    if not line or line == "[DONE]":
                        continue

                    data = json.loads(line)
                    choices = data.get("choices") or []

                    if not choices:
                        continue

                    delta = choices[0].get("delta") or {}
                    content = delta.get("content")

                    if content:
                        yield content
        except Exception:
            if allow_error:
                return

            yield "Saya belum mendapat jawaban dari OpenRouter brain."

    def ask_local(self, prompt, language=None):
        messages = self.build_messages(prompt, language)
        final_prompt = f"""
{messages[0]['content']}

User:
{messages[1]['content']}

NOVA:
"""

        payload = {
            "model": self.local_model,
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
                self.local_url,
                json=payload,
                timeout=self.local_timeout
            )

            response.raise_for_status()

            data = response.json()

            answer = data.get("response", "").strip()

            if not answer:
                return "I'm ready, Sir."

            return answer

        except Exception as error:

            return f"Brain Error : {error}"

    def ask_nvidia(self, prompt, language=None, allow_error=False):
        if not self.nvidia_api_key:
            if allow_error:
                return ""

            return "NVIDIA_API_KEY belum diset."

        answer = self.ask_nvidia_model(
            self.nvidia_model,
            prompt,
            language,
            allow_error=True
        )

        if answer:
            return answer

        if self.nvidia_fallback_model != self.nvidia_model:
            answer = self.ask_nvidia_model(
                self.nvidia_fallback_model,
                prompt,
                language,
                allow_error=True
            )

            if answer:
                return answer

        if allow_error:
            return ""

        return "Saya belum mendapat jawaban dari NVIDIA brain."

    def ask_nvidia_model(self, model, prompt, language=None, allow_error=False):
        payload = {
            "model": model,
            "messages": self.build_messages(prompt, language),
            "temperature": 0.7,
            "top_p": 0.95,
            "max_tokens": self.max_tokens,
            "stream": False,
            "chat_template_kwargs": {
                "thinking": self.thinking,
                "reasoning_effort": self.reasoning_effort
            }
        }

        headers = {
            "Authorization": f"Bearer {self.nvidia_api_key}",
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(
                self.nvidia_url,
                json=payload,
                headers=headers,
                timeout=self.nvidia_timeout
            )
            response.raise_for_status()
            data = response.json()
            message = data["choices"][0]["message"]
            answer = (message.get("content") or "").strip()

            if answer:
                return answer

            if allow_error:
                return ""

            return "Saya belum mendapat jawaban dari NVIDIA brain."
        except Exception as error:
            if allow_error:
                return ""

            return f"NVIDIA Brain Error : {error}"

    def ask_nvidia_stream_model(self, model, prompt, language=None, allow_error=False):
        payload = {
            "model": model,
            "messages": self.build_messages(prompt, language),
            "temperature": 0.7,
            "top_p": 0.95,
            "max_tokens": self.max_tokens,
            "stream": True,
            "chat_template_kwargs": {
                "thinking": self.thinking,
                "reasoning_effort": self.reasoning_effort
            }
        }

        headers = {
            "Authorization": f"Bearer {self.nvidia_api_key}",
            "Content-Type": "application/json"
        }

        try:
            with requests.post(
                self.nvidia_url,
                json=payload,
                headers=headers,
                timeout=self.nvidia_timeout,
                stream=True
            ) as response:
                response.raise_for_status()

                for line in response.iter_lines(decode_unicode=True):
                    if not line:
                        continue

                    if line.startswith("data:"):
                        line = line[5:].strip()

                    if not line or line == "[DONE]":
                        continue

                    data = json.loads(line)
                    choices = data.get("choices") or []

                    if not choices:
                        continue

                    delta = choices[0].get("delta") or {}
                    content = delta.get("content")

                    if content:
                        yield content
        except Exception:
            if allow_error:
                return

            yield "Saya belum mendapat jawaban dari NVIDIA brain."
