import os
import re
import tempfile
import time

import numpy as np
import sounddevice as sd
import soundfile as sf
from faster_whisper import WhisperModel

try:
    import webrtcvad
except ImportError:
    webrtcvad = None


class Listener:

    def __init__(self):
        self.sample_rate = 16000
        self.chunk_duration = 0.1
        self.max_duration = 12
        self.no_speech_timeout = 2.2
        self.silence_duration = 1.35
        self.energy_threshold = 0.008
        self.noise_multiplier = 2.9
        self.calibration_duration = 0.5
        self.min_speech_duration = 0.42
        self.vad = webrtcvad.Vad(2) if webrtcvad else None
        self.vad_frame_ms = 30
        self.vad_min_ratio = 0.32
        self.stt_beam_size = int(os.getenv("NOVA_STT_BEAM", "1"))
        self.stt_fallback_beam_size = int(os.getenv("NOVA_STT_FALLBACK_BEAM", "1"))
        self.stt_good_score = float(os.getenv("NOVA_STT_GOOD_SCORE", "12"))
        self.stt_fallback_score = float(os.getenv("NOVA_STT_FALLBACK_SCORE", "7"))
        self.initial_prompt = (
            "NOVA desktop assistant commands. "
            "Indonesian and English voice commands: "
            "jam berapa, buka aplikasi, cek status sistem, cuaca hari ini, "
            "berapa lama ke kantor, lihat layar saya, analisa layar ini, "
            "update software, cari lagu di Spotify, putar lagu di Spotify, "
            "cari video YouTube, kurs mata uang, matikan laptop, restart komputer, "
            "rute dan estimasi perjalanan: mall ciputra jakarta barat, grand indonesia, "
            "ice bsd, puri indah mall, mall taman anggrek, kebun raya bogor, "
            "berapa lama ke mall, berapa jam ke jakarta barat, "
            "what time is it, open app, system status, weather today."
        )

        self.model = WhisperModel(
            "small",
            device="cuda",
            compute_type="float16"
        )
        self.last_listen_started = 0

    def chunk_energy(self, chunk):
        return float(np.sqrt(np.mean(chunk ** 2)))

    def audio_stats(self, audio):
        if audio is None or len(audio) == 0:
            return 0.0, 0.0, 0.0

        mono = np.squeeze(audio)
        duration = len(mono) / self.sample_rate
        rms = float(np.sqrt(np.mean(mono ** 2)))
        peak = float(np.max(np.abs(mono)))
        return duration, rms, peak

    def is_usable_audio(self, audio):
        duration, rms, peak = self.audio_stats(audio)

        if duration < 0.35:
            return False

        # Whisper tends to hallucinate text from very quiet clips after long idle.
        if peak < 0.018 and rms < 0.0045:
            return False

        return True

    def chunk_to_pcm16(self, chunk):
        audio = np.squeeze(chunk)
        audio = np.clip(audio, -1.0, 1.0)
        return (audio * 32767).astype(np.int16)

    def is_webrtc_voice(self, chunk):
        if self.vad is None:
            return None

        pcm = self.chunk_to_pcm16(chunk)
        frame_size = int(self.sample_rate * self.vad_frame_ms / 1000)

        if len(pcm) < frame_size:
            return False

        voiced = 0
        total = 0

        for start in range(0, len(pcm) - frame_size + 1, frame_size):
            frame = pcm[start:start + frame_size]
            total += 1

            try:
                if self.vad.is_speech(frame.tobytes(), self.sample_rate):
                    voiced += 1
            except Exception:
                return None

        if total == 0:
            return False

        return (voiced / total) >= self.vad_min_ratio

    def is_voice_chunk(self, chunk, dynamic_threshold, strict=False):
        energy = self.chunk_energy(chunk)
        vad_voice = self.is_webrtc_voice(chunk)

        if vad_voice is None:
            threshold = dynamic_threshold * (1.25 if strict else 1.0)
            return energy >= threshold, energy

        if strict:
            return (
                vad_voice and energy >= max(dynamic_threshold * 1.15, 0.018)
            ), energy

        return (
            (vad_voice and energy >= dynamic_threshold * 0.45) or
            energy >= dynamic_threshold * 1.25
        ), energy

    def clean_transcript(self, text):
        text = " ".join(text.split())
        if not text:
            return ""

        corrections = [
            (r"\banova\s+update your software(?:\s+mode)?\b", "nova update software mu"),
            (r"\bnota\s+update\s+software(?:\s+mode)?\b(?!\s+mu\b)", "nova update software mu"),
            (r"\bnofa\s+update\s+software(?:\s+mode)?\b(?!\s+mu\b)", "nova update software mu"),
            (r"\bnova\s+update\s+software(?:\s+mode)?\b(?!\s+mu\b)", "nova update software mu"),
            (r"\bupdate your software\s+mode\b", "update software mu"),
            (r"\bupdate software\s+mode\b", "update software mu"),
            (r"\bupdate your chest\b", "update software mu"),
            (r"\bupdate your chess\b", "update software mu"),
            (r"\bupdate your test\b", "update software mu"),
            (r"\bupdate your ches\b", "update software mu"),
            (r"\bupdate softwaremu\b", "update software mu"),
            (r"\bupdate softwarenya\b", "update software mu"),
            (r"\bperbarui softwar(?:e|)\b", "perbarui software"),
            (r"\bterima kasih kerana menonton\b", "terima kasih"),
            (r"\bterima kasih karena menonton\b", "terima kasih"),
            (r"\blantor\b", "kantor"),
            (r"\blantoor\b", "kantor"),
            (r"\bkantoor\b", "kantor"),
            (r"\bke kantor\b", "ke kantor"),
            (r"\bkekantor\b", "ke kantor"),
            (r"\bjakatah barat\b", "jakarta barat"),
            (r"\butera jakarta barat\b", "mall ciputra jakarta barat"),
            (r"\butara jakarta barat\b", "mall ciputra jakarta barat"),
            (r"\butera jakarta\b", "mall ciputra jakarta"),
            (r"\bmall utera\b", "mall ciputra"),
            (r"\bmall citra\b", "mall ciputra"),
            (r"(?<!mall\s)\bcitra jakarta barat\b", "mall ciputra jakarta barat"),
            (r"(?<!mall\s)\bciputra jakarta barat\b", "mall ciputra jakarta barat"),
            (r"\bciputra mall\b", "mall ciputra"),
            (r"\bmall putra jakarta(?: barat)?\b", "mall ciputra jakarta barat"),
            (r"\bmall putra\b", "mall ciputra"),
            (r"\bkebun raya (?:bulur|bukur|bokur|bokor|boger|bugur|bohor|botor|tukur|tuker)\b", "kebun raya bogor"),
            (r"\bhotel campinski\b", "Hotel Indonesia Kempinski Jakarta"),
            (r"\bcampinski\b", "Hotel Indonesia Kempinski Jakarta"),
            (r"\bhotel kempinski\b", "Hotel Indonesia Kempinski Jakarta"),
            (r"\bkempinski\b", "Hotel Indonesia Kempinski Jakarta"),
            (r"\bmall tamat anggrek\b", "mall taman anggrek"),
            (r"\btamat anggrek\b", "taman anggrek"),
            (r"\bkuri mall\b", "puri mall"),
            (r"\bcuri mall\b", "puri mall"),
            (r"\bpuri mol+\b", "puri mall"),
            (r"\bais bsd\b", "ice bsd"),
            (r"\bis bsd\b", "ice bsd"),
            (r"\bi c e bsd\b", "ice bsd"),
            (r"\bgeran indonesia\b", "grand indonesia"),
            (r"\bgeren indonesia\b", "grand indonesia"),
            (r"\bgrand indonesa\b", "grand indonesia"),
            (r"\bbuild gates\b", "Bill Gates"),
            (r"\bbil gates\b", "Bill Gates"),
            (r"\bbill gate\b", "Bill Gates"),
            (r"\bspotif(?:i|y)\b", "Spotify"),
            (r"\bbeauty full led\b", "Beautiful Lie"),
            (r"\bbeautiful lead\b", "Beautiful Lie"),
            (r"\bbeautiful lied\b", "Beautiful Lie"),
            (r"\bdewas 19\b", "Dewa 19"),
            (r"\bdos 19\b", "Dewa 19"),
            (r"\byutube\b", "YouTube"),
            (r"\byou tube\b", "YouTube"),
        ]

        cleaned = text
        for pattern, replacement in corrections:
            cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE)

        cleaned = re.sub(r"\bmall\s+mall\s+", "mall ", cleaned, flags=re.IGNORECASE)
        return " ".join(cleaned.split())

    def transcript_score(self, text, preferred_language="id"):
        clean = text.lower().strip()
        if not clean:
            return -100

        words = clean.split()
        score = min(len(words), 12)

        if self.is_repetitive_transcript(clean):
            score -= 60

        command_markers = [
            "nova", "jam", "berapa", "cuaca", "buka", "putar", "cari",
            "spotify", "youtube", "kantor", "kurs", "status", "layar",
            "translate", "bahasa", "what", "who", "how", "weather", "time",
            "mau ke", "ingin ke", "berapa lama", "berapa jam", "waktu tempuh",
            "mall", "ciputra", "grand indonesia", "ice bsd", "puri",
            "taman anggrek", "kebun raya", "kempinski", "campinski",
            "jakarta barat", "jakarta pusat", "bsd",
        ]
        media_markers = ["spotify", "youtube", "lagu", "video", "play", "putar"]
        route_markers = [
            "mau ke", "ingin ke", "berapa lama", "berapa jam", "waktu tempuh",
            "mall", "ciputra", "grand indonesia", "ice bsd", "puri",
            "taman anggrek", "kebun raya", "jakarta barat", "bogor", "bsd",
        ]
        bad_markers = [
            "thanks for watching",
            "thank you for watching",
            "terima kasih kerana menonton",
            "terima kasih karena menonton",
            "subtitles by",
            "amara.org",
            "bye bye",
            "no pasa",
            "que mol",
            "malo",
            "puta",
            "mía",
            "mia ",
            "vamos",
            "gracias",
        ]

        if any(marker in clean for marker in command_markers):
            score += 8

        if any(marker in clean for marker in media_markers):
            score += 5

        if any(marker in clean for marker in route_markers):
            score += 6

        if any(marker in clean for marker in bad_markers):
            score -= 35

        foreign_noise_hits = sum(
            1
            for marker in ["no pasa", "que mol", "malo", "puta", "mía", "mia ", "vamos", "gracias"]
            if marker in clean
        )
        if foreign_noise_hits >= 2 and not any(marker in clean for marker in command_markers):
            score -= 50

        if preferred_language == "id":
            id_markers = [
                "saya", "kamu", "apa", "berapa", "jam", "cuaca", "di",
                "ke", "dari", "hari", "ini", "tolong", "coba", "putar",
            ]
            if any(marker in words for marker in id_markers):
                score += 4

        if len(words) <= 2 and not any(marker in clean for marker in command_markers):
            score -= 8

        return score

    def is_repetitive_transcript(self, text):
        words = text.lower().split()

        if len(words) < 10:
            return False

        unique_ratio = len(set(words)) / len(words)
        if unique_ratio <= 0.28:
            return True

        bigrams = list(zip(words, words[1:]))
        if len(bigrams) < 6:
            return False

        most_common = max(bigrams.count(bigram) for bigram in set(bigrams))
        return most_common >= 4 and most_common / len(bigrams) >= 0.28

    def transcribe_file(self, audio_path, preferred_language="id"):
        variants = [
            {
                "language": preferred_language,
                "beam_size": self.stt_beam_size,
                "initial_prompt": self.initial_prompt,
            },
        ]

        if preferred_language:
            variants.append(
                {
                    "language": None,
                    "beam_size": self.stt_fallback_beam_size,
                    "initial_prompt": self.initial_prompt,
                }
            )

        best_text = ""
        best_score = -100

        for index, variant in enumerate(variants):
            segments, _ = self.model.transcribe(
                audio_path,
                language=variant["language"],
                beam_size=variant["beam_size"],
                vad_filter=True,
                vad_parameters={
                    "min_silence_duration_ms": 850,
                    "speech_pad_ms": 320,
                },
                initial_prompt=variant["initial_prompt"],
                temperature=0.0,
                condition_on_previous_text=False
            )

            text = ""
            segment_count = 0
            no_speech_probs = []
            avg_logprobs = []
            compression_ratios = []
            for segment in segments:
                segment_count += 1
                no_speech_probs.append(getattr(segment, "no_speech_prob", 0.0) or 0.0)
                avg_logprobs.append(getattr(segment, "avg_logprob", 0.0) or 0.0)
                compression_ratios.append(getattr(segment, "compression_ratio", 0.0) or 0.0)
                text += segment.text + " "

            text = self.clean_transcript(text)
            score = self.transcript_score(text, preferred_language)

            if segment_count == 0:
                score -= 40

            if no_speech_probs and float(np.mean(no_speech_probs)) >= 0.68:
                score -= 14

            if avg_logprobs and float(np.mean(avg_logprobs)) <= -0.85:
                score -= 10

            if compression_ratios and max(compression_ratios) >= 2.5:
                score -= 18

            if score > best_score:
                best_text = text
                best_score = score

            if best_score >= self.stt_good_score:
                break

            if index == 0 and best_score >= self.stt_fallback_score:
                break

        return best_text

    def record_until_silence(
        self,
        max_duration=None,
        no_speech_timeout=None,
        silence_duration=None,
        min_speech_duration=None,
    ):
        block_size = int(self.sample_rate * self.chunk_duration)
        max_chunks = int((max_duration or self.max_duration) / self.chunk_duration)
        no_speech_chunks = int((no_speech_timeout or self.no_speech_timeout) / self.chunk_duration)
        silence_chunks_needed = int((silence_duration or self.silence_duration) / self.chunk_duration)
        min_speech_chunks = int((min_speech_duration or self.min_speech_duration) / self.chunk_duration)

        frames = []
        pre_roll = []
        started = False
        silent_chunks = 0
        speech_chunks = 0
        noise_floor = self.energy_threshold / self.noise_multiplier
        idle_seconds = time.monotonic() - self.last_listen_started if self.last_listen_started else 0
        self.last_listen_started = time.monotonic()

        if idle_seconds >= 90:
            try:
                sd.stop()
            except Exception:
                pass

        with sd.InputStream(
            samplerate=self.sample_rate,
            channels=1,
            dtype="float32",
            blocksize=block_size
        ) as stream:
            calibration_chunks = max(3, int(self.calibration_duration / self.chunk_duration))
            calibration_energies = []

            for _ in range(calibration_chunks):
                chunk, _ = stream.read(block_size)
                energy = self.chunk_energy(chunk)
                calibration_energies.append(energy)
                pre_roll.append(chunk.copy())
                pre_roll = pre_roll[-3:]

            if calibration_energies:
                baseline = float(np.percentile(calibration_energies, 30))
                noise_floor = max(noise_floor, baseline)

            for index in range(max_chunks):
                chunk, _ = stream.read(block_size)
                dynamic_threshold = max(
                    self.energy_threshold,
                    noise_floor * self.noise_multiplier
                )
                is_voice, energy = self.is_voice_chunk(
                    chunk,
                    dynamic_threshold
                )

                if not started:
                    if energy < dynamic_threshold:
                        noise_floor = (noise_floor * 0.92) + (energy * 0.08)

                    pre_roll.append(chunk.copy())
                    pre_roll = pre_roll[-3:]

                    if is_voice:
                        started = True
                        frames.extend(pre_roll)
                        silent_chunks = 0
                        speech_chunks = 1
                    elif index >= no_speech_chunks:
                        return None

                    continue

                frames.append(chunk.copy())

                if is_voice:
                    silent_chunks = 0
                    speech_chunks += 1
                else:
                    silent_chunks += 1

                if (
                    speech_chunks >= min_speech_chunks and
                    silent_chunks >= silence_chunks_needed
                ):
                    break

        if not frames or speech_chunks < min_speech_chunks:
            return None

        audio = np.concatenate(frames, axis=0)
        if not self.is_usable_audio(audio):
            return None

        return audio

    def wait_for_barge_in(
        self,
        stop_event,
        min_delay=1.25,
        min_voice_duration=0.75,
        threshold_multiplier=4.6,
        absolute_threshold=0.052,
    ):
        block_size = int(self.sample_rate * self.chunk_duration)
        speech_chunks_needed = max(
            4,
            int(min_voice_duration / self.chunk_duration)
        )
        voice_chunks = 0
        started = time.monotonic()

        with sd.InputStream(
            samplerate=self.sample_rate,
            channels=1,
            dtype="float32",
            blocksize=block_size
        ) as stream:
            while not stop_event.is_set():
                chunk, _ = stream.read(block_size)

                if time.monotonic() - started < min_delay:
                    continue

                is_voice, _ = self.is_voice_chunk(
                    chunk,
                    max(self.energy_threshold * threshold_multiplier, absolute_threshold),
                    strict=True
                )

                if is_voice:
                    voice_chunks += 1
                else:
                    voice_chunks = max(0, voice_chunks - 1)

                if voice_chunks >= speech_chunks_needed:
                    return True

        return False

    def listen(
        self,
        max_duration=None,
        no_speech_timeout=None,
        silence_duration=None,
        min_speech_duration=None,
        preferred_language="id",
    ):
        audio = self.record_until_silence(
            max_duration=max_duration,
            no_speech_timeout=no_speech_timeout,
            silence_duration=silence_duration,
            min_speech_duration=min_speech_duration,
        )

        if audio is None:
            return ""

        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as file:
            audio_path = file.name

        try:
            sf.write(audio_path, audio, self.sample_rate)

            return self.transcribe_file(audio_path, preferred_language)

        finally:
            try:
                os.remove(audio_path)
            except OSError:
                pass
