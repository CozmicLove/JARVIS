import warnings
warnings.filterwarnings("ignore")

import os
import tempfile
import subprocess

import soundfile as sf
from kokoro import KPipeline


class Speaker:

    def __init__(self):

        self.pipeline = KPipeline(
            lang_code="a",
            repo_id="hexgrad/Kokoro-82M"
        )

        self.voice = "am_adam"
        self.speed = 0.95

    def speak(self, text):

        if not text:
            return

        text = str(text).strip()

        try:

            generator = self.pipeline(
                text,
                voice=self.voice,
                speed=self.speed
            )

            for _, _, audio in generator:

                with tempfile.NamedTemporaryFile(
                    delete=False,
                    suffix=".wav"
                ) as tmp:

                    wav_file = tmp.name

                sf.write(
                    wav_file,
                    audio,
                    24000
                )

                subprocess.run(
                    [
                        "powershell",
                        "-NoProfile",
                        "-Command",
                        f'(New-Object Media.SoundPlayer "{wav_file}").PlaySync();'
                    ],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )

                try:
                    os.remove(wav_file)
                except:
                    pass

                break

        except Exception as e:
            print(f"[Speaker Error] {e}")