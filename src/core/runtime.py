from core.listener import Listener
from core.speaker import Speaker
from core.brain import Brain
from core.command import CommandEngine
from core.online_tools import OnlineTools
from commands.router import CommandRouter
import threading
import re
import time
import random
from collections import deque
import os


WAKE_WORDS = [
    "nova",
    "anova",
    "a nova",
    "hey nova",
    "hei nova",
    "hai nova",
    "okay nova",
    "ok nova",
    "hi nova",
    "no va",
    "no far",
    "not far",
    "not for",
    "not fine",
    "nofar",
    "nofa",
    "novah",
    "nover",
    "no the",
    "know va",
]

WAKE_PHRASES = WAKE_WORDS + [
    "wake up",
    "wake nova",
    "bangun",
    "bangun nova",
    "aktif",
    "aktifkan",
    "aktifkan nova",
]


def clean_text(text):
    text = str(text or "").lower()

    for char in [",", ".", "!", "?", ";", ":"]:
        text = text.replace(char, "")

    return " ".join(text.split())


def is_repetitive_text(text):
    words = clean_text(text).split()

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


def looks_like_command_or_question(text):
    command = clean_text(text)
    if not command:
        return False

    question_markers = [
        "apa",
        "apakah",
        "siapa",
        "kenapa",
        "mengapa",
        "bagaimana",
        "gimana",
        "berapa",
        "kapan",
        "dimana",
        "di mana",
        "what",
        "who",
        "why",
        "how",
        "when",
        "where",
        "can you",
        "could you",
    ]

    return (
        any(marker in command for marker in COMMAND_MARKERS) or
        any(marker in command for marker in question_markers)
    )


def contains(text, words):
    text = clean_text(text)
    return any(word in text for word in words)


def contains_phrase(text, phrases):
    text = clean_text(text)

    for phrase in phrases:
        phrase = clean_text(phrase)

        if re.search(rf"(?<!\w){re.escape(phrase)}(?!\w)", text):
            return True

    return False


def remove_wake_word(text):
    result = clean_text(text)

    for word in sorted(WAKE_PHRASES, key=len, reverse=True):
        result = re.sub(
            rf"(?<!\w){re.escape(clean_text(word))}(?!\w)",
            " ",
            result
        )

    return result.strip()


def detect_language(text):
    command = clean_text(text)
    indonesian_markers = [
        "apa",
        "apakah",
        "buka",
        "bukakan",
        "cari",
        "carikan",
        "cuaca",
        "cek",
        "di",
        "dari",
        "hari ini",
        "bisa apa",
        "kemampuan",
        "fitur",
        "jam",
        "berapa",
        "pukul",
        "sekarang",
        "status sistem",
        "status laptop",
        "kondisi",
        "matikan",
        "komputer",
        "mulai ulang",
        "tidurkan",
        "baterai",
        "kurs",
        "dolar",
        "dollar",
        "rupiah",
        "harga jual",
        "tidak",
        "nggak",
        "enggak",
        "iya",
        "ya",
        "batal",
        "jangan",
        "lanjut",
        "menurut",
        "kamu",
        "gimana",
        "bagaimana",
        "cara",
        "menaikkan",
        "menurunkan",
        "berat badan",
        "sehat",
        "maksimal",
        "makan",
        "minum",
        "latihan",
        "olahraga",
        "secara",
        "untuk",
        "dengan",
        "tentang",
        "lebih dalam",
        "gali",
        "jelaskan",
        "saya",
        "perbarui",
        "muat ulang",
        "software mu",
        "update software mu",
        "restart aplikasi",
    ]

    words = command.split()

    for marker in indonesian_markers:
        if len(marker) <= 3:
            if marker in words:
                return "id"
        elif marker in command:
            return "id"

    return "en"


