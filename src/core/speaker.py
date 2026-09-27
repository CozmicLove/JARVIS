import warnings
warnings.filterwarnings("ignore")

import os
import tempfile
import subprocess
import re
import time
import winsound
import asyncio

import numpy as np
import sounddevice as sd
import soundfile as sf


class Speaker:

    def __init__(self):
        base_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..")
        )

        self.pipeline = None
        self.voice = "am_adam"
        self.speed = 0.95
        self.sample_rate = 24000
        self.piper_exe = os.path.join(base_dir, "tools", "piper", "piper.exe")
        self.piper_model = os.path.join(
            base_dir,
            "models",
            "piper",
            "id_ID-news_tts-medium.onnx"
        )
        self.piper_config = f"{self.piper_model}.json"
        self.edge_voice = "id-ID-ArdiNeural"
        self.edge_english_voice = "en-US-GuyNeural"
        self.edge_rate = "+4%"
        self.edge_english_rate = "+6%"
        self.edge_volume = "+0%"
        self.enable_kokoro = os.getenv("NOVA_ENABLE_KOKORO", "0") == "1"

    def load_engine(self):
        if self.pipeline is None:
            print("Loading NOVA voice engine...")

            from kokoro import KPipeline

            self.pipeline = KPipeline(
                lang_code="a",
                repo_id="hexgrad/Kokoro-82M"
            )

            print("Voice engine ready.")

    def is_indonesian(self, text):
        lowered = text.lower()
        markers = [
            "saya",
            "anda",
            "baik",
            "buka",
            "membuka",
            "jam",
            "pukul",
            "sekarang",
            "sistem",
            "persen",
            "baterai",
            "komputer",
            "matikan",
            "tidak",
            "ya",
            "dibatalkan",
            "mohon",
            "konfirmasi",
            "apakah",
            "ingin",
            "dalam lima detik",
        ]

        return any(marker in lowered for marker in markers)

    def normalize_indonesian_text(self, text):
        replacements = {
            "NOVA": "Nova",
            "Chrome": "krom",
            "Notepad": "not ped",
            "Calculator": "kalkulator",
            "File Explorer": "penjelajah file",
            "CPU": "si pi yu",
            "GPU": "ji pi yu",
            "VRAM": "vi ram",
            "USD": "dolar amerika",
            "IDR": "rupiah",
            "RAM": "ram",
            "Disk": "disk",
            "Online": "online",
            "Charging": "sedang mengisi daya",
            "Battery": "baterai",
            "Power": "daya",
            "Intel(R)": "Intel",
            "Core(TM)": "Core",
            "NVIDIA": "envidia",
            "GeForce": "ji fors",
            "Laptop GPU": "laptop ji pi yu",
            "N/A": "tidak tersedia",
        }

        for source, replacement in replacements.items():
            if any(not char.isalnum() and not char.isspace() for char in source):
                text = re.sub(
                    re.escape(source),
                    replacement,
                    text,
                    flags=re.IGNORECASE
                )
            else:
                text = re.sub(
                    rf"\b{re.escape(source)}\b",
                    replacement,
                    text,
                    flags=re.IGNORECASE
                )

        text = text.replace("°C", "derajat celsius")

        # Edge Indonesian voice tends to ignore commas. Semicolons produce a
        # short, more natural pause without sounding as stiff as a full stop.
        text = re.sub(r"\s*,\s*", "; ", text)
        text = re.sub(r"\s*;\s*", "; ", text)
        text = re.sub(r"\s*:\s*", "; ", text)
        text = re.sub(r"\s+", " ", text).strip()

        return text

    def normalize_english_text(self, text):
        text = re.sub(r"\s+", " ", text).strip()
        text = re.sub(r"\.\s+", "; ", text)
        text = re.sub(r":\s+", ", ", text)
        return text

    def split_text(self, text, max_chars=2800):
        parts = re.split(r"(?<=[.!?])\s+", text)
        chunks = []
        current = ""

        for part in parts:
            part = part.strip()

            if not part:
                continue

            if len(part) > max_chars:
                subparts = re.split(r"(?<=[,;:])\s+", part)
            else:
                subparts = [part]

            for subpart in subparts:
                subpart = subpart.strip()

                if not subpart:
                    continue

                pieces = [subpart]
                if len(subpart) > max_chars:
                    pieces = []
                    piece = ""
                    for word in subpart.split():
                        if piece and len(piece) + len(word) + 1 > max_chars:
                            pieces.append(piece)
                            piece = word
                        else:
                            piece = f"{piece} {word}".strip()
                    if piece:
                        pieces.append(piece)

                for piece in pieces:
                    if current and len(current) + len(piece) + 1 > max_chars:
                        chunks.append(current)
                        current = piece
                    else:
                        current = f"{current} {piece}".strip()

        if current:
            chunks.append(current)

        return chunks or [text]

    def play_audio_file(self, audio_file, interrupt_event=None):
        audio, sample_rate = sf.read(audio_file, dtype="float32", always_2d=True)
        block_size = max(1024, int(sample_rate * 0.04))

        try:
            with sd.OutputStream(
                samplerate=sample_rate,
                channels=audio.shape[1],
                dtype="float32",
                blocksize=block_size
            ) as stream:
                for start in range(0, len(audio), block_size):
                    if interrupt_event is not None and interrupt_event.is_set():
                        stream.abort()
                        return False

                    block = np.ascontiguousarray(audio[start:start + block_size])
                    stream.write(block)

            return True
        finally:
            sd.stop()

    def play_wav(self, wav_file, interrupt_event=None):
        return self.play_audio_file(wav_file, interrupt_event)

    def play_mp3(self, mp3_file, interrupt_event=None):
        try:
            import imageio_ffmpeg

            sample_rate = 24000
            process = subprocess.run(
                [
                    imageio_ffmpeg.get_ffmpeg_exe(),
                    "-v",
                    "error",
                    "-i",
                    mp3_file,
                    "-f",
                    "f32le",
                    "-acodec",
                    "pcm_f32le",
                    "-ac",
                    "1",
                    "-ar",
                    str(sample_rate),
                    "pipe:1",
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True
            )
            samples = np.frombuffer(process.stdout, dtype=np.float32).reshape((-1, 1))

            return self.play_audio_data(
                samples,
                sample_rate,
                interrupt_event
            )
        except Exception as decode_error:
            print(f"[MP3 Decode Error] {decode_error}")

        script = f"""
Add-Type -AssemblyName PresentationCore
$player = New-Object System.Windows.Media.MediaPlayer
$player.Open([Uri]::new('{mp3_file.replace("'", "''")}'))
Start-Sleep -Milliseconds 120
$player.Play()
while ($player.NaturalDuration.HasTimeSpan -eq $false) {{
    Start-Sleep -Milliseconds 50
}}
$duration = $player.NaturalDuration.TimeSpan.TotalMilliseconds
$deadline = (Get-Date).AddMilliseconds($duration + 700)
while ($player.Position.TotalMilliseconds -lt ($duration - 80) -and (Get-Date) -lt $deadline) {{
    Start-Sleep -Milliseconds 50
}}
Start-Sleep -Milliseconds 180
$player.Stop()
$player.Close()
"""
        process = subprocess.Popen(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                script
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        while process.poll() is None:
            if interrupt_event is not None and interrupt_event.is_set():
                subprocess.run(
                    ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                return False

            time.sleep(0.03)

        return process.returncode == 0

    def play_audio_data(self, audio, sample_rate, interrupt_event=None):
        block_size = max(1024, int(sample_rate * 0.035))

        try:
            with sd.OutputStream(
                samplerate=sample_rate,
                channels=audio.shape[1],
                dtype="float32",
                blocksize=block_size
            ) as stream:
                for start in range(0, len(audio), block_size):
                    if interrupt_event is not None and interrupt_event.is_set():
                        stream.abort()
                        return False

                    block = np.ascontiguousarray(audio[start:start + block_size])
                    stream.write(block)

            return True
        finally:
            sd.stop()

    def speak_with_piper(self, text, interrupt_event=None):
        if not os.path.exists(self.piper_exe):
            raise FileNotFoundError(self.piper_exe)

        if not os.path.exists(self.piper_model):
            raise FileNotFoundError(self.piper_model)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            wav_file = tmp.name

        try:
            command = [
                self.piper_exe,
                "--model",
                self.piper_model,
                "--config",
                self.piper_config,
                "--output_file",
                wav_file,
            ]

            subprocess.run(
                command,
                input=text,
                text=True,
                cwd=os.path.dirname(self.piper_exe),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True
            )

            return self.play_wav(wav_file, interrupt_event)
        finally:
            try:
                os.remove(wav_file)
            except OSError:
                pass

    async def create_edge_audio(self, text, output_file, voice, rate):
        import edge_tts

        communicate = edge_tts.Communicate(
            text=text,
            voice=voice,
            rate=rate,
            volume=self.edge_volume
        )
        await communicate.save(output_file)

    def speak_with_edge_tts(self, text, interrupt_event=None, voice=None, rate=None):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
            audio_file = tmp.name

        try:
            asyncio.run(
                self.create_edge_audio(
                    text,
                    audio_file,
                    voice or self.edge_voice,
                    rate or self.edge_rate
                )
            )
            return self.play_mp3(audio_file, interrupt_event)
        finally:
            try:
                os.remove(audio_file)
            except OSError:
                pass

    def speak_with_kokoro(self, text, interrupt_event=None):
        if not self.enable_kokoro:
            return False

        self.load_engine()

        generator = self.pipeline(
            text,
            voice=self.voice,
            speed=self.speed
        )

        played_any = False
        for _, _, audio in generator:
            if interrupt_event is not None and interrupt_event.is_set():
                return False

            wav_file = None
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
                    wav_file = tmp.name

                sf.write(wav_file, audio, self.sample_rate)
                played_any = True

                if not self.play_wav(wav_file, interrupt_event):
                    return False
            finally:
                if wav_file:
                    try:
                        os.remove(wav_file)
                    except OSError:
                        pass

        return played_any

    def speak(self, text, language=None, interrupt_event=None):
        if not text:
            return True

        text = str(text).strip()

        if not text:
            return True

        try:
            use_indonesian_voice = language == "id" or (
                language is None and self.is_indonesian(text)
            )
            chunks = self.split_text(text)

            if use_indonesian_voice:
                chunks = [
                    self.normalize_indonesian_text(chunk)
                    for chunk in chunks
                ]
            else:
                chunks = [
                    self.normalize_english_text(chunk)
                    for chunk in chunks
                ]

            for chunk in chunks:
                if interrupt_event is not None and interrupt_event.is_set():
                    return False

                if use_indonesian_voice:
                    try:
                        completed = self.speak_with_edge_tts(
                            chunk,
                            interrupt_event,
                            self.edge_voice,
                            self.edge_rate
                        )
                    except Exception as edge_error:
                        print(f"[Edge TTS Error] {edge_error}")

                        try:
                            completed = self.speak_with_piper(
                                chunk,
                                interrupt_event
                            )
                        except Exception as piper_error:
                            print(f"[Piper Error] {piper_error}")
                            completed = self.speak_with_kokoro(
                                chunk,
                                interrupt_event
                            )
                else:
                    try:
                        completed = self.speak_with_edge_tts(
                            chunk,
                            interrupt_event,
                            self.edge_english_voice,
                            self.edge_english_rate
                        )
                    except Exception as edge_error:
                        print(f"[Edge TTS Error] {edge_error}")
                        completed = self.speak_with_kokoro(
                            chunk,
                            interrupt_event
                        )

                if not completed:
                    return False

            return True

        except Exception as e:
            print(f"[Speaker Error] {e}")
            return False
