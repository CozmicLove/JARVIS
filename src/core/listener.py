import tempfile
import sounddevice as sd
import soundfile as sf
from faster_whisper import WhisperModel


class Listener:

    def __init__(self):
        self.sample_rate = 16000
        self.duration = 5
        self.model = WhisperModel("base", device="cpu", compute_type="int8")

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

        sf.write(audio_path, audio, self.sample_rate)

        segments, _ = self.model.transcribe(audio_path)

        text = ""

        for segment in segments:
            text += segment.text

        return text.strip()