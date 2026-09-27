import base64
import json
import os
import tempfile

import requests
from PIL import ImageGrab


class ScreenVision:

    def __init__(self, env_file=None, settings_file=None):
        self.env_file = env_file
        self.settings_file = settings_file
        self.load_env_file()
        self.api_key = os.getenv("NVIDIA_API_KEY", "").strip()
        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
        self.api_url = "https://integrate.api.nvidia.com/v1/chat/completions"
        self.model = "meta/llama-3.2-11b-vision-instruct"
        self.openrouter_url = "https://openrouter.ai/api/v1/chat/completions"
        self.openrouter_model = "openrouter/free"
        self.timeout = 10
        self.load_settings()

    def load_env_file(self):
        if not self.env_file or not os.path.exists(self.env_file):
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
        if not self.settings_file or not os.path.exists(self.settings_file):
            return

        try:
            with open(self.settings_file, "r", encoding="utf-8") as file:
                settings = json.load(file)

            vision = settings.get("vision", {})
            self.model = vision.get("model", self.model)
            self.openrouter_model = vision.get(
                "openrouter_model",
                self.openrouter_model
            )
            self.timeout = vision.get("timeout", self.timeout)
        except Exception:
            pass

    def capture_screen(self):
        image = ImageGrab.grab(all_screens=True)
        image = image.convert("RGB")

        max_width = 1600
        if image.width > max_width:
            ratio = max_width / image.width
            image = image.resize(
                (max_width, int(image.height * ratio))
            )

        temp = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
        temp.close()
        image.save(temp.name, "JPEG", quality=82, optimize=True)
        return temp.name

    def image_to_data_url(self, image_path):
        with open(image_path, "rb") as file:
            encoded = base64.b64encode(file.read()).decode("ascii")

        return f"data:image/jpeg;base64,{encoded}"

    def ask_vision(self, prompt, image_path, timeout=None):
        request_timeout = timeout or self.timeout

        if self.openrouter_api_key and self.is_specific_openrouter_vision_model():
            answer = self.ask_openrouter_vision(
                prompt,
                image_path,
                timeout=request_timeout
            )
            if answer and not self.is_unhelpful_vision_answer(answer):
                return answer

        if not self.api_key:
            return ""

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt,
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": self.image_to_data_url(image_path),
                            },
                        },
                    ],
                }
            ],
            "temperature": 0.1,
            "max_tokens": 220,
            "stream": False,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        response = requests.post(
            self.api_url,
            json=payload,
            headers=headers,
            timeout=request_timeout,
        )
        response.raise_for_status()
        data = response.json()
        answer = (
            data.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
            .strip()
        )
        if self.is_unhelpful_vision_answer(answer):
            return ""
        return answer

    def is_specific_openrouter_vision_model(self):
        model = str(self.openrouter_model or "").strip().lower()
        if not model or model == "openrouter/free":
            return False

        vision_markers = ("vision", "vl", "omni", "image")
        return any(marker in model for marker in vision_markers)

    def is_unhelpful_vision_answer(self, answer):
        text = str(answer or "").strip().lower()
        if not text:
            return True

        bad_markers = [
            "user safety",
            "safe",
            "i cannot assist",
            "i can't assist",
            "as an ai",
            "no image",
            "cannot view",
            "can't view",
        ]
        if text in bad_markers:
            return True

        return any(marker in text for marker in bad_markers[:4])

    def ask_openrouter_vision(self, prompt, image_path, timeout=None):
        request_timeout = timeout or self.timeout

        payload = {
            "model": self.openrouter_model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt,
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": self.image_to_data_url(image_path),
                            },
                        },
                    ],
                }
            ],
            "temperature": 0.1,
            "max_tokens": 260,
            "stream": False,
        }
        headers = {
            "Authorization": f"Bearer {self.openrouter_api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://127.0.0.1:8888",
            "X-Title": "NOVA Desktop Assistant",
        }

        try:
            response = requests.post(
                self.openrouter_url,
                json=payload,
                headers=headers,
                timeout=request_timeout,
            )
            response.raise_for_status()
            data = response.json()
            answer = (
                data.get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
                .strip()
            )
            if self.is_unhelpful_vision_answer(answer):
                return ""
            return answer
        except Exception:
            return ""

    def analyze_current_screen(self, prompt, timeout=None):
        image_path = self.capture_screen()

        try:
            return self.ask_vision(prompt, image_path, timeout=timeout)
        finally:
            try:
                os.remove(image_path)
            except OSError:
                pass

    def read_maps_route(self, language="id", timeout=None):
        if language == "id":
            prompt = (
                "Baca screenshot Google Maps ini. Cari estimasi durasi perjalanan "
                "untuk rute mobil atau driving yang sedang tampil. Jika beberapa mode "
                "terlihat, prioritaskan durasi pada tab mobil. Jawab hanya satu kalimat bahasa Indonesia "
                "yang natural, tanpa markdown, tanpa tanda bintang, tanpa label, dan jangan memakai bahasa Inggris. "
                "Jika Google Maps menampilkan pesan tidak dapat menemukan tujuan, can't find, "
                "atau meminta ejaan diperiksa, abaikan durasi rute lama yang mungkin masih terlihat "
                "dan jawab persis dengan format: ROUTE_NOT_FOUND: <nama tujuan yang terlihat>. "
                "Jika durasi terlihat, sebutkan durasi utama dan kondisi lalu lintas singkat. "
                "Jika rute atau durasi tidak terlihat, jawab: Saya belum bisa membaca estimasi waktu dari layar Maps."
            )
        else:
            prompt = (
                "Read this Google Maps screenshot. Find the visible trip duration "
                "for the driving or car route on screen. If multiple travel modes are visible, "
                "prioritize the car tab duration. Reply in one short English sentence. "
                "If Google Maps says it cannot find the destination, can't find, or asks to check spelling, "
                "ignore any stale route duration still visible and reply exactly: ROUTE_NOT_FOUND: <visible destination>. "
                "If the duration is visible, mention the main duration and brief traffic condition. "
                "If no route or duration is visible, reply: I cannot read the travel time from the Maps screen yet."
            )

        return self.analyze_current_screen(prompt, timeout=timeout)
