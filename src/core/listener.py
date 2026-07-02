import os
import tempfile

import sounddevice as sd
import soundfile as sf
from faster_whisper import WhisperModel


class Listener:

    def __init__(self):
        self.sample_rate = 16000
        self.duration = 5

        self.model = WhisperModel(
            "small",
            device="cuda",
            compute_type="float16"
        )

    def listen(self):
        print("Listening...")

        audio = sd.rec(
            int(self.duration * self.sample_rate),
            samplerate=self.sample_rate,
            channels=1,
            dtype="float32"
        )

        sd.wait()

        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as file:
            audio_path = file.name

        try:
            sf.write(audio_path, audio, self.sample_rate)

            segments, _ = self.model.transcribe(
                audio_path,
                language="en",
                beam_size=3,
                vad_filter=True,
                condition_on_previous_text=False
            )

            text = ""

            for segment in segments:
                text += segment.text + " "

            return text.strip()

        finally:
            try:
                os.remove(audio_path)
            except:
                pass