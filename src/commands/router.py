import re


class CommandRouter:

    def __init__(self):
        self.stop_commands = [
            "stop",
            "stop listening",
            "stop voice",
            "voice off",
            "cancel",
            "cancel voice",
            "be quiet",
            "silence",
            "pause",
            "pause listening",
            "sleep",
            "go to sleep",
            "stand by",
            "standby",
            "berhenti",
            "stop dulu",
            "diam dulu",
            "jangan dengarkan",
            "tidur dulu",
            "mode tidur",
        ]

        self.exit_commands = [
            "exit",
            "quit",
            "goodbye",
            "bye nova",
            "turn off nova",
            "keluar",
            "tutup nova",
            "matikan nova",
            "selesai",
        ]

        self.yes_commands = [
            "yes",
            "yes sir",
            "yeah",
            "yep",
            "ok",
            "okay",
            "confirm",
            "confirmed",
            "do it",
            "proceed",
            "ya",
            "iya",
            "iya benar",
            "oke",
            "oke lanjut",
            "oke matikan",
            "boleh",
            "lanjut",
            "lanjutkan",
            "konfirmasi",
            "setuju",
            "benar",
        ]

        self.no_commands = [
            "no",
            "cancel",
            "never mind",
            "abort",
            "tidak",
            "nggak",
            "enggak",
            "batal",
            "jangan",
        ]

    def clean(self, text):
        text = text.lower()

        for char in [",", ".", "!", "?", ";", ":"]:
            text = text.replace(char, "")

        corrections = {
            "kegeran indonesia": "ke grand indonesia",
            "kegeren indonesia": "ke grand indonesia",
            "ke geran indonesia": "ke grand indonesia",
            "ke geren indonesia": "ke grand indonesia",
            "geran indonesia": "grand indonesia",
            "geren indonesia": "grand indonesia",
            "grand indonesa": "grand indonesia",
            "grand indonesia": "grand indonesia",
            "jakatah barat": "jakarta barat",
            "utera jakarta barat": "mall ciputra jakarta barat",
            "utara jakarta barat": "mall ciputra jakarta barat",
            "utera jakarta": "mall ciputra jakarta",
            "mall utera": "mall ciputra",
            "mall citra": "mall ciputra",
            "citra jakarta barat": "mall ciputra jakarta barat",
            "ciputra jakarta barat": "mall ciputra jakarta barat",
            "ciputra mall": "mall ciputra",
            "mall putra jakarta barat": "mall ciputra jakarta barat",
            "mall putra jakarta": "mall ciputra jakarta",
            "mall putra": "mall ciputra",
            "kebun raya bulur": "kebun raya bogor",
            "kebun raya bukur": "kebun raya bogor",
            "kebun raya bokur": "kebun raya bogor",
            "kebun raya bokor": "kebun raya bogor",
            "kebun raya tukur": "kebun raya bogor",
            "kebun raya tuker": "kebun raya bogor",
            "mall tamat anggrek": "mall taman anggrek",
            "tamat anggrek": "taman anggrek",
            "kuri mall": "puri mall",
            "curi mall": "puri mall",
            "puri mol": "puri mall",
            "puri moll": "puri mall",
            "lipo mall": "lippo mall",
            "lipo mall puri": "lippo mall puri",
            "lipomall puri": "lippo mall puri",
            "ais bsd": "ice bsd",
            "ice bsd": "ice bsd",
            "is bsd": "ice bsd",
            "i c e bsd": "ice bsd",
        }

        text = " ".join(text.split())

        for source, replacement in corrections.items():
            text = re.sub(
                rf"(?<!\w){re.escape(source)}(?!\w)",
                replacement,
                text,
                flags=re.IGNORECASE,
            )

        text = re.sub(r"\bmall\s+mall\s+", "mall ", text, flags=re.IGNORECASE)
        return " ".join(text.split())

    def is_stop_command(self, command):
        if any(marker in command for marker in ["laptop", "komputer", "computer"]):
            return False

        translation_context_markers = [
            "bahasa indonesia",
            "bahasa inggris",
            "bahasa english",
            "to indonesian",
            "to english",
            "translate",
            "terjemah",
            "terjemahkan",
            "artinya",
            "apa arti",
            "what is the indonesian",
            "what is the english",
            "how do you say",
        ]
        if any(marker in command for marker in translation_context_markers):
            return False

        if any(word in {"sleepy", "sleeping", "asleep"} for word in command.split()):
            return False

        direct_commands = {
            "stop",
            "stop dulu",
            "stop listening",
            "stop voice",
            "voice off",
            "cancel voice",
            "be quiet",
            "silence",
            "pause",
            "pause listening",
            "sleep",
            "go to sleep",
            "stand by",
            "standby",
            "berhenti",
            "diam dulu",
            "jangan dengarkan",
            "tidur",
            "tidur dulu",
            "mode tidur",
        }

        if command in direct_commands:
            return True

        phrase_commands = [
            "go to sleep",
            "stop listening",
            "stop voice",
            "pause listening",
            "voice off",
            "be quiet",
            "diam dulu",
            "jangan dengarkan",
            "tidur dulu",
            "mode tidur",
            "berhenti mendengarkan",
        ]

        return any(
            re.search(rf"(?<!\w){re.escape(phrase)}(?!\w)", command)
            for phrase in phrase_commands
        )

    def is_capabilities_command(self, command):
        exact_phrases = {
            "what can you do",
            "what can you do for me",
            "what are your abilities",
            "show your abilities",
            "list your abilities",
            "apa yang bisa kamu lakukan",
            "apa saja yang bisa kamu lakukan",
            "apa yang bisa nova lakukan",
            "apa saja yang bisa nova lakukan",
            "kamu bisa apa",
            "nova bisa apa",
            "apa kemampuan kamu",
            "apa saja kemampuan kamu",
            "apa kemampuan nova",
            "sebutkan kemampuan kamu",
            "sebutkan kemampuan nova",
            "fitur kamu apa",
            "fitur nova apa",
        }

        if command in exact_phrases:
            return True

        capability_blockers = [
            "menyebabkan",
            "penyebab",
            "gejala",
            "penyakit",
            "masuk angin",
            "kolesterol",
            "asam urat",
            "darah tinggi",
            "harga",
            "kurs",
            "cuaca",
            "jam",
            "rute",
            "berapa lama",
            "berapa jam",
            "siapa",
            "apa itu",
            "jelaskan",
            "menurut",
            "bahasa",
            "translate",
            "terjemah",
            "spotify",
            "youtube",
            "lagu",
            "video",
            "maps",
            "google maps",
            "status",
        ]
        if any(marker in command for marker in capability_blockers):
            return False

        patterns = [
            r"\bwhat\s+can\s+(you|nova)\s+do(\s+for\s+me)?\b",
            r"\bwhat\s+are\s+(your|nova'?s)\s+abilities\b",
            r"\b(apa|apakah)\s+(saja\s+)?(yang\s+)?bisa\s+(kamu|nova)\s+(lakukan|kerjakan)\b",
            r"\b(kamu|nova)\s+bisa\s+apa\b",
            r"\b(apa|apakah)\s+(saja\s+)?kemampuan\s+(kamu|nova)\b",
            r"\bsebutkan\s+kemampuan\s+(kamu|nova)\b",
            r"\bfitur\s+(kamu|nova)\s+apa\b",
        ]

        return any(re.search(pattern, command) for pattern in patterns)

    def route(self, text):
        command = self.clean(text)
        office_markers = [
            "kantor",
            "kekantor",
            "ke kantor",
            "lantor",
            "kantoor",
            "cantor",
            "office",
            "tempat kerja",
            "work",
        ]
        home_markers = ["rumah", "home", "pulang"]
        saved_place_markers = office_markers + home_markers

        if any(item == command for item in self.yes_commands):
            return {
                "type": "confirm_yes",
                "message": text
            }

        if any(item == command for item in self.no_commands):
            return {
                "type": "confirm_no",
                "message": "Dibatalkan, Sir."
            }

        if any(item in command for item in self.exit_commands):
            return {
                "type": "exit",
                "message": "Baik, sampai jumpa, Sir."
            }

        if (
            "update yourself" in command or
            "update your self" in command or
            "update your software" in command or
            "update your software mode" in command or
            "update your chest" in command or
            "update your chess" in command or
            "update your test" in command or
            "please update yourself" in command or
            "restart yourself" in command or
            "restart nova" in command or
            "reload nova" in command or
            "update software" in command or
            "update software mode" in command or
            "update software mu" in command or
            "nova update software mu" in command or
            "nota update software" in command or
            "anova update software" in command or
            "nofa update software" in command or
            "update softwareku" in command or
            "update software saya" in command or
            "update softwarenu" in command or
            "perbarui nova" in command or
            "perbarui software" in command or
            "muat ulang nova" in command or
            "restart aplikasi nova" in command
        ):
            return {
                "type": "command",
                "action": "self_update",
                "message": text
            }

        if (
            "bahasa inggris" in command or
            "bahasa english" in command or
            "in english" in command or
            "to english" in command or
            "translate" in command or
            "terjemahkan" in command or
            "artinya" in command or
            "apa arti" in command or
            "bahasa indonesia" in command or
            "to indonesian" in command
        ):
            translation_markers = [
                "apa bahasa",
                "apakah bahasa",
                "bahasa inggrisnya",
                "bahasa inggris nya",
                "bahasa englishnya",
                "bahasa english nya",
                "bahasa indonesianya",
                "bahasa indonesia nya",
                "bahasa indonesian nya",
                "terjemahkan",
                "translate",
                "apa arti",
                "artinya",
                "how do you say",
                "what is",
            ]

            if (
                any(marker in command for marker in translation_markers) or
                re.search(
                    r"(?:apa|apakah)?\s*bahasa\s+"
                    r"(?:inggris|english|indonesia|indonesian)\s*(?:nya)?",
                    command
                )
            ):
                return {
                    "type": "command",
                    "action": "translate",
                    "message": text
                }

        if self.is_stop_command(command):
            return {
                "type": "stop",
                "message": "Mode mendengarkan dijeda."
            }

        if self.is_capabilities_command(command):
            return {
                "type": "command",
                "action": "capabilities",
                "message": text
            }

        if (
            ("status" in command and ("sistem" in command or "system" in command or "laptop" in command)) or
            ("cek" in command and ("sistem" in command or "system" in command or "laptop" in command)) or
            "spesifikasi laptop" in command or
            "spek laptop" in command or
            "laptop specs" in command
        ):
            return {
                "type": "command",
                "action": "system_status",
                "message": text
            }

        if (
            (
                "simpan lokasi" in command or
                "save location" in command or
                "set home" in command or
                "set office" in command
            ) and
            any(marker in command for marker in saved_place_markers)
        ):
            return {
                "type": "command",
                "action": "save_location",
                "message": text
            }

        if (
            (
                "dimana" in command or
                "di mana" in command or
                "lokasi" in command or
                "alamat" in command or
                "koordinat" in command or
                "coordinate" in command
            ) and
            any(marker in command for marker in saved_place_markers)
        ):
            return {
                "type": "command",
                "action": "saved_location",
                "message": text
            }

        route_intent_markers = [
            "mau ke",
            "mau kegeran",
            "mau kegeren",
            "ingin ke",
            "pengen ke",
            "mau pergi ke",
            "ingin pergi ke",
            "pergi ke",
            "berangkat ke",
            "arah ke",
            "rute ke",
            "berapa lama ke",
            "berapa jam ke",
            "berapa waktu ke",
            "waktu tempuh ke",
            "cek berapa lama",
            "cek berapa jam",
            "cek waktu tempuh",
            "cari tahu berapa lama",
            "cari tahu berapa jam",
            "open route to",
            "directions to",
            "go to",
        ]
        route_time_markers = [
            "berapa jam",
            "berapa lama",
            "berapa waktu",
            "butuh berapa jam",
            "butuh berapa lama",
            "perlu berapa jam",
            "perlu berapa lama",
            "waktu yang perlu",
            "waktu yang saya perlu",
            "waktu yang saya perlukan",
            "waktu yang saya butuhkan",
            "waktu yang perlu saya perlukan",
            "berapa waktu yang saya perlukan",
            "berapa waktu yang saya butuhkan",
            "cek berapa",
            "estimasi",
            "waktu tempuh",
        ]
        route_place_markers = [
            "mall",
            "ciputra",
            "grand indonesia",
            "ice bsd",
            "bsd",
            "puri",
            "lippo",
            "taman anggrek",
            "kebun raya",
            "jakarta barat",
            "jakarta pusat",
            "jakarta selatan",
            "jakarta utara",
            "jakarta timur",
            "bogor",
            "sentul",
            "tangerang",
            "serpong",
            "cengkareng",
            "citra",
        ]

        route_blockers = [
            "apa penyebab",
            "penyebab",
            "gejala",
            "penyakit",
            "kolesterol",
            "asam urat",
            "darah tinggi",
            "masuk angin",
            "bahasa inggris",
            "bahasa indonesia",
            "translate",
            "terjemah",
            "spotify",
            "youtube",
            "lagu",
            "video",
            "harga",
            "kurs",
            "bitcoin",
            "dollar",
            "dolar",
            "euro",
            "apa itu",
            "siapa",
            "jelaskan",
            "menurut kamu",
        ]
        has_route_intent = any(marker in command for marker in route_intent_markers)
        has_route_time = any(marker in command for marker in route_time_markers)
        has_saved_place = any(marker in command for marker in saved_place_markers)
        has_office = any(marker in command for marker in office_markers)
        has_route_place = any(marker in command for marker in route_place_markers)
        has_route_blocker = any(marker in command for marker in route_blockers)

        product_price_markers = [
            "berapa harga",
            "harga",
            "price",
            "berapa kisaran harga",
            "kisaran harga",
            "harga jual",
        ]
        financial_price_markers = [
            "kurs",
            "dollar",
            "dolar",
            "usd",
            "euro",
            "bitcoin",
            "btc",
            "idr",
            "rupiah",
        ]
        if (
            any(marker in command for marker in product_price_markers) and
            not any(marker in command for marker in financial_price_markers)
        ):
            return {
                "type": "command",
                "action": "online_search",
                "message": text
            }

        if not has_route_blocker and (
            (has_route_intent and has_saved_place) or
            (has_office and has_route_time) or
            (has_route_intent and has_route_time) or
            (re.search(r"(^|\s)ke\s+[\w\s]+", command) and has_route_time) or
            (has_route_place and has_route_time)
        ):
            return {
                "type": "command",
                "action": "maps_route",
                "message": text
            }

        if (
            "presiden amerika" in command or
            "president amerika" in command or
            "presiden us" in command or
            "presiden usa" in command or
            "us president" in command or
            "president of america" in command or
            "president of the united states" in command
        ):
            return {
                "type": "command",
                "action": "us_president",
                "message": text
            }

        time_locations = [
            "cina",
            "china",
            "beijing",
            "shanghai",
            "hong kong",
            "jepang",
            "japan",
            "tokyo",
            "korea",
            "seoul",
            "singapura",
            "singapore",
            "malaysia",
            "kuala lumpur",
            "bangkok",
            "thailand",
            "india",
            "dubai",
            "london",
            "inggris",
            "uk",
            "paris",
            "prancis",
            "new york",
            "amerika",
            "los angeles",
            "sydney",
            "australia",
        ]
        time_words = ["jam", "pukul", "time", "waktu"]

        if (
            any(word in command for word in time_words) and
            any(
                re.search(rf"(?<!\w){re.escape(location)}(?!\w)", command)
                for location in time_locations
            )
        ):
            return {
                "type": "command",
                "action": "world_time",
                "message": text
            }

        online_markers = [
            "cari tahu",
            "caritahu",
            "coba cari tahu",
            "coba kamu cari tahu",
            "tolong cari tahu",
            "telusuri",
            "riset",
            "research",
            "lookup",
            "look up",
            "cari online",
            "search online",
            "cari di internet",
            "cek internet",
            "cek online",
            "berita terbaru",
            "info terbaru",
            "update terbaru",
            "terkini",
            "terbaru",
            "real time",
            "realtime",
            "saat ini",
            "sekarang",
            "hari ini",
        ]

        if any(marker in command for marker in online_markers):
            weather_words = [
                "cuaca",
                "weather",
                "gerimis",
                "hujan",
                "cerah",
                "mendung",
                "berawan",
                "suhu",
                "kelembapan",
            ]
            local_time_words = ["jam", "pukul", "time"]
            crypto_words = [
                "bitcoin",
                "btc",
                "ethereum",
                "etherium",
                "eth",
                "crypto",
                "kripto",
            ]
            currency_words = [
                "kurs",
                "exchange rate",
                "dollar",
                "dolar",
                "usd",
                "euro",
                "eur",
                "yen",
                "jpy",
                "pound",
                "gbp",
                "rupiah",
                "idr",
            ]

            if any(word in command for word in weather_words):
                return {
                    "type": "command",
                    "action": "weather",
                    "message": text
                }

            if not any(word in command for word in weather_words + local_time_words + currency_words + crypto_words):
                return {
                    "type": "command",
                    "action": "online_search",
                    "message": text
            }

        weather_followup_markers = [
            "cuaca",
            "weather",
            "gerimis",
            "hujan",
            "cerah",
            "mendung",
            "berawan",
            "panas",
            "dingin",
            "suhu",
            "kelembapan",
        ]

        if any(marker in command for marker in weather_followup_markers):
            return {
                "type": "command",
                "action": "weather",
                "message": text
            }

        knowledge_online_markers = [
            "apa yang kamu tahu tentang",
            "apa yang anda tahu tentang",
            "apa yang kau tahu tentang",
            "cari tahu tentang",
            "gali lebih dalam",
            "lebih dalam tentang",
            "bahas lebih dalam",
            "jelaskan lebih dalam",
            "apa itu",
            "siapa itu",
            "tentang",
        ]

        if any(marker in command for marker in knowledge_online_markers):
            local_exclusions = [
                "rumah",
                "kantor",
                "office",
                "home",
                "lokasi",
                "koordinat",
                "jam",
                "pukul",
                "cuaca",
                "kurs",
                "spotify",
                "youtube",
            ]

            if not any(word in command for word in local_exclusions):
                return {
                    "type": "command",
                    "action": "online_search",
                    "message": text
                }

        product_words = [
            "iphone",
            "samsung",
            "galaxy",
            "xiaomi",
            "oppo",
            "vivo",
            "lenovo",
            "thinkpad",
            "ideapad",
            "asus",
            "rog",
            "macbook",
            "ipad",
            "rtx",
            "nvidia",
            "amd",
            "intel",
            "hyundai",
            "toyota",
            "honda",
            "suzuki",
            "mitsubishi",
            "wuling",
            "byd",
            "chery",
            "omoda",
            "creta",
            "kerta",
            "kereta",
            "mobil",
            "motor",
            "nmax",
            "pcx",
        ]
        research_words = [
            "beda",
            "bedaan",
            "perbedaan",
            "bandingkan",
            "compare",
            "comparison",
            "rincian",
            "detail",
            "spesifikasi",
            "spek",
            "review",
            "harga",
        ]

        if (
            any(word in command for word in product_words) and
            any(word in command for word in research_words)
        ):
            return {
                "type": "command",
                "action": "online_search",
                "message": text
            }

        crypto_markers = [
            "bitcoin",
            "btc",
            "ethereum",
            "etherium",
            "eth",
            "crypto",
            "kripto",
        ]

        if (
            ("harga" in command or "price" in command or "berapa" in command) and
            any(marker in command for marker in crypto_markers)
        ):
            return {
                "type": "command",
                "action": "crypto_price",
                "message": text
            }

        currency_markers = [
            "kurs",
            "exchange rate",
            "dollar",
            "dolar",
            "usd",
            "euro",
            "eur",
            "yen",
            "jpy",
            "pound",
            "gbp",
            "rupiah",
            "idr",
        ]

        if (
            ("kurs tengah" in command or "middle rate" in command) and
            any(marker in command for marker in currency_markers)
        ):
            return {
                "type": "command",
                "action": "middle_rate",
                "message": text
            }

        if any(marker in command for marker in currency_markers):
            return {
                "type": "command",
                "action": "currency_rate",
                "message": text
            }

        product_price_markers = [
            "berapa harga",
            "harga berapa",
            "cek harga",
            "cari harga",
            "carikan harga",
            "harga terbaru",
            "harga sekarang",
            "harga saat ini",
            "price of",
            "how much is",
            "how much does",
            "what is the price",
        ]
        product_price_exclusions = [
            "kurs",
            "kurs tengah",
            "exchange rate",
            "dollar",
            "dolar",
            "usd",
            "euro",
            "eur",
            "yen",
            "jpy",
            "pound",
            "gbp",
            "rupiah",
            "idr",
            "bitcoin",
            "btc",
            "ethereum",
            "etherium",
            "eth",
            "crypto",
            "kripto",
            "berapa lama",
            "waktu tempuh",
            "perjalanan",
            "ongkir",
            "biaya kirim",
        ]

        if (
            any(marker in command for marker in product_price_markers) and
            not any(marker in command for marker in product_price_exclusions)
        ):
            return {
                "type": "command",
                "action": "online_search",
                "message": text
            }

        if (
            "shutdown" in command or
            "shut down laptop" in command or
            "turn off laptop" in command or
            "matikan laptop" in command or
            "matikan komputer" in command or
            "shutdown laptop" in command
        ):
            return {
                "type": "confirm",
                "action": "shutdown",
                "message": "Apakah Anda yakin ingin mematikan laptop?"
            }

        if (
            "restart" in command or
            "reboot" in command or
            "restart laptop" in command or
            "restart komputer" in command or
            "mulai ulang laptop" in command or
            "mulai ulang komputer" in command
        ):
            return {
                "type": "confirm",
                "action": "restart",
                "message": "Apakah Anda yakin ingin restart laptop?"
            }

        if (
            "sleep laptop" in command or
            "put laptop to sleep" in command or
            "tidurkan laptop" in command or
            "laptop tidur" in command or
            "sleep komputer" in command
        ):
            return {
                "type": "confirm",
                "action": "sleep_laptop",
                "message": "Apakah Anda yakin ingin membuat laptop masuk mode sleep?"
            }

        if (
            "youtube" in command or
            "you tube" in command
        ):
            search_markers = [
                "cari",
                "carikan",
                "search",
                "find",
                "video",
                "lagu",
                "song",
                "judul",
                "putar",
                "butar",
                "utar",
                "mainkan",
                "play",
            ]

            if any(marker in command for marker in search_markers):
                return {
                    "type": "command",
                    "action": "youtube_search",
                    "message": text
                }

            if (
                "buka" in command or
                "open" in command or
                "launch" in command
            ):
                return {
                    "type": "command",
                    "action": "open_youtube",
                    "message": text
                }

        if "spotify" in command:
            play_markers = [
                "putar",
                "butar",
                "tar",
                "utara",
                "mainkan",
                "play",
                "nyalakan",
            ]
            search_markers = [
                "cari",
                "carikan",
                "search",
                "find",
                "lagu",
                "song",
                "album",
                "artis",
                "artist",
            ]

            if any(marker in command for marker in play_markers):
                return {
                    "type": "command",
                    "action": "spotify_play",
                    "message": text
                }

            if any(marker in command for marker in search_markers):
                return {
                    "type": "command",
                    "action": "spotify_search",
                    "message": text
                }

            if (
                "buka" in command or
                "open" in command or
                "launch" in command
            ):
                return {
                    "type": "command",
                    "action": "open_spotify",
                    "message": text
                }

        if (
            (
                command.startswith("di ") and
                ("hari ini" in command or "sekarang" in command)
            ) or
            (
                command.startswith("di") and
                not command.startswith("dimana") and
                ("hari ini" in command or "sekarang" in command) and
                len(command.split()) <= 4
            ) or
            (
                " " in command and
                ("hari ini" in command or "sekarang" in command) and
                len(command.split()) <= 4 and
                not command.startswith("apa ")
            )
            and not any(word in command for word in ["jam", "pukul", "time", "waktu"])
        ):
            return {
                "type": "command",
                "action": "weather",
                "message": text
            }

        local_commands = {
            "capabilities": [
                "what can you do",
                "what can you do for me",
                "what are your abilities",
                "show your abilities",
                "list your abilities",
                "apa yang bisa kamu lakukan",
                "kamu bisa apa",
                "nova bisa apa",
                "apa kemampuan kamu",
                "sebutkan kemampuan kamu",
                "fitur kamu apa",
            ],
            "open_chrome": [
                "open chrome",
                "launch chrome",
                "start chrome",
                "buka chrome",
                "bukakan chrome",
                "jalankan chrome",
            ],
            "time": [
                "time",
                "what time is it",
                "but time is it",
                "what dime is it",
                "current time",
                "jam berapa",
                "sekarang jam berapa",
                "pukul berapa",
                "waktu sekarang",
            ],
            "system_status": [
                "system status",
                "check system",
                "status system",
                "cek sistem",
                "cek status",
                "cek status sistem",
                "status sistem",
                "status laptop",
                "spesifikasi laptop",
                "spek laptop",
                "laptop specs",
                "cek laptop",
                "kondisi sistem",
                "kondisi laptop",
            ],
            "battery_status": [
                "battery",
                "battery status",
                "check battery",
                "baterai",
                "cek baterai",
                "status baterai",
                "sisa baterai",
            ],
            "date": [
                "date",
                "today date",
                "what date is it",
                "tanggal",
                "tanggal berapa",
                "hari ini tanggal berapa",
            ],
            "weather": [
                "weather",
                "weather today",
                "weather now",
                "what is the weather",
                "how is the weather",
                "cuaca",
                "cuaca hari ini",
                "cuaca sekarang",
                "bagaimana cuaca",
                "cek cuaca",
            ],
            "open_notepad": [
                "open notepad",
                "launch notepad",
                "buka notepad",
                "bukakan notepad",
            ],
            "open_calculator": [
                "open calculator",
                "launch calculator",
                "buka kalkulator",
                "bukakan kalkulator",
                "buka calculator",
            ],
            "open_explorer": [
                "open file explorer",
                "open explorer",
                "buka file explorer",
                "buka explorer",
                "buka folder",
            ],
        }

        for action, phrases in local_commands.items():
            if any(phrase in command for phrase in phrases):
                return {
                    "type": "command",
                    "action": action,
                    "message": text
                }

        return {
            "type": "chat",
            "message": text
        }
