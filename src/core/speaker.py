import subprocess
import tempfile
from pathlib import Path


class Speaker:

    def __init__(self):
        self.piper_exe = Path("tools/piper/piper.exe")
        self.model_path = Path("models/piper/id_ID-news_tts-medium.onnx")

    def speak(self, text):

        text = str(text).strip()

        if not text:
            return

        try:
            # Buat file audio sementara
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
                audio_path = temp_audio.name

            # Generate audio menggunakan Piper
            subprocess.run(
                [
                    str(self.piper_exe),
                    "--model",
                    str(self.model_path),
                    "--output_file",
                    audio_path,
                ],
                input=text,
                text=True,
                encoding="utf-8",
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True,
            )

            # Putar hasil audio
            subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-Command",
                    f'(New-Object Media.SoundPlayer "{audio_path}").PlaySync();'
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True,
            )

        except Exception as e:
            print(f"[Speaker Error] {e}")