def clean_answer_text(text):
    text = str(text)
    replacements = {
        "â€“": "-",
        "â€”": "-",
        "â€˜": "'",
        "â€™": "'",
        "â€œ": '"',
        "â€": '"',
        "Â°C": "°C",
        "Â": "",
        "â": "",
    }

    for source, replacement in replacements.items():
        text = text.replace(source, replacement)

    symbol_replacements = {
        "ï¿½": " ",
        "â–¡": " > ",
        "→": " > ",
        "⇒": " > ",
        "➜": " > ",
        "➡": " > ",
        "➔": " > ",
        "□": " > ",
        "▯": " > ",
        "▢": " > ",
    }
    for source, replacement in symbol_replacements.items():
        text = text.replace(source, replacement)

    text = text.replace("ï¿½", " ")
    text = text.replace("�", " ")
    text = text.replace("□", " ")
    text = re.sub(r"\bUser Safety:\s*safe\b\.?", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = re.sub(r"\*(.*?)\*", r"\1", text)
    text = re.sub(r"__([^_]+)__", r"\1", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"#{1,6}\s*", "", text)
    text = re.sub(r"\bNatural\s*:", ". Natural:", text, flags=re.IGNORECASE)
    text = re.sub(r"\bTerjemahan\s*:", "Terjemahan:", text, flags=re.IGNORECASE)
    text = re.sub(r"(?<=\d)[^\w\s.,%°]+(?=\d)", "-", text)
    text = re.sub(r"[�□]+", "", text)
    text = re.sub(r"[□▯▢]+", " > ", text)
    text = re.sub(r"[→⇒➜➡➔]+", " > ", text)
    text = re.sub(r"(?<=\w)\s*\?{2,}\s*(?=\w)", " > ", text)
    text = re.sub(r"\s*>\s*(?:>\s*)+", " > ", text)
    text = re.sub(r"\s*>\s*", " > ", text)
    text = re.sub(r"\s+", " ", text)
    text = text.replace(" - ", "; ")
    return text.strip()


SHORT_COMMAND_MARKERS = [
    "ya",
    "iya",
    "yes",
    "yeah",
    "yep",
    "ok",
    "okay",
    "oke",
    "tidak",
    "no",
    "batal",
    "jangan",
    "sleep",
    "tidur",
    "bangun",
    "wake",
    "cuaca",
    "weather",
    "time",
    "jam",
    "tanggal",
    "status",
    "kurs",
]


COMMAND_MARKERS = SHORT_COMMAND_MARKERS + [
    "buka",
    "open",
    "matikan",
    "shutdown",
    "restart",
    "mulai ulang",
    "baterai",
    "battery",
    "laptop",
    "sistem",
    "system",
    "dolar",
    "dollar",
    "rupiah",
    "presiden",
    "president",
    "apa",
    "apakah",
    "siapa",
    "who",
    "what",
    "why",
    "how",
    "mau ke",
    "ingin ke",
    "berapa lama",
    "berapa jam",
    "waktu tempuh",
    "kantor",
    "rumah",
    "mall",
    "ciputra",
    "grand indonesia",
    "ice bsd",
    "puri",
    "taman anggrek",
    "kebun raya",
    "bogor",
    "jakarta barat",
    "spotify",
    "youtube",
    "lagu",
    "video",
    "update software",
    "software mu",
]


NOISE_FRAGMENTS = [
    "number of",
    "thank you",
    "thanks",
    "sorry",
    "sorry sorry",
    "terima kasih",
    "terima kasih kerana menonton",
    "terima kasih karena menonton",
    "thanks for watching",
    "thank you for watching",
    "subtitles by",
    "amara.org",
    "no pasa",
    "que mol",
    "malo",
    "puta",
    "mia",
    "mía",
    "vamos",
    "gracias",
]


class NovaRuntime:

    def __init__(self):
        self.listener = Listener()
        self.speaker = Speaker()
        self.brain = Brain()
        self.online_tools = OnlineTools()
        self.router = CommandRouter()
        self.command_engine = CommandEngine()
        self.pending_action = None
        self.pending_language = "id"
        self.current_language = "id"
        self.sleeping = False
        self.running = False
        self.last_status = None
        self.pending_youtube_search = False
        self.pending_media_search = None
        self.forced_speech_language = None
        self.pending_middle_rate_command = None
        self.pending_middle_rate_language = "id"
        self.pending_route_destination = None
        self.pending_route_language = "id"
        self.pending_route_retry_until = 0
        self.last_middle_rate_command = None
        self.last_middle_rate_language = "id"
        self.last_middle_rate_time = 0
        self.last_weather_location = None
        self.last_weather_language = "id"
        self.last_weather_time = 0
        self.session_window_seconds = 45
        self.startup_window_seconds = 75
        self.context_window_seconds = 90
        self.followup_until = 0
        self.conversation_context = None
        self.recent_contexts = deque(maxlen=5)
        self.last_transcript = ""
        self.last_transcript_time = 0
        self.last_spoken_text = ""
        self.last_spoken_time = 0
        self.listen_mute_until = 0
        self.is_speaking = False
        self.enable_barge_in = os.getenv("NOVA_ENABLE_BARGE_IN", "1") != "0"

    def build_ready_greeting(self):
        hour = time.localtime().tm_hour

        if 4 <= hour < 11:
            period = "pagi"
        elif 11 <= hour < 15:
            period = "siang"
        elif 15 <= hour < 18:
            period = "sore"
        else:
            period = "malam"

        endings = [
            "NOVA sudah aktif dan siap membantu. Semoga harimu berjalan lancar.",
            "Saya sudah siap menemani pekerjaanmu. Semoga hari ini produktif dan menyenangkan.",
            "Sistem sudah siap. Semoga semua urusanmu hari ini berjalan mulus.",
            "Saya aktif sekarang. Mari kita buat hari ini lebih ringan dan teratur.",
            "NOVA siap menerima perintah. Semoga harimu menyenangkan.",
        ]

        return f"Selamat {period} Alfred. {random.choice(endings)}"

    def stop(self):
        self.running = False

    def open_followup_window(self):
        self.followup_until = time.monotonic() + self.session_window_seconds
        self.sleeping = False

    def open_startup_window(self):
        self.followup_until = time.monotonic() + self.startup_window_seconds
        self.sleeping = False

    def followup_window_active(self):
        return time.monotonic() <= self.followup_until

    def close_followup_window(self):
        self.followup_until = 0
        self.sleeping = True

    def remember_context(self, route, user_text, answer):
        if route.get("type") not in ("command", "chat"):
            return

        if route.get("type") == "command" and route.get("action") == "maps_route":
            if self.is_route_not_found_answer(answer):
                self.pending_route_retry_until = (
                    time.monotonic() + self.context_window_seconds
                )
            else:
                self.pending_route_retry_until = 0

        self.conversation_context = {
            "created_at": time.monotonic(),
            "action": route.get("action", route.get("type", "")),
            "user": user_text,
            "answer": answer,
            "language": self.current_language,
        }
        self.recent_contexts.append(self.conversation_context)
        self.prune_recent_contexts()

    def prune_recent_contexts(self):
        now = time.monotonic()
        fresh_contexts = [
            context for context in self.recent_contexts
            if now - context.get("created_at", 0) <= self.context_window_seconds
        ]
        self.recent_contexts = deque(fresh_contexts[-5:], maxlen=5)

    def get_recent_context(self):
        self.prune_recent_contexts()

        if not self.conversation_context:
            return None

        age = time.monotonic() - self.conversation_context["created_at"]
        if age > self.context_window_seconds:
            self.conversation_context = None
            if self.recent_contexts:
                self.conversation_context = self.recent_contexts[-1]
                return self.conversation_context
            return None

        return self.conversation_context

    def remember_weather_context(self, text, language):
        try:
            location = self.command_engine.extract_weather_location(text, language)
        except Exception:
            location = None

        if location:
            self.last_weather_location = location
            self.last_weather_language = language
            self.last_weather_time = time.monotonic()

    def weather_context_active(self):
        return (
            self.last_weather_location is not None and
            time.monotonic() - self.last_weather_time <= self.context_window_seconds
        )

    def is_weather_followup(self, text):
        command = clean_text(text)

        if not command or not self.weather_context_active():
            return False

        weather_followup_markers = [
            "gerimis",
            "hujan",
            "cerah",
            "berawan",
            "mendung",
            "panas",
            "dingin",
            "suhu",
            "kelembapan",
            "di ",
            "area",
            "daerah",
            "juga",
            "hari ini",
            "sekarang",
        ]

        return any(marker in command for marker in weather_followup_markers)

    def extract_weather_followup_location(self, text):
        command = clean_text(text)

        patterns = [
            r"\bdi\s+(.+?)(?:\s+apakah|\s+apa|\s+gimana|\s+bagaimana|\s+akan|\s+juga|\s+hari ini|\s+sekarang|$)",
            r"\bdaerah\s+(.+?)(?:\s+apakah|\s+apa|\s+gimana|\s+bagaimana|\s+akan|\s+juga|\s+hari ini|\s+sekarang|$)",
            r"\barea\s+(.+?)(?:\s+apakah|\s+apa|\s+gimana|\s+bagaimana|\s+akan|\s+juga|\s+hari ini|\s+sekarang|$)",
        ]

        for pattern in patterns:
            match = re.search(pattern, command)
            if match:
                location = match.group(1).strip()
                if location:
                    return location

        return self.last_weather_location

    def enrich_weather_followup_text(self, text, route):
        if route.get("type") == "command" and route.get("action") == "weather":
            return text, route

        if not self.is_weather_followup(text):
            return text, route

        location = self.extract_weather_followup_location(text)
        if not location:
            location = self.last_weather_location or "Jakarta"

        enriched_text = f"cuaca di {location} hari ini"
        return enriched_text, {
            "type": "command",
            "action": "weather",
            "message": enriched_text,
        }

    def route_retry_active(self):
        return time.monotonic() <= self.pending_route_retry_until

    def clear_route_context(self):
        self.pending_route_destination = None
        self.pending_route_language = None
        self.pending_route_retry_until = 0

    def is_pending_route_followup(self, route, text):
        if route.get("type") == "command" and route.get("action") == "maps_route":
            return True

        return self.route_retry_active() and self.is_likely_route_retry_text(text)

    def is_route_not_found_answer(self, answer):
        command = clean_text(answer)
        markers = [
            "rute tidak ditemukan",
            "route not found",
            "tidak menemukan tujuan",
            "tidak dapat menemukan tujuan",
            "tolong ulangi nama tujuan",
            "please repeat the destination",
            "can't find",
            "cant find",
            "cannot find",
            "can not find",
            "make sure your search is spelled",
            "spelled correctly",
            "try adding a city",
            "periksa ejaan",
            "tidak ditemukan ulangi nama tujuan",
        ]
        return any(marker in command for marker in markers)

    def is_likely_route_retry_text(self, text):
        command = clean_text(text)

        if not command:
            return False

        cancel_markers = ["batal", "cancel", "tidak jadi", "jangan"]
        if any(marker in command for marker in cancel_markers):
            return True

        route_intent_markers = [
            "maksudnya",
            "maksud saya",
            "tujuannya",
            "yang benar",
            "seharusnya",
            "ulang",
            "coba ke",
            "cek ke",
            "mau ke",
            "ingin ke",
            "pengen ke",
            "pergi ke",
            "berangkat ke",
            "arah ke",
            "menuju",
            "rute",
            "maps",
            "google maps",
        ]
        route_time_markers = [
            "berapa lama",
            "berapa jam",
            "waktu tempuh",
            "butuh berapa",
            "perlu berapa",
            "estimasi",
            "perjalanan",
            "durasi",
        ]
        place_markers = [
            "mall",
            "hotel",
            "jalan ",
            "jl ",
            "jl.",
            "gedung",
            "kantor",
            "rumah",
            "bandara",
            "stasiun",
            "terminal",
            "taman",
            "kebun",
            "raya",
            "jakarta",
            "bogor",
            "bsd",
            "tangerang",
            "bekasi",
            "depok",
            "sentul",
            "ciputra",
            "kempinski",
            "campinski",
            "grand indonesia",
            "ice bsd",
            "puri",
            "anggrek",
            "cafe",
            "kafe",
            "restoran",
            "restaurant",
            "rumah sakit",
            "rs ",
            "klinik",
            "sekolah",
            "universitas",
            "apartemen",
            "residence",
            "tower",
            "plaza",
            "indonesia",
        ]
        has_route_intent = any(marker in command for marker in route_intent_markers)
        has_route_time = any(marker in command for marker in route_time_markers)
        has_place_marker = any(marker in command for marker in place_markers)

        new_task_markers = [
            "apa penyebab",
            "penyebab",
            "gejala",
            "penyakit",
            "kolesterol",
            "asam urat",
            "darah tinggi",
            "obat",
            "sejarah",
            "siapa",
            "mengapa",
            "kenapa",
            "jelaskan",
            "menurut",
            "bahasa inggris",
            "bahasa indonesia",
            "translate",
            "terjemah",
            "cuaca",
            "kurs",
            "spotify",
            "youtube",
            "lagu",
            "video",
            "jam berapa sekarang",
            "status",
            "harga",
            "bitcoin",
            "crypto",
            "update",
            "software",
            "apa itu",
            "apa yang",
            "terima kasih",
            "thanks",
            "thank you",
        ]
        if any(marker in command for marker in new_task_markers) and not (
            has_route_intent or (has_route_time and has_place_marker)
        ):
            return False

        if has_route_intent:
            return True

        if has_route_time and has_place_marker:
            return True

        if re.match(r"^(ke|menuju)\s+\S+", command):
            return True

        return has_place_marker and len(command.split()) <= 7

    def extract_route_retry_destination(self, text):
        raw = str(text or "").strip()
        command = clean_text(raw)

        if not command:
            return ""

        cancel_markers = ["batal", "cancel", "tidak jadi", "jangan"]
        if any(marker in command for marker in cancel_markers):
            self.pending_route_retry_until = 0
            return ""

        if not self.is_likely_route_retry_text(command):
            self.pending_route_retry_until = 0
            return ""

        destination = command
        prefixes = [
            r"^(maksudnya|maksud saya|tujuannya|yang benar|seharusnya)\s+",
            r"^(coba\s+ke|cek\s+ke|ke|menuju|saya\s+mau\s+ke|saya\s+ingin\s+ke|saya\s+pengen\s+ke|pergi\s+ke)\s+",
        ]
        for pattern in prefixes:
            destination = re.sub(pattern, "", destination).strip()

        destination = re.sub(
            r"\b(berapa\s+lama|berapa\s+jam|butuh\s+berapa\s+lama|coba\s+cek|cek\s+rute|rutenya|waktu\s+tempuh|perjalanan|google\s+maps|maps)\b",
            "",
            destination,
        )
        destination = destination.strip(" .,:;?!")

        if not destination or len(destination.split()) > 10:
            return ""

        reject_markers = [
            "apa penyebab",
            "penyebab",
            "gejala",
            "penyakit",
            "kolesterol",
            "asam urat",
            "darah tinggi",
            "obat",
            "sejarah",
            "siapa",
            "mengapa",
            "kenapa",
            "jelaskan",
            "menurut",
            "bahasa inggris",
            "bahasa indonesia",
            "translate",
            "terjemah",
            "cuaca",
            "kurs",
            "spotify",
            "youtube",
            "lagu",
            "video",
            "jam berapa sekarang",
            "status",
            "harga",
            "bitcoin",
            "crypto",
            "update",
            "software",
            "apa itu",
            "apa yang",
            "terima kasih",
            "thanks",
            "thank you",
        ]
        if any(marker in destination for marker in reject_markers):
            self.pending_route_retry_until = 0
            return ""

        return self.command_engine.normalize_route_destination_name(destination)

    def enrich_route_retry_text(self, text, route):
        if not self.route_retry_active():
            return text, route

        if route.get("type") == "command" and route.get("action") == "maps_route":
            return text, route

        if not self.is_likely_route_retry_text(text):
            self.pending_route_retry_until = 0
            return text, route

        destination = self.extract_route_retry_destination(text)
        if not destination:
            return text, route

        enriched_text = f"saya mau ke {destination} berapa lama"
        return enriched_text, {
            "type": "command",
            "action": "maps_route",
            "message": enriched_text,
        }

    def is_followup_question(self, text):
        command = clean_text(text)

        if not command:
            return False

        command = re.sub(r"^(oke|ok|okay|baik|ya|iya)\s+", "", command)

        starters = [
            "kalau",
            "kalo",
            "lalu",
            "terus",
            "bagaimana kalau",
            "gimana kalau",
            "bagaimana dengan",
            "gimana dengan",
            "dan",
            "kalau di",
            "lalu di",
            "terus di",
            "what about",
            "how about",
            "and",
            "then",
        ]

        question_words = [
            "dimana",
            "di mana",
            "area mana",
            "daerah mana",
            "lokasi",
            "kenapa",
            "mengapa",
            "memangnya",
            "apa bedanya",
            "berapa",
            "dia",
            "itu",
            "tersebut",
            "lebih dalam",
            "gali lebih dalam",
            "jelaskan lagi",
            "lanjutkan",
        ]

        if any(command.startswith(starter) for starter in starters):
            return True

        if any(starter in command for starter in starters):
            return True

        return any(word in command for word in question_words)

    def extract_context_subject(self, context):
        texts = [
            context.get("user", ""),
            context.get("answer", ""),
        ]

        known_subjects = [
            "Bill Gates",
            "Ade Rai",
            "Microsoft",
        ]

        joined = " ".join(texts).lower()
        for subject in known_subjects:
            if subject.lower() in joined:
                return subject

        for text in texts:
            match = re.search(
                r"(?:siapa|apa itu|tentang|mengenai)\s+([a-zA-Z][a-zA-Z\s.'-]{2,60})",
                text,
                flags=re.IGNORECASE,
            )

            if match:
                subject = match.group(1)
                subject = re.sub(
                    r"\b(?:ini|itu|dia|kak|pak|bu|adalah|yang|di|dari|dan)\b.*$",
                    "",
                    subject,
                    flags=re.IGNORECASE,
                )
                subject = " ".join(subject.split()).strip(" .?!,")

                if len(subject) >= 3:
                    return subject.title()

        for text in texts:
            candidates = re.findall(
                r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3}\b",
                text
            )
            ignored = {"Saya", "Dari", "The", "From", "Online", "Search"}
            candidates = [
                candidate for candidate in candidates
                if candidate not in ignored
            ]

            if candidates:
                return candidates[0]

        return ""

    def enrich_online_search_query(self, text):
        context = self.get_recent_context()

        if not context or not self.is_followup_question(text):
            return text

        subject = self.extract_context_subject(context)

        if not subject:
            return text

        command = clean_text(text)
        depth_markers = [
            "gali lebih dalam",
            "lebih dalam",
            "jelaskan lagi",
            "cari tahu lebih dalam",
            "bahas lebih dalam",
        ]

        if any(marker in command for marker in depth_markers):
            return (
                f"Cari informasi lebih dalam tentang {subject}. "
                "Fokus pada latar belakang, peran penting, pencapaian, "
                "dan hal-hal yang relevan."
            )

        if any(pronoun in command.split() for pronoun in ["dia", "itu"]):
            return f"{text} tentang {subject}"

        return text

    def prepare_online_search_query(self, text):
        query = (text or "").strip()
        command = clean_text(query)

        vehicle_corrections = {
            "hyundai kereta": "Hyundai Creta",
            "hyundai kerta": "Hyundai Creta",
            "hyundai kreta": "Hyundai Creta",
            "hyundai creta": "Hyundai Creta",
        }

        for source, replacement in vehicle_corrections.items():
            query = re.sub(
                rf"(?<!\w){re.escape(source)}(?!\w)",
                replacement,
                query,
                flags=re.IGNORECASE,
            )

        price_markers = [
            "berapa harga",
            "harga berapa",
            "cek harga",
            "cari harga",
            "carikan harga",
            "harga terbaru",
            "harga sekarang",
            "price of",
            "how much is",
            "what is the price",
        ]
        price_exclusions = [
            "kurs",
            "exchange rate",
            "usd",
            "dollar",
            "dolar",
            "euro",
            "eur",
            "bitcoin",
            "btc",
            "ethereum",
            "eth",
        ]

        if (
            any(marker in command for marker in price_markers) and
            not any(marker in command for marker in price_exclusions)
        ):
            return f"{query} harga terbaru OTR Indonesia Jakarta 2026 situs resmi dealer"

        return query

    def enrich_followup_text(self, text, route):
        context = self.get_recent_context()

        if not context:
            return text, route

        if context.get("action") == "maps_route":
            if (
                route.get("type") == "command" and
                route.get("action") == "maps_route"
            ):
                return text, route

            if self.route_retry_active() and self.is_likely_route_retry_text(text):
                return text, route

            self.clear_route_context()
            return text, route

        if not self.is_followup_question(text):
            return text, route

        if (
            context.get("action") == "world_time" and
            route.get("type") == "chat"
        ):
            combined_text = f"jam berapa sekarang {text}"
            return combined_text, self.router.route(combined_text)

        if (
            route.get("type") == "command" and
            route.get("action") == "online_search"
        ):
            enriched_text = self.enrich_online_search_query(text)
            return enriched_text, route

        if route.get("type") == "chat":
            if self.current_language == "id":
                prompt = (
                    "Ini adalah pertanyaan lanjutan dari percakapan sebelumnya. "
                    "Jawab dengan memahami konteks, jangan mulai dari nol.\n\n"
                    f"Pertanyaan sebelumnya: {context['user']}\n"
                    f"Jawaban sebelumnya: {context['answer']}\n"
                    f"Pertanyaan lanjutan: {text}"
                )
            else:
                prompt = (
                    "This is a follow-up question. Answer using the previous context, "
                    "not as a brand-new topic.\n\n"
                    f"Previous question: {context['user']}\n"
                    f"Previous answer: {context['answer']}\n"
                    f"Follow-up question: {text}"
                )

            return prompt, route

        return text, route

    def is_low_value_fragment(self, text):
        command = clean_text(text)

        if not command:
            return True

        if is_repetitive_text(command):
            return True

        if self.is_foreign_noise_transcript(command):
            return True

        if self.pending_middle_rate_command:
            return False

        if self.pending_media_search:
            return False

        if self.pending_action:
            return False

        if command in NOISE_FRAGMENTS:
            return True

        if any(marker in command for marker in COMMAND_MARKERS):
            return False

        words = command.split()

        if len(words) <= 6 and not looks_like_command_or_question(command):
            return True

        return len(words) <= 2

    def is_bad_transcript(self, text):
        command = clean_text(text)

        if not command:
            return True

        if is_repetitive_text(command):
            return True

        if self.is_foreign_noise_transcript(command):
            return True

        bad_markers = [
            "terima kasih kerana menonton",
            "terima kasih karena menonton",
            "thanks for watching",
            "thank you for watching",
            "subtitles by",
            "amaraorg",
            "bye bye",
        ]

        if any(marker in command for marker in bad_markers):
            return True

        if command in NOISE_FRAGMENTS:
            return True

        words = command.split()
        if len(words) <= 2 and not any(marker in command for marker in SHORT_COMMAND_MARKERS):
            return True

        return False

    def is_foreign_noise_transcript(self, text):
        command = clean_text(text)
        if not command:
            return False

        protected_markers = [
            "nova",
            "jam",
            "berapa",
            "cuaca",
            "buka",
            "putar",
            "cari",
            "spotify",
            "youtube",
            "kantor",
            "kurs",
            "status",
            "layar",
            "bahasa",
            "mau ke",
            "ingin ke",
            "mall",
            "ciputra",
            "grand indonesia",
            "ice bsd",
            "kebun raya",
            "jakarta",
            "puri",
            "taman anggrek",
        ]
        if any(marker in command for marker in protected_markers):
            return False

        padded = f" {command} "
        foreign_markers = [
            "no pasa",
            "que mol",
            "malo",
            "puta",
            "mia ",
            "mía",
            "vamos",
            "gracias",
            "por favor",
        ]
        hits = sum(1 for marker in foreign_markers if marker in padded)
        return hits >= 2

    def is_duplicate_transcript(self, text, window_seconds=4.0):
        command = clean_text(text)

        if not command:
            return True

        now = time.monotonic()
        if (
            command == self.last_transcript and
            now - self.last_transcript_time <= window_seconds
        ):
            return True

        self.last_transcript = command
        self.last_transcript_time = now
        return False

    def looks_like_route_area_followup(self, text):
        command = clean_text(text)
        if not command:
            return False

        blockers = [
            "apa penyebab", "penyebab", "gejala", "penyakit", "kolesterol",
            "asam urat", "darah tinggi", "masuk angin", "bahasa inggris",
            "bahasa indonesia", "translate", "terjemah", "spotify", "youtube",
            "lagu", "video", "harga", "kurs", "bitcoin", "dollar", "dolar",
            "euro", "apa itu", "siapa", "jelaskan", "menurut", "cuaca",
            "weather", "status", "update", "software",
        ]
        if any(marker in command for marker in blockers):
            return False

        area_terms = [
            "jakarta", "bogor", "depok", "tangerang", "bekasi", "sentul",
            "bsd", "serpong", "cengkareng", "puri", "barat", "timur",
            "utara", "selatan", "pusat", "banten", "jawa",
        ]
        if any(marker in command for marker in area_terms):
            return True

        question_terms = ["apa", "berapa", "kenapa", "gimana", "bagaimana"]
        words = command.split()
        return len(words) <= 4 and not any(term in command for term in question_terms)

    def mute_listening(self, seconds=0.8):
        self.listen_mute_until = max(
            self.listen_mute_until,
            time.monotonic() + seconds
        )

    def post_speech_mute_seconds(self, text):
        return max(2.0, min(4.0, 1.4 + len(str(text)) / 1500))

    def wait_until_listening_allowed(self):
        while self.running and self.is_speaking:
            time.sleep(0.05)

        remaining = self.listen_mute_until - time.monotonic()
        if remaining > 0:
            time.sleep(min(remaining, 1.5))

    def remember_spoken_text(self, text):
        spoken = clean_text(text)
        if not spoken:
            return

        self.last_spoken_text = spoken
        self.last_spoken_time = time.monotonic()

    def is_echo_transcript(self, text, window_seconds=18.0):
        command = clean_text(text)
        if not command or not self.last_spoken_text:
            return False

        if time.monotonic() - self.last_spoken_time > window_seconds:
            return False

        if command in self.last_spoken_text and len(command) >= 18:
            return True

        command_words = {
            word for word in command.split()
            if len(word) > 2 and word not in {"dan", "yang", "ini", "itu", "saya", "anda"}
        }

        if len(command_words) < 4:
            return False

        spoken_words = set(self.last_spoken_text.split())
        overlap = len(command_words & spoken_words) / len(command_words)
        return overlap >= 0.68

    def should_process_sleep_command(self, text, route):
        command = clean_text(text)

        if not command or command in NOISE_FRAGMENTS:
            return False

        safe_sleep_actions = {
            "time",
            "world_time",
            "date",
            "weather",
            "system_status",
            "battery_status",
            "maps_route",
            "currency_rate",
            "middle_rate",
            "crypto_price",
            "capabilities",
            "translate",
            "online_search",
            "open_youtube",
            "youtube_search",
            "open_spotify",
            "spotify_search",
            "spotify_play",
            "self_update",
            "saved_location",
        }

        if route.get("type") == "command":
            return route.get("action") in safe_sleep_actions

        if route.get("type") in ("exit", "stop", "confirm", "confirm_yes", "confirm_no"):
            return True

        direct_markers = [
            "jam berapa",
            "pukul berapa",
            "cuaca",
            "ke kantor",
            "berapa lama",
            "berapa jam",
            "status sistem",
            "status laptop",
            "kurs",
            "harga bitcoin",
            "spotify",
            "youtube",
            "cari tahu",
            "siapa itu",
            "apa itu",
        ]
        return any(marker in command for marker in direct_markers)

    def is_confirmation_no(self, text):
        command = clean_text(text)
        no_markers = [
            "tidak",
            "nggak",
            "enggak",
            "jangan",
            "batal",
            "no",
            "cancel",
            "abort",
        ]
        return any(marker in command for marker in no_markers)

    def is_confirmation_yes(self, text):
        command = clean_text(text)
        yes_markers = [
            "ya",
            "iya",
            "yeah",
            "yes",
            "yep",
            "ok",
            "okay",
            "oke",
            "boleh",
            "lanjut",
            "lanjutkan",
            "setuju",
            "benar",
            "konfirmasi",
            "do it",
            "proceed",
        ]

        action_markers = {
            "shutdown": [
                "matikan",
                "shutdown",
                "turn off",
                "off",
            ],
            "restart": [
                "restart",
                "mulai ulang",
                "reboot",
            ],
            "sleep_laptop": [
                "tidurkan",
                "sleep",
                "mode tidur",
            ],
        }

        if any(marker in command for marker in yes_markers):
            return True

        for marker in action_markers.get(self.pending_action, []):
            if marker in command:
                return True

        return False

    def emit(self, callbacks, name, value):
        if name == "status":
            if value == self.last_status:
                return

            self.last_status = value

        callback = callbacks.get(name)
        if callback:
            callback(value)

    def confirmation_message(self, action):
        if self.current_language == "id":
            messages = {
                "shutdown": "Apakah Anda yakin ingin mematikan laptop?",
                "restart": "Apakah Anda yakin ingin restart laptop?",
                "sleep_laptop": "Apakah Anda yakin ingin membuat laptop masuk mode sleep?",
            }
        else:
            messages = {
                "shutdown": "Are you sure you want to shut down the laptop, Sir?",
                "restart": "Are you sure you want to restart the laptop, Sir?",
                "sleep_laptop": "Are you sure you want to put the laptop to sleep, Sir?",
            }

        return messages.get(action, "Please confirm, Sir.")

    def handle_route(self, route, callbacks):
        route_type = route["type"]

        if self.pending_route_destination:
            message = route.get("message", "")
            area = self.command_engine.extract_route_area_answer(message)

            if area == "__cancel__":
                self.pending_route_destination = None
                if self.pending_route_language == "id":
                    return "Baik, rute dibatalkan.", False

                return "Okay, route cancelled.", False

            if area:
                destination = self.pending_route_destination
                language = self.pending_route_language or self.current_language
                self.pending_route_destination = None
                command_text = self.command_engine.build_route_with_area_command(
                    destination,
                    area
                )
                self.emit(callbacks, "status", "THINKING")
                return self.command_engine.open_saved_maps_route(
                    language,
                    command_text
                ), False

            if route_type == "chat":
                if self.looks_like_route_area_followup(message):
                    return self.command_engine.route_area_question(
                        self.pending_route_destination,
                        self.pending_route_language or self.current_language
                    ), False
                self.pending_route_destination = None

            self.pending_route_destination = None

        if self.pending_middle_rate_command:
            message = route.get("message", "")
            source = self.detect_middle_rate_source(message)

            if source:
                command_text = self.pending_middle_rate_command
                language = self.pending_middle_rate_language
                self.pending_middle_rate_command = None
                return self.command_engine.get_middle_rate(
                    language,
                    command_text,
                    source=source
                ), False

            if self.is_confirmation_no(message):
                self.pending_middle_rate_command = None
                if self.pending_middle_rate_language == "id":
                    return "Baik, dibatalkan.", False

                return "Okay, cancelled.", False

            if self.pending_middle_rate_language == "id":
                return "Saya masih menunggu sumber kurs tengahnya. Jawab cukup: BI, atau Kurs Dollar.", False

            return "I am still waiting for the middle rate source. Just say BI, or Kurs Dollar.", False

        if self.pending_action:
            message = route.get("message", "")

            if route_type == "confirm_no" or self.is_confirmation_no(message):
                self.pending_action = None
                if self.pending_language == "id":
                    return "Dibatalkan.", False

                return "Cancelled, Sir.", False

            if route_type == "confirm_yes" or self.is_confirmation_yes(message):
                answer = self.command_engine.execute_action(
                    self.pending_action,
                    self.pending_language,
                    message
                )
                self.pending_action = None
                return answer, True

            if self.pending_language == "id":
                return "Saya belum menangkap konfirmasinya. Ucapkan ya matikan, atau batal.", False

            return "I did not catch the confirmation. Please say yes, do it, or cancel.", False

        if route_type == "exit":
            if self.current_language == "id":
                return "Baik, sampai jumpa.", True

            return "Goodbye, Sir.", True

        if route_type == "stop":
            self.sleeping = True
            if self.current_language == "id":
                return "Mode mendengarkan dijeda.", False

            return "Standing by.", False

        if route_type == "confirm":
            self.pending_action = route["action"]
            self.pending_language = self.current_language
            return self.confirmation_message(route["action"]), False

        if (
            route_type == "command" and
            route.get("action") == "translate"
        ):
            return self.translate_text(route.get("message", "")), False

        if (
            route_type == "command" and
            route.get("action") == "online_search"
        ):
            return self.answer_with_online_search(
                route.get("message", ""),
                self.current_language
            ), False

        if (
            route_type == "command" and
            route.get("action") == "middle_rate"
        ):
            self.pending_middle_rate_command = route.get("message", "")
            self.pending_middle_rate_language = self.current_language
            self.remember_middle_rate_task(
                self.pending_middle_rate_command,
                self.pending_middle_rate_language
            )

            if self.current_language == "id":
                return "Data kurs tengah mana yang ingin digunakan? Jawab cukup: BI, atau Kurs Dollar.", False

            return "Which middle rate source would you like to use? Just say BI, or Kurs Dollar.", False

        if (
            route_type == "command" and
            route.get("action") == "maps_route"
        ):
            message = route.get("message", "")
            destination_alias = self.command_engine.extract_route_destination_alias(message)
            destination = ""

            if not destination_alias:
                destination = self.command_engine.extract_free_route_destination(message)

            if (
                destination and
                self.command_engine.route_destination_needs_area(destination)
            ):
                self.pending_route_destination = destination
                self.pending_route_language = self.current_language
                return self.command_engine.route_area_question(
                    destination,
                    self.current_language
                ), False

            self.emit(callbacks, "status", "THINKING")

        if (
            route_type == "command" and
            route.get("action") == "self_update"
        ):
            update_language = detect_language(route.get("message", ""))
            return self.command_engine.execute_action(
                "self_update",
                update_language,
                route.get("message", "")
            ), True

        if route_type == "command":
            return self.command_engine.execute_action(
                route["action"],
                self.current_language,
                route.get("message", "")
            ), False

        plugin_answer = self.command_engine.execute(self.router.clean(route["message"]))
        if plugin_answer != "Command not recognized.":
            return plugin_answer, False

        self.emit(callbacks, "status", "THINKING")
        return self.brain.ask(route["message"], self.current_language), False

    def detect_middle_rate_source(self, text):
        command = clean_text(text)
        kursdollar_markers = [
            "kursdollar",
            "kurs dollar",
            "kursdollar org",
            "kurs dollar org",
            "website kurs dollar",
            "kurs dolar",
            "dollar",
            "dolar",
            "tolar",
            "stolar",
            "shtolar",
            "ushtolar",
            "purstolar",
            "org",
        ]
        bi_markers = [
            "bi",
            "bank indonesia",
            "kurs tengah bi",
            "data bi",
            "bank",
            "indonesia",
            "be eye",
            "b i",
        ]

        if any(marker in command for marker in kursdollar_markers):
            return "kursdollar"

        if any(marker in command for marker in bi_markers):
            return "bi"

        return ""

    def is_new_task_while_pending_middle_rate(self, route, text):
        if not self.pending_middle_rate_command:
            return False

        if self.detect_middle_rate_source(text):
            return False

        if self.is_confirmation_no(text):
            return False

        if route["type"] in ("exit", "stop", "confirm"):
            return True

        if route["type"] == "command":
            return route.get("action") != "middle_rate"

        command = clean_text(text)
        new_task_markers = [
            "buka",
            "bukakan",
            "open",
            "cari",
            "carikan",
            "search",
            "youtube",
            "cuaca",
            "weather",
            "status",
            "sistem",
            "system",
            "laptop",
            "jam",
            "tanggal",
            "translate",
            "terjemahkan",
            "bahasa inggris",
            "bahasa indonesia",
            "apa arti",
            "kurs ",
            "harga",
            "bitcoin",
            "crypto",
            "berita",
            "info terbaru",
        ]

        return any(marker in command for marker in new_task_markers)

    def remember_middle_rate_task(self, command_text, language):
        self.last_middle_rate_command = command_text
        self.last_middle_rate_language = language
        self.last_middle_rate_time = time.monotonic()

    def recall_middle_rate_task(self, max_age=120):
        if not self.last_middle_rate_command:
            return None, None

        if time.monotonic() - self.last_middle_rate_time > max_age:
            return None, None

        return self.last_middle_rate_command, self.last_middle_rate_language

    def answer_with_online_search(self, query, language="id"):
        query = self.prepare_online_search_query(query)
        command = clean_text(query)
        is_price_query = any(marker in command for marker in [
            "berapa harga",
            "harga berapa",
            "cek harga",
            "cari harga",
            "carikan harga",
            "harga terbaru",
            "harga sekarang",
            "price of",
            "how much is",
            "what is the price",
        ])
        search_data = self.online_tools.search(query, language)

        if not search_data.get("ok"):
            error = search_data.get("error", "")
            if language == "id":
                return f"Saya belum bisa mencari online. {error}"

            return f"I could not search online. {error}"

        context = self.online_tools.format_context(search_data)

        if not context:
            if language == "id":
                return "Saya belum menemukan hasil online yang cukup jelas."

            return "I could not find clear online results."

        direct_answer = (search_data.get("answer") or "").strip()

        if direct_answer and language != "id":
            return f"From an online search: {direct_answer}"

        if language == "id":
            price_instruction = ""

            if is_price_query:
                price_instruction = (
                    "Jika pertanyaan meminta harga produk, kendaraan, atau barang, "
                    "berikan harga atau kisaran indikatif yang muncul dari hasil online. "
                    "Sebutkan jika harga bisa berbeda tergantung varian, tahun, lokasi, promo, "
                    "atau dealer. Jangan menjawab bahwa Anda tidak punya akses internet jika "
                    "hasil online di bawah tersedia. "
                )

            prompt = (
                "Jawab pertanyaan user berdasarkan hasil pencarian online berikut. "
                "Jawab hanya dalam bahasa Indonesia. "
                "Jawab singkat, natural, dan sebutkan kalau datanya berasal dari pencarian online. "
                "Jangan mengarang di luar konteks. "
                f"{price_instruction}\n\n"
                f"Pertanyaan: {query}\n\n"
                f"Hasil online:\n{context}"
            )
        else:
            prompt = (
                "Answer the user based on the online search results below. "
                "Keep it brief, natural, and mention that it comes from an online search. "
                "Do not invent details outside the context.\n\n"
                f"Question: {query}\n\n"
                f"Online results:\n{context}"
            )

        answer = self.brain.ask(prompt, language)
        refusal_markers = [
            "tidak memiliki akses internet",
            "tidak punya akses internet",
            "tidak dapat mengakses internet",
            "tidak bisa mengakses internet",
            "do not have internet access",
            "don't have internet access",
            "cannot access the internet",
        ]

        if any(marker in answer.lower() for marker in refusal_markers):
            if direct_answer:
                if language == "id":
                    return f"Dari pencarian online: {direct_answer}"

                return f"From an online search: {direct_answer}"

            first_result = (search_data.get("results") or [{}])[0]
            snippet = (first_result.get("content") or "").strip()
            title = (first_result.get("title") or "").strip()

            if snippet:
                if language == "id":
                    return f"Dari pencarian online: {snippet}"

                return f"From an online search: {snippet}"

            if title:
                if language == "id":
                    return f"Saya menemukan hasil online tentang {title}, tetapi ringkasannya belum cukup jelas."

                return f"I found an online result about {title}, but the summary was not clear enough."

        return answer

    def extract_quoted_text(self, text):
        match = re.search(r'"([^"]+)"', text)

        if match:
            return match.group(1).strip()

        match = re.search(r"'([^']+)'", text)

        if match:
            return match.group(1).strip()

        return ""

    def extract_translation_request(self, text):
        command = text.strip()
        lowered = command.lower()
        target_language = "English"

        if (
            re.search(r"bahasa\s+indonesia\s*(?:nya)?", lowered) or
            re.search(r"bahasa\s+indonesian\s*(?:nya)?", lowered) or
            "to indonesian" in lowered or
            "to bahasa indonesia" in lowered or
            "apa arti" in lowered or
            "artinya" in lowered
        ):
            target_language = "Indonesian"

        quoted = self.extract_quoted_text(command)

        if quoted:
            return target_language, quoted

        language_request = re.search(
            r"^(?:nova\s+)?(?:apa|apakah|tolong|coba|please)?\s*"
            r"(?:bahasa|ke\s+bahasa)\s+"
            r"(?:inggris|english|indonesia|indonesian)\s*(?:nya)?"
            r"(?:\s+(?:dari|untuk|kalimat|sentence|of|for))?"
            r"\s*[,.:;?-]*\s*(.+)$",
            command,
            flags=re.IGNORECASE,
        )

        if language_request:
            content = language_request.group(1).strip(" .?!,:;\"'")
            return target_language, content

        translate_request = re.search(
            r"^(?:nova\s+)?(?:tolong|coba|please)?\s*"
            r"(?:terjemahkan|translate)"
            r"(?:\s+(?:ini|kalimat ini|this|this sentence))?"
            r"(?:\s+(?:ke|to)\s+(?:bahasa\s+)?(?:inggris|english|indonesia|indonesian))?"
            r"\s*[,.:;?-]*\s*(.+)$",
            command,
            flags=re.IGNORECASE,
        )

        if translate_request:
            content = translate_request.group(1).strip(" .?!,:;\"'")
            return target_language, content

        meaning_request = re.search(
            r"^(?:nova\s+)?(?:apa\s+arti(?:nya)?|artinya|what\s+does)\s*"
            r"(?:dari|of|mean)?\s*[,.:;?-]*\s*(.+)$",
            command,
            flags=re.IGNORECASE,
        )

        if meaning_request:
            content = meaning_request.group(1).strip(" .?!,:;\"'")
            return target_language, content

        markers = [
            "apa bahasa inggrisnya",
            "apa bahasa indonesianya",
            "apa bahasa inggris nya",
            "apa bahasa indonesia nya",
            "apa bahasa englishnya",
            "apa bahasa english nya",
            "apa bahasa indonesianya",
            "apa bahasa indonesian nya",
            "apakah bahasa inggrisnya",
            "apakah bahasa inggris nya",
            "apakah bahasa indonesianya",
            "apakah bahasa indonesia nya",
            "bahasa inggrisnya",
            "bahasa indonesianya",
            "bahasa inggris nya",
            "bahasa indonesia nya",
            "bahasa englishnya",
            "bahasa english nya",
            "bahasa indonesian nya",
            "terjemahkan ke bahasa inggris",
            "terjemahkan ke bahasa indonesia",
            "terjemahkan",
            "translate to english",
            "translate to indonesian",
            "translate",
            "how do you say",
            "apa arti dari",
            "apa arti",
            "artinya",
        ]

        content = lowered

        for marker in markers:
            if marker in content:
                content = command[lowered.find(marker) + len(marker):]
                break

        content = content.strip(" .?!,:;\"'")

        return target_language, content

    def ensure_sentence_pause(self, text):
        text = str(text or "").strip()

        if not text:
            return ""

        if text[-1] not in ".?!":
            return f"{text}."

        return text

    def normalize_translation_answer(self, answer):
        answer = str(answer or "").strip()

        if not answer:
            return answer

        match = re.match(
            r"(?is)^\s*(Translation|Terjemahan)\s*:\s*(.*?)(?:\s+Natural\s*:\s*(.*))?\s*$",
            answer,
        )

        if match:
            label = match.group(1)
            translation = self.ensure_sentence_pause(match.group(2))
            natural = self.ensure_sentence_pause(match.group(3))

            if natural:
                return f"{label}: {translation}\nNatural: {natural}"

            return f"{label}: {translation}"

        return re.sub(
            r"(?<![.!?])\s+(Natural\s*:)",
            r".\n\1",
            answer,
            flags=re.IGNORECASE,
        )

    def translate_text(self, text):
        target_language, source_text = self.extract_translation_request(text)

        if not source_text:
            if target_language == "English":
                return "Kalimat apa yang mau diterjemahkan ke bahasa Inggris?"

            return "Kalimat apa yang mau diterjemahkan ke bahasa Indonesia?"

        self.forced_speech_language = "en" if target_language == "English" else "id"

        if target_language == "English":
            format_hint = (
                "Translation: <best translation>\n"
                "Natural: <more natural everyday English version if useful>\n"
            )
            answer_language = "en"
        else:
            format_hint = (
                "Terjemahan: <terjemahan terbaik>\n"
                "Natural: <versi bahasa Indonesia sehari-hari jika berguna>\n"
            )
            answer_language = "id"

        prompt = (
            f"Translate this text to {target_language}. "
            "Return only a concise answer in this format:\n"
            f"{format_hint}"
            "Translate only the text after 'Text:'. "
            "Do not translate the user's instruction. "
            "Do not answer conversationally. "
            "Do not add names, Sir, Alfred, offers, or follow-up questions. "
            "Do not explain grammar unless asked.\n\n"
            f"Text: {source_text}"
        )

        answer = self.brain.ask(prompt, answer_language)
        return self.normalize_translation_answer(answer)

    def listen_for_text(
        self,
        callbacks,
        status="LISTENING",
        emit_heard=True,
        listen_options=None,
    ):
        self.wait_until_listening_allowed()
        self.emit(callbacks, "status", status)
        listen_options = listen_options or {}
        text = self.listener.listen(**listen_options)

        if text and (self.is_speaking or time.monotonic() < self.listen_mute_until):
            print(f"[Listen Guard] Ignored while speaking/muted: {text}")
            return ""

        if text and self.is_echo_transcript(text):
            print(f"[Echo Guard] Ignored transcript: {text}")
            return ""

        if text and emit_heard:
            self.emit(callbacks, "heard", text)

        return text

    def prepare_response_text(self, response):
        if isinstance(response, dict):
            display_text = response.get("display") or response.get("text") or response.get("speech") or ""
            speech_text = response.get("speech") or display_text
            language = response.get("language")

            if language not in ("id", "en"):
                language = None

            return (
                clean_answer_text(display_text),
                clean_answer_text(speech_text),
                language,
            )

        text = clean_answer_text(response)
        return text, text, None

    def speak_with_barge_in(
        self,
        text,
        language,
        callbacks,
        stream_text=False,
        display_text=None,
    ):
        stop_event = threading.Event()
        interrupt_event = threading.Event()
        typer = None
        monitor = None
        previous_mute_until = self.listen_mute_until

        self.emit(callbacks, "status", "SPEAKING")
        self.is_speaking = True
        # While NOVA is speaking, normal listening must stay muted. Barge-in
        # uses its own guarded monitor below, so the main listener cannot hear
        # NOVA's speaker output and route it as a new command.
        self.listen_mute_until = max(self.listen_mute_until, time.monotonic() + 3600.0)

        def monitor_voice():
            try:
                if self.listener.wait_for_barge_in(
                    stop_event,
                    min_delay=0.9,
                    min_voice_duration=0.65,
                    threshold_multiplier=6.0,
                    absolute_threshold=0.08,
                ):
                    interrupt_event.set()
            except Exception as error:
                print(f"[Barge-in Error] {error}")

        # Keep a lightweight voice monitor alive while NOVA speaks so the user
        # can cut off long answers. Speaker verification will make this sharper
        # later, but disabling it makes the assistant feel stuck.
        if self.enable_barge_in:
            monitor = threading.Thread(target=monitor_voice, daemon=True)
            monitor.start()

        if stream_text:
            self.emit(callbacks, "answer_start", "")
            if display_text is not None and display_text != text:
                self.emit(callbacks, "answer_delta", display_text)
            else:
                typer = threading.Thread(
                    target=self.emit_typewriter_text,
                    args=(text, callbacks, interrupt_event),
                    daemon=True
                )
                typer.start()

        try:
            completed = self.speaker.speak(
                text,
                language=language,
                interrupt_event=interrupt_event
            )
        finally:
            self.is_speaking = False
            self.listen_mute_until = max(
                previous_mute_until,
                time.monotonic() + self.post_speech_mute_seconds(text)
            )

        stop_event.set()
        if monitor is not None:
            monitor.join(timeout=0.2)

        if not completed:
            interrupt_event.set()

        if typer is not None:
            typer.join(timeout=4.0)

        if not completed or interrupt_event.is_set():
            self.remember_spoken_text(text)
            self.mute_listening(0.35)
            return False

        self.remember_spoken_text(text)
        self.mute_listening(self.post_speech_mute_seconds(text))
        return True

    def split_ready_speech_chunk(self, text, min_chars=160, max_chars=330):
        if len(text) < min_chars:
            return None, text

        boundary = None

        for match in re.finditer(r"(?<=[.!?])\s+", text):
            if match.end() >= min_chars:
                boundary = match
                break

        if boundary is None:
            for match in re.finditer(r"(?<=[,;:])\s+", text):
                if match.end() >= min_chars:
                    boundary = match
                    break

        if boundary is None and len(text) >= max_chars:
            cut = text.rfind(" ", 0, max_chars)
            if cut > 0:
                return text[:cut].strip(), text[cut:].strip()

            return text[:max_chars].strip(), text[max_chars:].strip()

        if boundary is None:
            return None, text

        chunk = text[:boundary.end()].strip()
        rest = text[boundary.end():]
        return chunk, rest

    def emit_typewriter_text(self, text, callbacks, interrupt_event):
        words = text.split()

        for index, word in enumerate(words):
            if interrupt_event.is_set() or not self.running:
                break

            suffix = " " if index < len(words) - 1 else "\n"
            self.emit(callbacks, "answer_delta", word + suffix)
            time.sleep(0.024)

    def stream_chat_response(self, prompt, language, callbacks):
        self.emit(callbacks, "status", "THINKING")

        answer = ""

        try:
            for chunk in self.brain.ask_stream(prompt, language):
                if not self.running:
                    break

                answer += chunk
        except Exception as error:
            answer = f"Maaf, saya mengalami masalah saat memproses jawaban. {error}"

        answer = clean_answer_text(answer.strip())
        if not answer:
            answer = "Maaf, saya belum mendapatkan jawaban."

        completed = self.speak_with_barge_in(
            answer,
            language,
            callbacks,
            stream_text=True
        )
        return answer, completed

    def run(self, callbacks=None, announce=True):
        callbacks = callbacks or {}
        self.running = True

        if announce:
            ready_message = self.build_ready_greeting()
            self.emit(callbacks, "answer", ready_message)
            self.speak_with_barge_in(ready_message, "id", callbacks)

        self.open_startup_window()

        while self.running:
            route = None

            if self.sleeping:
                text = self.listen_for_text(
                    callbacks,
                    status="SLEEPING",
                    emit_heard=False,
                    listen_options={
                        "max_duration": 11,
                        "no_speech_timeout": 3.6,
                        "silence_duration": 1.35,
                        "min_speech_duration": 0.35,
                    }
                )

                if not text:
                    continue

                woke_by_name = contains_phrase(text, WAKE_PHRASES)
                command_text = remove_wake_word(text) if woke_by_name else text

                if woke_by_name and command_text == "":
                    self.emit(callbacks, "status", "SPEAKING")
                    language = detect_language(text)
                    if language == "id":
                        answer = "Saya siap."
                        self.emit(callbacks, "answer", answer)
                        self.speak_with_barge_in(answer, "id", callbacks)
                    else:
                        answer = "Ready."
                        self.emit(callbacks, "answer", answer)
                        self.speak_with_barge_in(answer, "en", callbacks)

                    self.sleeping = False
                    continue

                route = self.router.route(command_text)
                allowed_sleep_command = (
                    woke_by_name or
                    self.should_process_sleep_command(command_text, route)
                )

                if not allowed_sleep_command:
                    continue

                if (
                    self.is_bad_transcript(command_text) and
                    not (
                        route.get("type") == "command" and
                        route.get("action") in {"self_update", "time", "weather", "maps_route"}
                    )
                ):
                    continue

                if self.is_duplicate_transcript(command_text):
                    continue

                self.sleeping = False
                text = command_text
                self.current_language = detect_language(text)
                self.emit(callbacks, "heard", text)
            else:
                text = self.listen_for_text(
                    callbacks,
                    status="LISTENING",
                    emit_heard=False,
                    listen_options={
                        "max_duration": 18,
                        "no_speech_timeout": 2.4,
                        "silence_duration": 1.45,
                        "min_speech_duration": 0.45,
                    }
                )

                if not text:
                    if not self.followup_window_active():
                        self.close_followup_window()

                    continue

                if contains_phrase(text, WAKE_PHRASES):
                    command = remove_wake_word(text)

                    if command == "":
                        language = detect_language(text)
                        answer = "Saya siap." if language == "id" else "Ready, Sir."
                        self.current_language = language
                        self.emit(callbacks, "answer", answer)
                        self.emit(callbacks, "status", "SPEAKING")
                        self.speak_with_barge_in(answer, language, callbacks)
                        self.open_startup_window()
                        continue

                    text = command

                if self.is_bad_transcript(text) or self.is_duplicate_transcript(text):
                    continue

            if route is None:
                if (
                    self.is_low_value_fragment(text) and
                    not (
                        self.followup_window_active() and
                        self.get_recent_context() and
                        self.is_followup_question(text)
                    )
                ):
                    continue

                self.emit(callbacks, "heard", text)
                self.current_language = detect_language(text)
                route = self.router.route(text)
                text, route = self.enrich_route_retry_text(text, route)
                text, route = self.enrich_weather_followup_text(text, route)
                text, route = self.enrich_followup_text(text, route)
                recalled_source = self.detect_middle_rate_source(text)

                if recalled_source and not self.pending_middle_rate_command:
                    recalled_command, recalled_language = self.recall_middle_rate_task()

                    if recalled_command:
                        self.pending_middle_rate_command = recalled_command
                        self.pending_middle_rate_language = recalled_language or self.current_language

                if (
                    self.pending_media_search and
                    route["type"] == "chat"
                ):
                    route = {
                        "type": "command",
                        "action": f"{self.pending_media_search}_search",
                        "message": text
                    }

                if (
                    route["type"] == "command" and
                    route.get("action") in ("youtube_search", "spotify_search")
                ):
                    self.pending_media_search = None
                    self.pending_youtube_search = False

            if self.is_new_task_while_pending_middle_rate(route, text):
                self.pending_middle_rate_command = None

            if (
                (self.pending_route_destination or self.route_retry_active()) and
                not self.is_pending_route_followup(route, text)
            ):
                self.clear_route_context()

            if (
                self.pending_middle_rate_command or
                self.pending_action or
                self.pending_route_destination
            ):
                pending_response_language = (
                    self.pending_middle_rate_language
                    if self.pending_middle_rate_command
                    else (
                        self.pending_route_language
                        if self.pending_route_destination
                        else self.pending_language
                    )
                )
                response, should_exit = self.handle_route(route, callbacks)
                answer, speech_answer, response_language = self.prepare_response_text(response)
                speech_language = (
                    self.forced_speech_language or
                    response_language or
                    pending_response_language or
                    self.current_language
                )
                self.forced_speech_language = None
                self.speak_with_barge_in(
                    speech_answer,
                    speech_language,
                    callbacks,
                    stream_text=True,
                    display_text=answer
                )

                if should_exit:
                    self.emit(callbacks, "quit", True)
                    break

                if route["type"] == "stop":
                    self.emit(callbacks, "status", "SLEEPING")
                    self.close_followup_window()
                else:
                    self.remember_context(route, text, answer)
                    self.open_followup_window()

                continue

            if route["type"] == "chat":
                plugin_answer = self.command_engine.execute(
                    self.router.clean(route["message"])
                )

                if plugin_answer != "Command not recognized.":
                    answer = clean_answer_text(plugin_answer)
                    should_exit = False
                    self.speak_with_barge_in(
                        answer,
                        self.current_language,
                        callbacks,
                        stream_text=True
                    )
                else:
                    answer, completed = self.stream_chat_response(
                        text,
                        self.current_language,
                        callbacks
                    )
                    should_exit = False

                if should_exit:
                    self.emit(callbacks, "quit", True)
                    break

                if route["type"] == "stop":
                    self.emit(callbacks, "status", "SLEEPING")
                    self.close_followup_window()
                else:
                    self.remember_context(route, text, answer)
                    self.open_followup_window()

                continue

            response, should_exit = self.handle_route(route, callbacks)
            answer, speech_answer, response_language = self.prepare_response_text(response)

            if (
                route["type"] == "command" and
                route.get("action") == "weather"
            ):
                self.remember_weather_context(route.get("message", text), self.current_language)

            if (
                route["type"] == "command" and
                route.get("action") == "open_youtube"
            ):
                self.pending_media_search = "youtube"
                self.pending_youtube_search = True

            if (
                route["type"] == "command" and
                route.get("action") == "open_spotify"
            ):
                self.pending_media_search = "spotify"

            speech_language = (
                self.forced_speech_language or
                response_language or
                self.current_language
            )
            self.forced_speech_language = None
            self.speak_with_barge_in(
                speech_answer,
                speech_language,
                callbacks,
                stream_text=True,
                display_text=answer
            )

            if should_exit:
                self.emit(callbacks, "quit", True)
                break

            if route["type"] == "stop":
                self.emit(callbacks, "status", "SLEEPING")
                self.close_followup_window()
            else:
                self.remember_context(route, text, answer)
                self.open_followup_window()

        self.running = False
        self.emit(callbacks, "status", "OFFLINE")
