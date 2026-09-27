from core.plugin_loader import PluginLoader
from core.screen_vision import ScreenVision
from datetime import datetime
try:
    from zoneinfo import ZoneInfo
except ImportError:
    ZoneInfo = None
from system.monitor import SystemMonitor
import subprocess
import requests
import re
import json
import os
import time
import base64
import webbrowser
import queue
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from html import unescape
from urllib.parse import quote, quote_plus, urlencode, urlparse, parse_qs


class CommandEngine:

    def __init__(self):
        loader = PluginLoader()
        self.plugins = loader.load_plugins()
        self.monitor = SystemMonitor()
        self.project_root = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..")
        )
        self.locations_file = os.path.join(
            self.project_root,
            "config",
            "locations.json"
        )
        self.env_file = os.path.join(self.project_root, ".env")
        self.settings_file = os.path.join(
            self.project_root,
            "config",
            "settings.json"
        )
        self.spotify_token_file = os.path.join(
            self.project_root,
            "config",
            "spotify_token.json"
        )
        self.load_env_file()
        self.screen_vision = ScreenVision(
            env_file=self.env_file,
            settings_file=self.settings_file
        )
        self.spotify_client_id = os.getenv("SPOTIFY_CLIENT_ID", "").strip()
        self.spotify_client_secret = os.getenv("SPOTIFY_CLIENT_SECRET", "").strip()
        self.spotify_redirect_uri = os.getenv(
            "SPOTIFY_REDIRECT_URI",
            "http://127.0.0.1:8888/callback"
        ).strip()
        self.capabilities = [
            ("id", "mendengarkan perintah suara tanpa wake word"),
            ("id", "menjawab pertanyaan umum dalam bahasa Indonesia atau Inggris"),
            ("id", "mencari informasi online terbaru menggunakan Tavily"),
            ("id", "membuka krom, catatan, kalkulator, dan folder"),
            ("id", "memberi tahu jam, tanggal, baterai, status sistem, cuaca, kurs mata uang, dan harga crypto dasar"),
            ("id", "membuka YouTube atau Spotify, mencari media, dan mencoba memutar lagu Spotify berdasarkan perintah suara"),
            ("id", "menyimpan lokasi rumah dan kantor lalu membuka rute Google Maps tanpa API"),
            ("id", "membaca layar Google Maps untuk estimasi durasi perjalanan saat diminta"),
            ("id", "menerjemahkan kalimat antara bahasa Indonesia dan bahasa Inggris"),
            ("id", "memuat ulang NOVA dari perintah update atau restart"),
            ("id", "menjeda listening dengan perintah sleep dan aktif lagi dengan wake up atau bangun"),
            ("id", "mematikan, restart, atau sleep laptop dengan konfirmasi"),
            ("en", "listen to voice commands without a wake word"),
            ("en", "answer general questions in Indonesian or English"),
            ("en", "search fresh online information using Tavily"),
            ("en", "open Chrome, Notepad, Calculator, and File Explorer"),
            ("en", "report time, date, battery, system status, weather, exchange rates, and basic crypto prices"),
            ("en", "open YouTube or Spotify, search media, and try to play Spotify songs from voice commands"),
            ("en", "save home and office locations and open Google Maps directions without an API"),
            ("en", "read the Google Maps screen for travel time estimates when asked"),
            ("en", "translate sentences between Indonesian and English"),
            ("en", "restart NOVA from an update or restart voice command"),
            ("en", "pause listening with sleep and wake again with wake up or bangun"),
            ("en", "shut down, restart, or sleep the laptop after confirmation"),
        ]

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

    def execute(self, command):
        command = command.lower()

        if command in self.plugins:
            return self.plugins[command]()

        return "Command not recognized."

    def execute_action(self, action, language="en", command_text=""):
        if action == "capabilities":
            return self.get_capabilities(language)

        if action == "self_update":
            return self.self_update_nova(language, command_text)

        if action == "open_chrome":
            return self.open_chrome(language)

        if action == "open_youtube":
            return self.open_youtube(language)

        if action == "youtube_search":
            return self.search_youtube(language, command_text)

        if action == "open_spotify":
            return self.open_spotify(language)

        if action == "spotify_search":
            return self.search_spotify(language, command_text)

        if action == "spotify_play":
            return self.play_spotify(language, command_text)

        if action == "save_location":
            return self.save_location_from_command(language, command_text)

        if action == "saved_location":
            return self.get_saved_location(language, command_text)

        if action == "maps_route":
            return self.open_saved_maps_route(language, command_text)

        if action == "time":
            return self.get_time(language)

        if action == "world_time":
            return self.get_world_time(language, command_text)

        if action == "system_status":
            return self.get_system_status(language, command_text)

        if action == "battery_status":
            return self.get_battery_status(language)

        if action == "date":
            return self.get_date(language)

        if action == "weather":
            return self.get_weather(language, command_text)

        if action == "us_president":
            return self.get_us_president(language)

        if action == "usd_idr_rate":
            return self.get_currency_rate(language, command_text)

        if action == "currency_rate":
            return self.get_currency_rate(language, command_text)

        if action == "middle_rate":
            return self.get_middle_rate(language, command_text)

        if action == "crypto_price":
            return self.get_crypto_price(language, command_text)

        if action == "open_notepad":
            return self.open_program("notepad", "Notepad", language)

        if action == "open_calculator":
            return self.open_program("calc", "Calculator", language)

        if action == "open_explorer":
            return self.open_program("explorer", "File Explorer", language)

        if action == "shutdown":
            return self.shutdown_laptop(language)

        if action == "restart":
            return self.restart_laptop(language)

        if action == "sleep_laptop":
            return self.sleep_laptop(language)

        return "Command not recognized."

    def get_capabilities(self, language="en"):
        lines = [
            text for item_language, text in self.capabilities
            if item_language == language
        ]

        plugin_names = sorted(self.plugins.keys())

        if language == "id":
            display_lines = [
                "Saya bisa melakukan banyak hal untuk Anda. Untuk detailnya bisa dicek di list berikut.",
                "",
                "Kemampuan utama:",
            ]

            display_lines.extend(
                f"{index}. {line}."
                for index, line in enumerate(lines, start=1)
            )

            if plugin_names:
                display_lines.extend([
                    "",
                    "Plugin aktif: " + ", ".join(plugin_names) + ".",
                ])

            return {
                "speech": "Saya bisa melakukan banyak hal untuk Anda. Untuk detailnya bisa dicek di list berikut.",
                "display": "\n".join(display_lines),
                "language": "id",
            }

        display_lines = [
            "I can help with many things. You can check the detailed list on screen.",
            "",
            "Main capabilities:",
        ]

        display_lines.extend(
            f"{index}. {line}."
            for index, line in enumerate(lines, start=1)
        )

        if plugin_names:
            display_lines.extend([
                "",
                "Active plugins: " + ", ".join(plugin_names) + ".",
            ])

        return {
            "speech": "I can help with many things. You can check the detailed list on screen.",
            "display": "\n".join(display_lines),
            "language": "en",
        }

    def self_update_nova(self, language="en", command_text=""):
        command = " ".join(str(command_text or "").lower().split())
        id_update_markers = [
            "software mu",
            "softwaremu",
            "softwarenya",
            "perbarui",
            "muat ulang",
            "update software mu",
            "nova update software",
            "anova update software",
            "nota update software",
            "nofa update software",
        ]
        en_update_markers = [
            "please update yourself",
            "update yourself",
            "restart yourself",
            "update your software",
        ]

        if any(marker in command for marker in id_update_markers):
            language = "id"
        elif (
            "update software" in command and
            not any(marker in command for marker in en_update_markers)
        ):
            language = "id"

        restart_script = os.path.join(self.project_root, "restart_nova_hidden.vbs")

        if not os.path.exists(restart_script):
            if language == "id":
                return "Saya belum menemukan file restart NOVA."

            return "I could not find the NOVA restart file."

        try:
            subprocess.Popen(
                ["wscript.exe", restart_script],
                cwd=self.project_root,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

            if language == "id":
                return "Baik, saya akan memuat ulang NOVA dengan versi terbaru."

            return "Okay, I will restart NOVA with the latest local version."
        except Exception as error:
            if language == "id":
                return f"Saya belum bisa memuat ulang NOVA. {error}"

            return f"I could not restart NOVA. {error}"

    def open_chrome(self, language="en"):
        try:
            subprocess.Popen(
                ["cmd", "/c", "start", "", "chrome"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            if language == "id":
                return "Membuka Chrome."

            return "Opening Chrome, Sir."
        except Exception as error:
            if language == "id":
                return f"Saya belum bisa membuka Chrome. {error}"

            return f"I could not open Chrome, Sir. {error}"

    def open_url(self, url):
        escaped_url = url.replace("'", "''")
        subprocess.Popen(
            [
                "powershell",
                "-NoProfile",
                "-WindowStyle",
                "Hidden",
                "-Command",
                f"Start-Process '{escaped_url}'",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

    def open_chrome_url(self, url):
        try:
            escaped_url = url.replace("'", "''")
            subprocess.Popen(
                [
                    "powershell",
                    "-NoProfile",
                    "-WindowStyle",
                    "Hidden",
                    "-Command",
                    f"Start-Process chrome -ArgumentList '{escaped_url}'",
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        except Exception:
            self.open_url(url)

    def open_youtube(self, language="en"):
        try:
            self.open_chrome_url("https://www.youtube.com")

            if language == "id":
                return "Membuka YouTube. Mau cari video apa?"

            return "Opening YouTube. What video would you like to search for?"
        except Exception as error:
            if language == "id":
                return f"Saya belum bisa membuka YouTube. {error}"

            return f"I could not open YouTube. {error}"

    def extract_youtube_query(self, command_text):
        query = command_text.lower().strip(" .?!,")
        replacements = [
            "coba kamu cari dan putar",
            "coba kamu cari dan butar",
            "coba kamu cari dan utar",
            "coba cari dan putar",
            "coba cari dan butar",
            "coba cari dan utar",
            "cari dan putar",
            "cari dan butar",
            "cari dan utar",
            "coba kamu",
            "coba",
            "kamu",
            "cari video tentang",
            "carikan video tentang",
            "cari video",
            "carikan video",
            "cari lagu tentang",
            "carikan lagu tentang",
            "cari lagu",
            "carikan lagu",
            "search youtube for",
            "search for",
            "find video about",
            "find video",
            "putar lagu",
            "butar lagu",
            "utar lagu",
            "mainkan lagu",
            "play song",
            "putar",
            "butar",
            "utar",
            "mainkan",
            "play",
            "lagu",
            "song",
            "dengan judul",
            "judul",
            "di youtube",
            "on youtube",
            "youtube",
            "you tube",
            "tentang",
            "mengenai",
            "tolong",
            "please",
        ]

        for replacement in replacements:
            query = query.replace(replacement, " ")

        corrections = {
            "paruh nafas": "separuh nafas",
            "paru nafas": "separuh nafas",
            "separu nafas": "separuh nafas",
            "separuh napas": "separuh nafas",
            "dewa19": "dewa 19",
            "dewas 19": "dewa 19",
            "dawas 19": "dewa 19",
            "dos 19": "dewa 19",
        }

        for source, replacement in corrections.items():
            query = re.sub(
                rf"(?<!\w){re.escape(source)}(?!\w)",
                replacement,
                query
            )

        query = " ".join(query.split()).strip(" .?!,")
        return query

    def clean_media_query(self, command_text, platform_words):
        query = command_text.lower().strip(" .?!,")
        replacements = [
            "coba kamu buka spotify lalu mainkan",
            "coba buka spotify lalu mainkan",
            "buka spotify lalu mainkan",
            "open spotify and play",
            "coba kamu cari dan putar",
            "coba kamu cari dan butar",
            "coba cari dan putar",
            "coba cari dan butar",
            "cari dan putar",
            "cari dan butar",
            "tolong cari dan putar",
            "cari lagu tentang",
            "carikan lagu tentang",
            "cari lagu",
            "carikan lagu",
            "lagu",
            "song",
            "album",
            "artis",
            "artist",
            "cari video tentang",
            "carikan video tentang",
            "cari video",
            "carikan video",
            "search for",
            "search",
            "find",
            "play",
            "tar",
            "utara",
            "butar",
            "putar",
            "mainkan",
            "buka",
            "open",
            "lalu",
            "dengan judul",
            "judul",
            "and",
            "tentang",
            "mengenai",
            "coba",
            "kamu",
            "tolong",
            "please",
        ] + platform_words

        for replacement in replacements:
            query = re.sub(
                rf"(?<!\w){re.escape(replacement)}(?!\w)",
                " ",
                query
            )

        corrections = {
            "paruh nafas": "separuh nafas",
            "paru nafas": "separuh nafas",
            "separu nafas": "separuh nafas",
            "separuh napas": "separuh nafas",
            "dewa19": "dewa 19",
            "dewas 19": "dewa 19",
            "dawas 19": "dewa 19",
            "dos 19": "dewa 19",
        }

        for source, replacement in corrections.items():
            query = re.sub(
                rf"(?<!\w){re.escape(source)}(?!\w)",
                replacement,
                query
            )

        return " ".join(query.split()).strip(" .?!,")

    def search_youtube(self, language="en", command_text=""):
        query = self.extract_youtube_query(command_text)

        if not query:
            if language == "id":
                return "Mau cari video apa di YouTube?"

            return "What video would you like to search for on YouTube?"

        try:
            url = (
                "https://www.youtube.com/results?search_query="
                f"{quote_plus(query)}"
            )
            self.open_chrome_url(url)

            if language == "id":
                return f"Mencari video {query} di YouTube."

            return f"Searching YouTube for {query}."
        except Exception as error:
            if language == "id":
                return f"Saya belum bisa mencari di YouTube. {error}"

            return f"I could not search YouTube. {error}"

    def open_spotify(self, language="en"):
        try:
            self.launch_spotify_app()

            if language == "id":
                return "Membuka Spotify. Mau cari lagu, album, atau artis apa?"

            return "Opening Spotify. What song, album, or artist would you like to search for?"
        except Exception as error:
            if language == "id":
                return f"Saya belum bisa membuka Spotify. {error}"

            return f"I could not open Spotify. {error}"

    def launch_spotify_app(self):
        try:
            self.open_url("spotify:")
            return
        except Exception:
            pass

        subprocess.Popen(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                (
                    "Start-Process "
                    "'shell:AppsFolder\\SpotifyAB.SpotifyMusic_zpdnekdrzrea0!Spotify'"
                ),
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

    def search_spotify(self, language="en", command_text=""):
        query = self.clean_media_query(
            command_text,
            ["di spotify", "on spotify", "spotify"]
        )

        if not query:
            if language == "id":
                return "Mau cari apa di Spotify?"

            return "What would you like to search for on Spotify?"

        try:
            self.open_spotify_search(query)

            if language == "id":
                return f"Membuka pencarian {query} di Spotify."

            return f"Opening Spotify search for {query}."
        except Exception as error:
            if language == "id":
                return f"Saya belum bisa mencari di Spotify. {error}"

            return f"I could not search Spotify. {error}"

    def open_spotify_search(self, query):
        url = f"spotify:search:{quote(query)}"
        self.open_url(url)

    def play_spotify(self, language="en", command_text=""):
        query = self.clean_media_query(
            command_text,
            ["di spotify", "on spotify", "spotify"]
        )

        if not query:
            if language == "id":
                return "Lagu apa yang mau diputar di Spotify?"

            return "What song would you like me to play on Spotify?"

        try:
            self.launch_spotify_app()
            track = self.search_spotify_track(query)
            self.play_spotify_track(track["uri"])

            if language == "id":
                return f"Memutar {track['name']} dari {track['artist']} di Spotify."

            return f"Playing {track['name']} by {track['artist']} on Spotify."
        except Exception as error:
            try:
                self.open_spotify_search(query)
                self.try_spotify_keyboard_play()
            except Exception:
                pass

            error_text = str(error)
            auth_hint_id = (
                " Pastikan Redirect URI di Spotify Developer Dashboard sama persis: "
                f"{self.spotify_redirect_uri}"
            )
            auth_hint_en = (
                " Make sure the Redirect URI in Spotify Developer Dashboard matches exactly: "
                f"{self.spotify_redirect_uri}"
            )
            if (
                "authorization timeout" in error_text.lower() or
                "tidak ada code" in error_text.lower() or
                "redirect_uri" in error_text.lower()
            ):
                error_text += auth_hint_id if language == "id" else auth_hint_en

            if language == "id":
                return f"Saya belum bisa memutar lewat Spotify API. Saya coba buka pencarian {query} di Spotify. {error_text}"

            return f"I could not play through the Spotify API. I tried opening Spotify search for {query}. {error_text}"

    def spotify_auth_header(self):
        raw = f"{self.spotify_client_id}:{self.spotify_client_secret}"
        encoded = base64.b64encode(raw.encode("utf-8")).decode("ascii")
        return {"Authorization": f"Basic {encoded}"}

    def load_spotify_token(self):
        if not os.path.exists(self.spotify_token_file):
            return {}

        try:
            with open(self.spotify_token_file, "r", encoding="utf-8") as file:
                data = json.load(file)

            if isinstance(data, dict):
                return data
        except Exception:
            pass

        return {}

    def save_spotify_token(self, token):
        os.makedirs(os.path.dirname(self.spotify_token_file), exist_ok=True)

        if "expires_in" in token:
            token["expires_at"] = time.time() + int(token["expires_in"]) - 60

        with open(self.spotify_token_file, "w", encoding="utf-8") as file:
            json.dump(token, file, ensure_ascii=False, indent=2)

    def get_spotify_access_token(self):
        if not self.spotify_client_id or not self.spotify_client_secret:
            raise RuntimeError("Spotify Client ID atau Client Secret belum diset.")

        token = self.load_spotify_token()

        if token.get("access_token") and time.time() < token.get("expires_at", 0):
            return token["access_token"]

        if token.get("refresh_token"):
            refreshed = self.refresh_spotify_token(token["refresh_token"])
            if "refresh_token" not in refreshed:
                refreshed["refresh_token"] = token["refresh_token"]
            self.save_spotify_token(refreshed)
            return refreshed["access_token"]

        token = self.authorize_spotify()
        self.save_spotify_token(token)
        return token["access_token"]

    def refresh_spotify_token(self, refresh_token):
        response = requests.post(
            "https://accounts.spotify.com/api/token",
            data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
            },
            headers=self.spotify_auth_header(),
            timeout=20
        )
        response.raise_for_status()
        return response.json()

    def authorize_spotify(self):
        parsed = urlparse(self.spotify_redirect_uri)
        host = parsed.hostname or "127.0.0.1"
        port = parsed.port or 8888
        path = parsed.path or "/callback"
        result = {}

        class ReusableHTTPServer(HTTPServer):
            allow_reuse_address = True

        class CallbackHandler(BaseHTTPRequestHandler):
            def do_GET(handler_self):
                parsed_path = urlparse(handler_self.path)

                if parsed_path.path != path:
                    handler_self.send_response(404)
                    handler_self.end_headers()
                    return

                query = parse_qs(parsed_path.query)
                result["code"] = query.get("code", [""])[0]
                result["error"] = query.get("error", [""])[0]
                handler_self.send_response(200)
                handler_self.send_header("Content-Type", "text/html; charset=utf-8")
                handler_self.end_headers()
                handler_self.wfile.write(
                    b"<html><body><h2>Spotify connected. You can close this tab.</h2></body></html>"
                )

            def log_message(self, format, *args):
                return

        try:
            server = ReusableHTTPServer((host, port), CallbackHandler)
        except OSError as error:
            raise RuntimeError(
                f"Spotify callback server tidak bisa berjalan di {host}:{port}. {error}"
            )

        server.timeout = int(os.getenv("SPOTIFY_AUTH_TIMEOUT_SECONDS", "180"))
        scopes = [
            "user-read-playback-state",
            "user-modify-playback-state",
            "user-read-currently-playing",
            "streaming",
        ]
        auth_url = (
            "https://accounts.spotify.com/authorize?"
            + urlencode({
                "client_id": self.spotify_client_id,
                "response_type": "code",
                "redirect_uri": self.spotify_redirect_uri,
                "scope": " ".join(scopes),
                "show_dialog": "false",
            })
        )

        try:
            webbrowser.open(auth_url)
            server.handle_request()
        finally:
            server.server_close()

        if result.get("error"):
            raise RuntimeError(f"Spotify authorization failed: {result['error']}")

        if not result.get("code"):
            raise RuntimeError("Spotify authorization timeout atau tidak ada code.")

        response = requests.post(
            "https://accounts.spotify.com/api/token",
            data={
                "grant_type": "authorization_code",
                "code": result["code"],
                "redirect_uri": self.spotify_redirect_uri,
            },
            headers=self.spotify_auth_header(),
            timeout=20
        )
        response.raise_for_status()
        return response.json()

    def spotify_api(self, method, endpoint, **kwargs):
        token = self.get_spotify_access_token()
        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {token}"
        response = requests.request(
            method,
            f"https://api.spotify.com/v1/{endpoint.lstrip('/')}",
            headers=headers,
            timeout=20,
            **kwargs
        )

        if response.status_code == 401:
            token_data = self.load_spotify_token()
            if token_data.get("refresh_token"):
                refreshed = self.refresh_spotify_token(token_data["refresh_token"])
                if "refresh_token" not in refreshed:
                    refreshed["refresh_token"] = token_data["refresh_token"]
                self.save_spotify_token(refreshed)
                headers["Authorization"] = f"Bearer {refreshed['access_token']}"
                response = requests.request(
                    method,
                    f"https://api.spotify.com/v1/{endpoint.lstrip('/')}",
                    headers=headers,
                    timeout=20,
                    **kwargs
                )

        response.raise_for_status()

        if response.content:
            return response.json()

        return {}

    def search_spotify_track(self, query):
        data = self.spotify_api(
            "GET",
            "search",
            params={
                "q": query,
                "type": "track",
                "limit": 1,
            }
        )
        items = data.get("tracks", {}).get("items", [])

        if not items:
            raise RuntimeError(f"Lagu {query} tidak ditemukan.")

        track = items[0]
        artists = ", ".join(artist["name"] for artist in track.get("artists", []))
        return {
            "uri": track["uri"],
            "name": track["name"],
            "artist": artists or "unknown artist",
        }

    def get_spotify_device_id(self):
        devices = self.spotify_api("GET", "me/player/devices").get("devices", [])

        if not devices:
            self.launch_spotify_app()
            time.sleep(4)
            devices = self.spotify_api("GET", "me/player/devices").get("devices", [])

        if not devices:
            raise RuntimeError("Tidak ada device Spotify aktif. Buka aplikasi Spotify dulu.")

        active = [device for device in devices if device.get("is_active")]
        selected = active[0] if active else devices[0]
        return selected["id"]

    def play_spotify_track(self, track_uri):
        device_id = self.get_spotify_device_id()
        self.spotify_api(
            "PUT",
            f"me/player/play?device_id={quote(device_id)}",
            json={"uris": [track_uri]},
            headers={"Content-Type": "application/json"}
        )

    def try_spotify_keyboard_play(self):
        script = r"""
$ws = New-Object -ComObject WScript.Shell
Start-Sleep -Milliseconds 3200

Add-Type @"
using System;
using System.Runtime.InteropServices;

public class NovaWin32 {
    [StructLayout(LayoutKind.Sequential)]
    public struct RECT {
        public int Left;
        public int Top;
        public int Right;
        public int Bottom;
    }

    [DllImport("user32.dll")]
    public static extern bool GetWindowRect(IntPtr hWnd, out RECT lpRect);

    [DllImport("user32.dll")]
    public static extern bool SetCursorPos(int X, int Y);

    [DllImport("user32.dll")]
    public static extern void mouse_event(uint dwFlags, uint dx, uint dy, uint dwData, UIntPtr dwExtraInfo);

}
"@

$spotify = Get-Process Spotify -ErrorAction SilentlyContinue |
    Where-Object { $_.MainWindowHandle -ne 0 } |
    Select-Object -First 1

if ($spotify) {
    $ws.AppActivate($spotify.Id) | Out-Null
    Start-Sleep -Milliseconds 800

    $rect = New-Object NovaWin32+RECT
    if ([NovaWin32]::GetWindowRect($spotify.MainWindowHandle, [ref]$rect)) {
        $width = $rect.Right - $rect.Left
        $height = $rect.Bottom - $rect.Top

        # Spotify search result top row green play button, relative to window size.
        $x = $rect.Left + [int]($width * 0.735)
        $y = $rect.Top + [int]($height * 0.205)

        [NovaWin32]::SetCursorPos($x, $y) | Out-Null
        Start-Sleep -Milliseconds 180
        [NovaWin32]::mouse_event(0x0002, 0, 0, 0, [UIntPtr]::Zero)
        [NovaWin32]::mouse_event(0x0004, 0, 0, 0, [UIntPtr]::Zero)
        Start-Sleep -Milliseconds 450

        # Some Spotify layouts place the top result play button a bit lower.
        $y2 = $rect.Top + [int]($height * 0.235)
        [NovaWin32]::SetCursorPos($x, $y2) | Out-Null
        Start-Sleep -Milliseconds 120
        [NovaWin32]::mouse_event(0x0002, 0, 0, 0, [UIntPtr]::Zero)
        [NovaWin32]::mouse_event(0x0004, 0, 0, 0, [UIntPtr]::Zero)
    }
} else {
    $activated = $ws.AppActivate('Spotify')
    Start-Sleep -Milliseconds 500
    if ($activated) {
        $ws.SendKeys('{ENTER}')
        Start-Sleep -Milliseconds 500
        $ws.SendKeys(' ')
    }
}
"""
        subprocess.Popen(
            [
                "powershell",
                "-NoProfile",
                "-WindowStyle",
                "Hidden",
                "-Command",
                script,
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

    def load_locations(self):
        if not os.path.exists(self.locations_file):
            return {}

        try:
            with open(self.locations_file, "r", encoding="utf-8") as file:
                data = json.load(file)

            if isinstance(data, dict):
                return data
        except Exception:
            pass

        return {}

    def save_locations(self, locations):
        os.makedirs(os.path.dirname(self.locations_file), exist_ok=True)

        with open(self.locations_file, "w", encoding="utf-8") as file:
            json.dump(locations, file, ensure_ascii=False, indent=2)

    def normalize_maps_location_query(self, value):
        value = value.strip()

        if not value.startswith(("http://", "https://")):
            return value

        try:
            response = requests.get(
                value,
                allow_redirects=True,
                timeout=12,
                headers={"User-Agent": "Mozilla/5.0"}
            )
            final_url = response.url
        except Exception:
            final_url = value

        coordinate_match = re.search(
            r"!3d(-?\d+(?:\.\d+)?)!4d(-?\d+(?:\.\d+)?)",
            final_url
        )

        if coordinate_match:
            return f"{coordinate_match.group(1)},{coordinate_match.group(2)}"

        coordinate_match = re.search(
            r"/@(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?)",
            final_url
        )

        if coordinate_match:
            return f"{coordinate_match.group(1)},{coordinate_match.group(2)}"

        return final_url

    def extract_location_alias(self, command_text):
        command = command_text.lower()

        aliases = {
            "home": ["rumah", "home"],
            "office": [
                "kantor",
                "ke kantor",
                "kekantor",
                "lantor",
                "kantoor",
                "cantor",
                "office",
                "tempat kerja",
                "work",
            ],
        }

        for alias, markers in aliases.items():
            if any(marker in command for marker in markers):
                return alias

        return ""

    def location_display_name(self, alias, language="id"):
        names = {
            "home": ("rumah", "home"),
            "office": ("kantor", "office"),
        }
        id_name, en_name = names.get(alias, (alias, alias))
        return id_name if language == "id" else en_name

    def extract_location_value(self, command_text):
        text = command_text.strip()
        lowered = text.lower()
        markers = [
            "di alamat",
            "alamatnya",
            "lokasinya",
            "lokasi rumah saya di",
            "lokasi kantor saya di",
            "rumah saya di",
            "kantor saya di",
            "save home as",
            "save office as",
            "set home to",
            "set office to",
            "at",
            "di",
        ]

        for marker in markers:
            index = lowered.rfind(marker)
            if index >= 0:
                value = text[index + len(marker):].strip(" .?!,:;")
                if value:
                    return value

        return ""

    def save_location_from_command(self, language="en", command_text=""):
        alias = self.extract_location_alias(command_text)
        value = self.extract_location_value(command_text)

        if not alias:
            if language == "id":
                return "Lokasi apa yang ingin disimpan? Misalnya rumah atau kantor."

            return "Which location would you like me to save? For example, home or office."

        if not value:
            name = self.location_display_name(alias, language)
            if language == "id":
                return f"Sebutkan alamat atau link Google Maps untuk lokasi {name}."

            return f"Please say the address or Google Maps link for {name}."

        locations = self.load_locations()
        locations[alias] = {
            "label": self.location_display_name(alias, "id"),
            "query": self.normalize_maps_location_query(value),
            "source": value,
        }
        self.save_locations(locations)

        name = self.location_display_name(alias, language)
        if language == "id":
            return f"Lokasi {name} sudah saya simpan."

        return f"I saved your {name} location."

    def get_saved_location(self, language="en", command_text=""):
        alias = self.extract_location_alias(command_text)

        if not alias:
            if language == "id":
                return "Lokasi mana yang ingin dicek? Rumah atau kantor?"

            return "Which saved location should I check? Home or office?"

        locations = self.load_locations()
        name = self.location_display_name(alias, language)

        if alias not in locations:
            if language == "id":
                return f"Saya belum punya lokasi {name} yang tersimpan."

            return f"I do not have your {name} location saved yet."

        location = locations[alias]
        query = location.get("query", "").strip()
        source = location.get("source", "").strip()

        if language == "id":
            if source and source != query:
                return (
                    f"Lokasi {name} yang tersimpan adalah koordinat {query}. "
                    f"Sumbernya dari link Google Maps yang kamu berikan: {source}"
                )

            return f"Lokasi {name} yang tersimpan adalah {query}."

        if source and source != query:
            return (
                f"Your saved {name} location is coordinates {query}. "
                f"The source is the Google Maps link you provided: {source}"
            )

        return f"Your saved {name} location is {query}."

    def extract_route_destination_alias(self, command_text):
        command = command_text.lower()

        if any(marker in command for marker in [
            "kantor",
            "ke kantor",
            "kekantor",
            "lantor",
            "kantoor",
            "cantor",
            "office",
            "tempat kerja",
            "work",
        ]):
            return "office"

        if any(marker in command for marker in ["rumah", "home", "pulang"]):
            return "home"

        return ""

    def extract_free_route_destination(self, command_text):
        text = command_text.strip()
        normalized_text = self.normalize_free_route_destination_text(text)
        lowered = normalized_text.lower()
        patterns = [
            r"(?:saya\s+)?(?:mau|ingin|pengen)(?:\s+pergi)?\s+ke\s+(.+)",
            r"(?:saya\s+)?(?:mau|ingin|pengen)\s+(.+)",
            r"(?:^|\s)ke\s+(.+)",
            r"(?:coba\s+)?(?:cek|lihat)\s+(?:rute|arah|waktu|estimasi).*?\s+ke\s+(.+)",
            r"(?:berapa\s+(?:lama|jam|waktu).*?\s+ke)\s+(.+)",
            r"(?:waktu\s+tempuh\s+ke)\s+(.+)",
            r"(?:directions\s+to|route\s+to|go\s+to)\s+(.+)",
            r"^(.+?)\s+(?:berapa\s+(?:lama|jam|waktu)|butuh\s+berapa|perlu\s+berapa|kira-kira\s+berapa|estimasi|waktu\s+tempuh)",
        ]

        for pattern in patterns:
            match = re.search(pattern, lowered, flags=re.IGNORECASE)
            if not match:
                continue

            destination = normalized_text[match.start(1):match.end(1)]
            destination = re.split(
                r"\b(?:berapa|butuh|perlu|waktu|estimasi|kira|kira-kira|ya|dong|tolong|coba|sekarang|cari|tahu|cek|lihat|rute|arah|lama|jam)\b",
                destination,
                maxsplit=1,
                flags=re.IGNORECASE,
            )[0]
            destination = destination.strip(" .?!,;:")
            destination = self.normalize_route_destination_name(destination)

            if destination and destination.lower() not in ["kantor", "rumah", "home", "office"]:
                return destination

        return ""

    def normalize_free_route_destination_text(self, text):
        corrections = {
            "kegeran indonesia": "ke grand indonesia",
            "kegeren indonesia": "ke grand indonesia",
            "ke geran indonesia": "ke grand indonesia",
            "ke geren indonesia": "ke grand indonesia",
            "geran indonesia": "grand indonesia",
            "geren indonesia": "grand indonesia",
            "grand indonesa": "grand indonesia",
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
            "kebun raya boger": "kebun raya bogor",
            "kebun raya bugur": "kebun raya bogor",
            "kebun raya bohor": "kebun raya bogor",
            "kebun raya botor": "kebun raya bogor",
            "kebun raya tukur": "kebun raya bogor",
            "kebun raya tuker": "kebun raya bogor",
            "hotel campinski": "hotel indonesia kempinski jakarta",
            "hotel kempinski": "hotel indonesia kempinski jakarta",
            "campinski": "hotel indonesia kempinski jakarta",
            "kempinski": "hotel indonesia kempinski jakarta",
            "hotel campinski jakarta": "hotel indonesia kempinski jakarta",
            "hotel kempinski jakarta": "hotel indonesia kempinski jakarta",
            "mall tamat anggrek": "mall taman anggrek",
            "tamat anggrek": "taman anggrek",
            "kuri mall": "puri mall",
            "curi mall": "puri mall",
            "puri mol": "puri mall",
            "puri moll": "puri mall",
            "lipomall": "lippo mall",
            "lipo mall": "lippo mall",
            "ais bsd": "ice bsd",
            "is bsd": "ice bsd",
            "i c e bsd": "ice bsd",
        }

        normalized = " ".join(text.split())

        for source, replacement in corrections.items():
            normalized = re.sub(
                rf"(?<!\w){re.escape(source)}(?!\w)",
                replacement,
                normalized,
                flags=re.IGNORECASE,
            )

        normalized = re.sub(r"\bmall\s+mall\s+", "mall ", normalized, flags=re.IGNORECASE)
        return normalized

    def normalize_route_destination_name(self, destination):
        cleaned = " ".join(destination.split()).strip(" .?!,;:")
        lookup = cleaned.lower()
        aliases = {
            "grand indonesia": "Grand Indonesia, Jakarta Pusat",
            "kebun raya bogor": "Kebun Raya Bogor, Bogor, Jawa Barat",
            "hotel indonesia kempinski jakarta": "Hotel Indonesia Kempinski Jakarta, Jakarta Pusat",
            "hotel indonesia kempinski": "Hotel Indonesia Kempinski Jakarta, Jakarta Pusat",
            "hotel kempinski": "Hotel Indonesia Kempinski Jakarta, Jakarta Pusat",
            "kempinski": "Hotel Indonesia Kempinski Jakarta, Jakarta Pusat",
            "campinski": "Hotel Indonesia Kempinski Jakarta, Jakarta Pusat",
            "hotel campinski": "Hotel Indonesia Kempinski Jakarta, Jakarta Pusat",
            "mall ciputra jakarta barat": "Mall Ciputra Jakarta, Jakarta Barat",
            "mall ciputra jakarta": "Mall Ciputra Jakarta, Jakarta Barat",
            "mall ciputra": "Mall Ciputra Jakarta, Jakarta Barat",
            "ciputra jakarta barat": "Mall Ciputra Jakarta, Jakarta Barat",
            "ciputra mall": "Mall Ciputra Jakarta, Jakarta Barat",
            "mall taman anggrek": "Mall Taman Anggrek, Jakarta Barat",
            "taman anggrek": "Mall Taman Anggrek, Jakarta Barat",
            "puri mall": "Puri Indah Mall, Jakarta Barat",
            "puri indah mall": "Puri Indah Mall, Jakarta Barat",
            "mall puri indah": "Puri Indah Mall, Jakarta Barat",
            "lippo mall": "Lippo Mall Puri, Jakarta Barat",
            "lippo mall puri": "Lippo Mall Puri, Jakarta Barat",
            "ice bsd": "ICE BSD, Tangerang Selatan",
        }

        return aliases.get(lookup, cleaned)

    def route_destination_needs_area(self, destination):
        cleaned = " ".join(str(destination or "").split()).strip(" .?!,;:")
        if not cleaned:
            return False

        lookup = cleaned.lower()
        known_places = {
            "grand indonesia",
            "grand indonesia, jakarta pusat",
            "puri mall",
            "puri indah mall, jakarta barat",
            "lippo mall",
            "lippo mall puri",
            "lippo mall puri, jakarta barat",
            "ice bsd",
            "ice bsd, tangerang selatan",
            "mall ciputra jakarta, jakarta barat",
            "mall taman anggrek, jakarta barat",
            "kebun raya bogor, bogor, jawa barat",
        }
        if lookup in known_places:
            return False

        street_markers = [
            "jalan ",
            "jl ",
            "jl. ",
            "jln ",
            "jln. ",
            "gang ",
            "gg ",
            "gg. ",
            "komplek ",
            "kompleks ",
            "cluster ",
            "blok ",
            "ruko ",
            "perumahan ",
            "perum ",
        ]
        if not any(marker in f"{lookup} " for marker in street_markers):
            return False

        area_markers = [
            "jakarta",
            "jakbar",
            "jakarta barat",
            "jakarta utara",
            "jakarta selatan",
            "jakarta timur",
            "jakarta pusat",
            "tangerang",
            "tangsel",
            "tangerang selatan",
            "bogor",
            "depok",
            "bekasi",
            "sentul",
            "bsd",
            "serpong",
            "bintaro",
            "cengkareng",
            "kapuk",
            "puri",
            "gading serpong",
        ]
        if "," in cleaned or any(marker in lookup for marker in area_markers):
            return False

        return True

    def route_area_question(self, destination, language="id"):
        if language == "id":
            return (
                f"{destination} ada di area mana, Alfred? "
                "Sebutkan kota atau daerahnya, misalnya Jakarta Barat, Bogor, atau Sentul."
            )

        return (
            f"Which area is {destination} in? "
            "Please say the city or district, for example West Jakarta, Bogor, or Sentul."
        )

    def extract_route_area_answer(self, text):
        cleaned = " ".join(str(text or "").split()).strip(" .?!,;:")
        if not cleaned:
            return ""

        lookup = cleaned.lower()
        cancel_markers = [
            "batal",
            "cancel",
            "tidak jadi",
            "forget it",
            "lupakan",
        ]
        if any(marker in lookup for marker in cancel_markers):
            return "__cancel__"

        new_task_markers = [
            "cuaca",
            "weather",
            "jam berapa",
            "tanggal",
            "spotify",
            "youtube",
            "kurs",
            "bitcoin",
            "update",
            "restart",
            "shutdown",
            "sleep",
            "buka ",
            "open ",
        ]
        if any(marker in lookup for marker in new_task_markers):
            return ""

        area_aliases = {
            "jakbar": "Jakarta Barat",
            "jakarta barat": "Jakarta Barat",
            "jakarta utara": "Jakarta Utara",
            "jakarta selatan": "Jakarta Selatan",
            "jakarta timur": "Jakarta Timur",
            "jakarta pusat": "Jakarta Pusat",
            "bogor": "Bogor",
            "sentul": "Sentul",
            "depok": "Depok",
            "bekasi": "Bekasi",
            "tangerang": "Tangerang",
            "tangerang selatan": "Tangerang Selatan",
            "tangsel": "Tangerang Selatan",
            "bsd": "BSD",
            "serpong": "Serpong",
            "bintaro": "Bintaro",
            "cengkareng": "Cengkareng",
            "kapuk": "Kapuk",
            "puri": "Puri",
        }

        for source, target in area_aliases.items():
            if re.search(rf"(?<!\w){re.escape(source)}(?!\w)", lookup):
                return target

        area = re.sub(
            r"^(?:yang\s+)?(?:di|daerah|area|sekitar|lokasi|kota)\s+",
            "",
            cleaned,
            flags=re.IGNORECASE,
        ).strip(" .?!,;:")

        if 1 <= len(area.split()) <= 5:
            return area.title()

        return ""

    def build_route_with_area_command(self, destination, area):
        destination = " ".join(str(destination or "").split()).strip(" .?!,;:")
        area = " ".join(str(area or "").split()).strip(" .?!,;:")
        if not destination or not area:
            return ""

        return f"saya mau ke {destination}, {area} berapa lama"

    def build_maps_route_url(self, origin, destination):
        return (
            "https://www.google.com/maps/dir/"
            f"?api=1&origin={quote_plus(str(origin))}"
            f"&destination={quote_plus(str(destination))}"
            "&travelmode=driving&dirflg=d"
        )

    def focus_chrome_window(self):
        script = """
$ws = New-Object -ComObject WScript.Shell
Start-Sleep -Milliseconds 300
if (-not $ws.AppActivate('Google Maps')) {
    $null = $ws.AppActivate('Google Chrome')
}
"""
        subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-WindowStyle",
                "Hidden",
                "-Command",
                script,
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=2,
            check=False,
        )

    def run_with_hard_timeout(self, func, timeout_seconds):
        result_queue = queue.Queue(maxsize=1)

        def worker():
            try:
                result_queue.put(("ok", func()))
            except Exception as error:
                result_queue.put(("error", error))

        thread = threading.Thread(target=worker, daemon=True)
        thread.start()

        try:
            status, value = result_queue.get(timeout=timeout_seconds)
        except queue.Empty:
            raise TimeoutError("Operation took too long.")

        if status == "error":
            raise value

        return value

    def is_maps_route_answer(self, answer):
        text = str(answer or "").strip().lower()
        if not text:
            return False

        if self.is_maps_route_not_found_answer(answer):
            return False

        bad_markers = [
            "user safety",
            "safe",
            "tidak memiliki akses",
            "tidak dapat mengakses",
            "i do not have access",
            "i cannot access",
            "as an ai",
        ]
        if any(marker in text for marker in bad_markers):
            return False

        duration_pattern = r"\b\d+\s*(?:menit|min|m|jam|hour|hours|hr|hrs|h)\b"
        return bool(re.search(duration_pattern, text))

    def extract_maps_route_duration(self, answer):
        text = str(answer or "")
        hour_units = r"jam|hour|hours|hr|hrs|h"
        minute_units = r"menit|min|m"

        composite_patterns = [
            rf"\b(\d+)\s*(?:{hour_units})\s*(\d+)\s*(?:{minute_units})\b",
            rf"(?:durasi\s+utama|durasi|duration|rute\s+mobil|car\s+route)\s*[:\-]?\s*(\d+)\s*(?:{hour_units})\s*(\d+)\s*(?:{minute_units})",
        ]

        for pattern in composite_patterns:
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if match:
                hours = int(match.group(1))
                minutes = int(match.group(2))
                return f"{hours} jam {minutes} menit"

        patterns = [
            rf"(?:durasi\s+utama|durasi|duration|rute\s+mobil|car\s+route)\s*[:\-]?\s*(\d+\s*(?:{minute_units}|{hour_units}))",
            rf"\b(\d+\s*(?:{minute_units}|{hour_units}))\b",
        ]

        for pattern in patterns:
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if match:
                duration = match.group(1).strip()
                duration = re.sub(r"\bmin\b|\bm\b", "menit", duration, flags=re.IGNORECASE)
                duration = re.sub(r"\bhours?\b|\bhrs?\b|\bh\b", "jam", duration, flags=re.IGNORECASE)
                return " ".join(duration.split())

        return ""

    def describe_maps_route_condition_id(self, answer):
        text = str(answer or "").lower()

        if "restricted" in text or "private road" in text or "private roads" in text:
            return "Ada catatan pembatasan akses atau jalan privat di rute tersebut."

        if "lighter traffic" in text:
            return "Lalu lintas lebih ringan dari biasanya."

        if "heavy traffic" in text or "traffic jam" in text or "macet" in text:
            return "Lalu lintas sedang padat."

        if "delay" in text or "delays" in text or "terlambat" in text:
            return "Ada sedikit hambatan di perjalanan."

        if "fastest route" in text and "usual traffic" in text:
            return "Ini rute tercepat, dengan lalu lintas seperti biasa."

        if "fastest route" in text:
            return "Ini rute tercepat berdasarkan kondisi lalu lintas saat ini."

        if "usual traffic" in text or "normal" in text:
            return "Kondisi lalu lintas terlihat normal."

        if "tol" in text or "toll" in text:
            return "Rute kemungkinan melewati jalan tol."

        return ""

    def normalize_maps_route_answer(self, answer, language="id"):
        text = str(answer or "").strip()
        if not text:
            return text

        text = text.replace("ï¿½", " ")
        text = text.replace("�", " ")
        text = text.replace("□", " ")
        text = re.sub(r"\bUser Safety:\s*safe\b\.?", "", text, flags=re.IGNORECASE)
        text = text.replace("*", " ")
        text = re.sub(r"\s+", " ", text).strip()

        if language != "id":
            return text

        duration = self.extract_maps_route_duration(text)
        if not duration:
            return text

        condition = self.describe_maps_route_condition_id(text)
        if condition:
            return f"Estimasi perjalanan dengan mobil sekitar {duration}. {condition}"

        return f"Estimasi perjalanan dengan mobil sekitar {duration}."

    def is_maps_route_not_found_answer(self, answer):
        text = str(answer or "").strip().lower()
        if not text:
            return False

        markers = [
            "route_not_found",
            "rute tidak ditemukan",
            "tidak menemukan tujuan",
            "tidak dapat menemukan tujuan",
            "can't find",
            "cant find",
            "cannot find",
            "can not find",
            "make sure your search is spelled",
            "spelled correctly",
            "try adding a city",
            "periksa ejaan",
        ]
        return any(marker in text for marker in markers)

    def extract_route_not_found_destination(self, answer, fallback=""):
        raw = str(answer or "").strip()
        match = re.search(r"ROUTE_NOT_FOUND\s*:\s*(.+)", raw, re.IGNORECASE)

        if match:
            destination = match.group(1).strip()
        else:
            destination = str(fallback or "").strip()

        destination = destination.splitlines()[0].strip(" .,:;\"'")
        return destination or str(fallback or "").strip()

    def maps_route_not_found_message(self, language="id", destination=""):
        destination = str(destination or "").strip()

        if language == "id":
            if destination:
                return (
                    f"Rute tidak ditemukan untuk tujuan '{destination}'. "
                    "Tolong ulangi nama tujuan, atau tambahkan area dan kota agar lebih tepat."
                )

            return (
                "Rute tidak ditemukan. Tolong ulangi nama tujuan, "
                "atau tambahkan area dan kota agar lebih tepat."
            )

        if destination:
            return (
                f"Route not found for '{destination}'. "
                "Please repeat the destination name, or add the area and city."
            )

        return (
            "Route not found. Please repeat the destination name, "
            "or add the area and city."
        )

    def maps_route_unreadable_message(self, language="id", destination=""):
        destination = str(destination or "").strip()

        if language == "id":
            if destination:
                return (
                    f"Google Maps sudah terbuka untuk tujuan '{destination}', "
                    "tapi saya belum berhasil membaca estimasi waktunya dari layar. "
                    "Silakan lihat panel Maps. Kalau lokasi yang terbuka salah, "
                    "sebutkan ulang tujuan beserta area atau kota."
                )

            return (
                "Google Maps sudah terbuka, tapi saya belum berhasil membaca "
                "estimasi waktunya dari layar. Silakan lihat panel Maps. "
                "Kalau lokasi yang terbuka salah, sebutkan ulang tujuan "
                "beserta area atau kota."
            )

        if destination:
            return (
                f"Google Maps is open for '{destination}', but I could not "
                "read the travel time automatically yet. If the destination "
                "is wrong or not found, repeat it with the area or city."
            )

        return (
            "Google Maps is open, but I could not read the travel time "
            "automatically yet. If the destination is wrong or not found, "
            "repeat it with the area or city."
        )

    def read_maps_route_from_screen(
        self,
        language="id",
        destination_name="",
        wait_seconds=1.2,
        vision_timeout=3,
        hard_timeout=5
    ):
        time.sleep(wait_seconds)
        self.focus_chrome_window()
        time.sleep(0.35)

        try:
            answer = self.run_with_hard_timeout(
                lambda: self.screen_vision.read_maps_route(
                    language,
                    timeout=vision_timeout
                ).strip(),
                hard_timeout
            )
        except requests.exceptions.Timeout:
            return self.maps_route_unreadable_message(language, destination_name)
        except TimeoutError:
            return self.maps_route_unreadable_message(language, destination_name)
        except Exception as error:
            if language == "id":
                return f"Saya sudah membuka Google Maps, tetapi belum bisa membaca layar. {error}"

            return f"I opened Google Maps, but I could not read the screen. {error}"

        answer = re.sub(
            r"(?im)^\s*user\s+safety\s*:\s*safe\s*$",
            "",
            answer
        ).strip()

        if self.is_maps_route_not_found_answer(answer):
            destination = self.extract_route_not_found_destination(
                answer,
                destination_name
            )
            return self.maps_route_not_found_message(language, destination)

        if not self.is_maps_route_answer(answer):
            return self.maps_route_unreadable_message(language, destination_name)

        return self.normalize_maps_route_answer(answer, language)

    def open_saved_maps_route(self, language="en", command_text=""):
        locations = self.load_locations()
        destination_alias = self.extract_route_destination_alias(command_text)
        free_destination = ""

        if not destination_alias:
            free_destination = self.extract_free_route_destination(command_text)

            if not free_destination:
                if language == "id":
                    return "Mau ke lokasi mana? Sebutkan nama tempatnya, misalnya mall, gedung, kantor, atau alamat tujuan."

                return "Where would you like to go? Say the place name, building, office, or destination address."

        if destination_alias and destination_alias not in locations:
            name = self.location_display_name(destination_alias, language)
            if language == "id":
                return f"Saya belum punya lokasi {name}. Simpan lokasinya dulu."

            return f"I do not have your {name} location yet. Please save it first."

        origin_alias = "home" if destination_alias != "home" else "office"

        if origin_alias not in locations:
            origin_name = self.location_display_name(origin_alias, language)
            if language == "id":
                return f"Saya belum punya lokasi {origin_name} sebagai titik awal."

            return f"I do not have your {origin_name} location as the starting point yet."

        origin = locations[origin_alias]["query"]
        destination = (
            locations[destination_alias]["query"]
            if destination_alias
            else free_destination
        )
        url = self.build_maps_route_url(origin, destination)
        self.open_chrome_url(url)

        destination_name = (
            self.location_display_name(destination_alias, language)
            if destination_alias
            else free_destination
        )
        origin_name = self.location_display_name(origin_alias, language)
        screen_answer = self.read_maps_route_from_screen(
            language,
            destination_name=destination_name
        )

        unreadable_markers = [
            "belum bisa membaca",
            "belum terbaca",
            "belum sempat terbaca",
            "belum terbaca otomatis",
            "tidak sesuai atau tidak ditemukan",
            "pembacaan layar terlalu lama",
            "tidak terlihat",
            "cannot read",
            "could not read",
            "wrong or not found",
            "not visible",
        ]

        if not any(marker in screen_answer.lower() for marker in unreadable_markers):
            return screen_answer

        if language == "id":
            return (
                f"Saya sudah membuka rute dari {origin_name} ke {destination_name} "
                "di Google Maps, tapi belum berhasil membaca angka estimasinya "
                "dari layar. Silakan lihat panel Maps. Kalau lokasi yang terbuka "
                "salah, sebutkan ulang tujuan beserta area atau kota."
            )

        return (
            f"I opened the route from {origin_name} to {destination_name} "
            "in Google Maps, but I could not clearly read the travel time from the screen."
        )

    def open_program(self, command, name, language="en"):
        try:
            subprocess.Popen(
                [command],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            if language == "id":
                return f"Membuka {name}."

            return f"Opening {name}."
        except Exception as error:
            if language == "id":
                return f"Saya belum bisa membuka {name}. {error}"

            return f"I could not open {name}. {error}"

    def get_time(self, language="en"):
        now = datetime.now()
        if language == "id":
            return now.strftime("Sekarang pukul %H:%M.")

        return now.strftime("The current time is %H:%M, Sir.")

    def get_world_time(self, language="en", command_text=""):
        locations = self.extract_time_locations(command_text)

        if not locations:
            if language == "id":
                return "Kota atau negara mana yang ingin dicek waktunya?"

            return "Which city or country would you like me to check?"

        source_time = self.extract_jakarta_time(command_text)
        results = []

        for display_name, timezone_name in locations:
            try:
                if ZoneInfo:
                    jakarta_zone = ZoneInfo("Asia/Jakarta")
                    target_zone = ZoneInfo(timezone_name)

                    if source_time:
                        now_jakarta = datetime.now(jakarta_zone)
                        source_dt = now_jakarta.replace(
                            hour=source_time[0],
                            minute=source_time[1],
                            second=0,
                            microsecond=0,
                        )
                    else:
                        source_dt = datetime.now(jakarta_zone)

                    target_dt = source_dt.astimezone(target_zone)
                else:
                    source_dt, target_dt = self.convert_world_time_without_zoneinfo(
                        timezone_name,
                        source_time
                    )
            except Exception:
                source_dt, target_dt = self.convert_world_time_without_zoneinfo(
                    timezone_name,
                    source_time
                )

            results.append((display_name, source_dt, target_dt))

        if language == "id":
            if source_time:
                parts = [
                    f"di {display_name} pukul {target_dt.strftime('%H:%M')}"
                    for display_name, _, target_dt in results
                ]
                return (
                    f"Jika di Jakarta pukul {results[0][1].strftime('%H:%M')}, "
                    f"{', sedangkan '.join(parts)}."
                )

            parts = [
                f"di {display_name} pukul {target_dt.strftime('%H:%M')}"
                for display_name, _, target_dt in results
            ]
            return f"Sekarang {', sedangkan '.join(parts)}."

        if source_time:
            parts = [
                f"in {display_name} it is {target_dt.strftime('%H:%M')}"
                for display_name, _, target_dt in results
            ]
            return (
                f"If it is {results[0][1].strftime('%H:%M')} in Jakarta, "
                f"{', while '.join(parts)}."
            )

        parts = [
            f"in {display_name} it is {target_dt.strftime('%H:%M')}"
            for display_name, _, target_dt in results
        ]
        return f"Right now, {', while '.join(parts)}."

    def time_location_aliases(self):
        return [
            ("china", "China", "Asia/Shanghai"),
            ("cina", "China", "Asia/Shanghai"),
            ("beijing", "Beijing", "Asia/Shanghai"),
            ("shanghai", "Shanghai", "Asia/Shanghai"),
            ("hong kong", "Hong Kong", "Asia/Hong_Kong"),
            ("jepang", "Jepang", "Asia/Tokyo"),
            ("japan", "Japan", "Asia/Tokyo"),
            ("tokyo", "Tokyo", "Asia/Tokyo"),
            ("korea", "Korea", "Asia/Seoul"),
            ("seoul", "Seoul", "Asia/Seoul"),
            ("singapura", "Singapura", "Asia/Singapore"),
            ("singapore", "Singapore", "Asia/Singapore"),
            ("malaysia", "Malaysia", "Asia/Kuala_Lumpur"),
            ("kuala lumpur", "Kuala Lumpur", "Asia/Kuala_Lumpur"),
            ("bangkok", "Bangkok", "Asia/Bangkok"),
            ("thailand", "Thailand", "Asia/Bangkok"),
            ("india", "India", "Asia/Kolkata"),
            ("dubai", "Dubai", "Asia/Dubai"),
            ("london", "London", "Europe/London"),
            ("inggris", "Inggris", "Europe/London"),
            ("uk", "United Kingdom", "Europe/London"),
            ("paris", "Paris", "Europe/Paris"),
            ("prancis", "Prancis", "Europe/Paris"),
            ("new york", "New York", "America/New_York"),
            ("amerika", "Amerika Serikat", "America/New_York"),
            ("los angeles", "Los Angeles", "America/Los_Angeles"),
            ("sydney", "Sydney", "Australia/Sydney"),
            ("australia", "Australia", "Australia/Sydney"),
        ]

    def extract_time_locations(self, command_text):
        command = command_text.lower()
        found = []
        seen_zones = set()

        for alias, display_name, timezone_name in self.time_location_aliases():
            for match in re.finditer(rf"(?<!\w){re.escape(alias)}(?!\w)", command):
                if timezone_name in seen_zones:
                    continue

                found.append((match.start(), display_name, timezone_name))
                seen_zones.add(timezone_name)

        if not found:
            return None

        found.sort(key=lambda item: item[0])
        return [
            (display_name, timezone_name)
            for _, display_name, timezone_name in found
        ]

    def extract_time_location(self, command_text):
        locations = self.extract_time_locations(command_text)

        if not locations:
            return None

        return locations[-1]

    def extract_jakarta_time(self, command_text):
        command = command_text.lower()
        match = re.search(
            r"(?:jam|pukul)\s+(\d{1,2})(?:[:.](\d{1,2}))?\s*(pagi|siang|sore|malam|am|pm)?",
            command
        )

        if not match:
            return None

        hour = int(match.group(1))
        minute = int(match.group(2) or 0)
        marker = match.group(3)

        if marker in ("malam", "pm") and hour < 12:
            hour += 12
        elif marker == "sore" and hour < 12:
            hour += 12
        elif marker == "siang" and hour < 11:
            hour += 12
        elif marker in ("pagi", "am") and hour == 12:
            hour = 0

        if 0 <= hour <= 23 and 0 <= minute <= 59:
            return hour, minute

        return None

    def convert_world_time_without_zoneinfo(self, timezone_name, source_time=None):
        offsets = {
            "Asia/Jakarta": 7,
            "Asia/Shanghai": 8,
            "Asia/Hong_Kong": 8,
            "Asia/Tokyo": 9,
            "Asia/Seoul": 9,
            "Asia/Singapore": 8,
            "Asia/Kuala_Lumpur": 8,
            "Asia/Bangkok": 7,
            "Asia/Kolkata": 5.5,
            "Asia/Dubai": 4,
            "Europe/London": 1,
            "Europe/Paris": 2,
            "America/New_York": -4,
            "America/Los_Angeles": -7,
            "Australia/Sydney": 10,
        }

        now = datetime.now()
        if source_time:
            source_dt = now.replace(
                hour=source_time[0],
                minute=source_time[1],
                second=0,
                microsecond=0,
            )
        else:
            source_dt = now

        target_offset = offsets.get(timezone_name, 7)
        minutes_delta = int((target_offset - 7) * 60)
        from datetime import timedelta
        target_dt = source_dt + timedelta(minutes=minutes_delta)
        return source_dt, target_dt

    def get_date(self, language="en"):
        now = datetime.now()
        if language == "id":
            days = [
                "Senin",
                "Selasa",
                "Rabu",
                "Kamis",
                "Jumat",
                "Sabtu",
                "Minggu",
            ]
            months = [
                "Januari",
                "Februari",
                "Maret",
                "April",
                "Mei",
                "Juni",
                "Juli",
                "Agustus",
                "September",
                "Oktober",
                "November",
                "Desember",
            ]
            day_name = days[now.weekday()]
            month_name = months[now.month - 1]
            return f"Hari ini {day_name}, {now.day} {month_name} {now.year}."

        return now.strftime("Today is %A, %B %d, %Y.")

    def get_system_status(self, language="en", command_text=""):
        data = self.monitor.get_status()
        command = command_text.lower()

        if (
            "laptop" in command or
            "spesifikasi" in command or
            "spek" in command or
            "spec" in command
        ):
            return self.get_laptop_status(language, data)

        if language == "id":
            gpu_temp = self.temperature_text(data["gpu_temp_text"], language)
            cpu_temperature_sentence = ""

            if data["cpu_temp_text"]:
                cpu_temperature_sentence = (
                    f"Suhu CPU {data['cpu_temp_text']}. "
                )

            return (
                f"Status sistem. "
                f"CPU {data['cpu_name']}, penggunaan {data['cpu']} persen. "
                f"{cpu_temperature_sentence}"
                f"GPU {data['gpu_name']}, penggunaan {data['gpu']} persen. "
                f"Suhu GPU {gpu_temp}. "
                f"RAM {data['ram']} persen. "
                f"Disk {data['disk']} persen. "
                f"Baterai {data['battery']}."
            )

        cpu_temperature_sentence = ""

        if data["cpu_temp_text"]:
            cpu_temperature_sentence = (
                f"CPU temperature {data['cpu_temp_text']}. "
            )

        return (
            f"System status, Sir. "
            f"CPU {data['cpu_name']}, usage {data['cpu']} percent. "
            f"{cpu_temperature_sentence}"
            f"GPU {data['gpu_name']}, usage {data['gpu']} percent. "
            f"GPU temperature {data['gpu_temp_text']}. "
            f"RAM {data['ram']} percent. "
            f"Disk {data['disk']} percent. "
            f"Battery {data['battery']}."
        )

    def temperature_text(self, value, language):
        if not value:
            if language == "id":
                return "tidak tersedia"

            return "not available"

        return value

    def format_gpu_list(self, gpus):
        names = []

        for gpu in gpus:
            name = gpu.get("Name")

            if name:
                names.append(name)

        if not names:
            return "N/A"

        return ", ".join(names)

    def format_disk_list(self, disks):
        names = []

        for disk in disks:
            name = disk.get("FriendlyName", "Disk")
            size = disk.get("Size") or 0
            media = disk.get("MediaType", "")
            size_gb = round(int(size) / (1000 ** 3)) if size else 0

            if size_gb:
                names.append(f"{name} {size_gb} GB {media}".strip())
            else:
                names.append(name)

        if not names:
            return "N/A"

        return ", ".join(names)

    def get_laptop_status(self, language, data):
        specs = data["specs"]
        model = f"{specs['manufacturer']} {specs['model']}".strip()
        cpu_clock = specs["cpu_max_clock_mhz"]
        cpu_clock_text = (
            f"{round(int(cpu_clock) / 1000, 1)} GHz"
            if str(cpu_clock).isdigit()
            else f"{cpu_clock} MHz"
        )
        gpu_text = self.format_gpu_list(specs["gpus"])
        disk_text = self.format_disk_list(specs["disks"])

        if language == "id":
            gpu_temp = self.temperature_text(data["gpu_temp_text"], language)
            temperature_sentence = f"Suhu GPU {gpu_temp}."

            if data["cpu_temp_text"]:
                temperature_sentence = (
                    f"Suhu CPU {data['cpu_temp_text']}, suhu GPU {gpu_temp}."
                )

            return (
                f"Status laptop. Model {model}. "
                f"CPU {specs['cpu_name']}, {specs['cpu_cores']} core, "
                f"{specs['cpu_threads']} thread, hingga {cpu_clock_text}. "
                f"GPU {gpu_text}. "
                f"RAM total {specs['ram_total_gb']} GB, penggunaan saat ini {data['ram']} persen. "
                f"Disk {disk_text}, penggunaan drive C {data['disk']} persen. "
                f"Baterai {data['battery']}, daya {data['charging']}. "
                f"{temperature_sentence}"
            )

        temperature_sentence = f"GPU temperature {data['gpu_temp_text']}."

        if data["cpu_temp_text"]:
            temperature_sentence = (
                f"CPU temperature {data['cpu_temp_text']}, "
                f"GPU temperature {data['gpu_temp_text']}."
            )

        return (
            f"Laptop status. Model {model}. "
            f"CPU {specs['cpu_name']}, {specs['cpu_cores']} cores, "
            f"{specs['cpu_threads']} threads, up to {cpu_clock_text}. "
            f"GPU {gpu_text}. "
            f"Total RAM {specs['ram_total_gb']} GB, current usage {data['ram']} percent. "
            f"Disk {disk_text}, C drive usage {data['disk']} percent. "
            f"Battery {data['battery']}, power {data['charging']}. "
            f"{temperature_sentence}"
        )

    def get_battery_status(self, language="en"):
        data = self.monitor.get_status()
        battery = data["battery"]
        power = data["charging"]

        if language == "id":
            return f"Baterai {battery}. Daya: {power}."

        return f"Battery {battery}. Power: {power}."

    def get_us_president(self, language="en"):
        try:
            response = requests.get(
                "https://www.whitehouse.gov/administration/",
                timeout=12,
                headers={
                    "User-Agent": "NOVA Desktop Assistant"
                }
            )
            response.raise_for_status()
            html = response.text

            candidates = [
                "Donald J. Trump",
                "Joseph R. Biden",
                "Joe Biden",
            ]
            president = ""

            for candidate in candidates:
                if candidate in html:
                    president = candidate
                    break

            if not president:
                if language == "id":
                    return "Saya belum bisa membaca data presiden Amerika dari sumber resmi."

                return "I could not read the current U.S. president from the official source."

            if language == "id":
                return f"Presiden Amerika Serikat saat ini adalah {president}."

            return f"The current president of the United States is {president}."
        except Exception:
            if language == "id":
                return "Saya belum bisa mengambil data presiden Amerika saat ini."

            return "I could not get the current U.S. president right now."

    def extract_currency_pair(self, command_text):
        command = command_text.lower()
        aliases = {
            "usd": ["usd", "dollar", "dolar", "dolar amerika", "dollar amerika"],
            "eur": ["eur", "euro"],
            "idr": ["idr", "rupiah"],
            "jpy": ["jpy", "yen"],
            "gbp": ["gbp", "pound", "poundsterling"],
            "sgd": ["sgd", "dolar singapura", "singapore dollar"],
            "aud": ["aud", "dolar australia", "australian dollar"],
            "cny": ["cny", "yuan", "renminbi"],
        }
        found = []

        for code, words in aliases.items():
            if any(word in command for word in words):
                found.append(code.upper())

        from_currency = found[0] if found else "USD"
        to_currency = "IDR"

        if "terhadap" in command or "ke " in command or "to " in command:
            for code, words in aliases.items():
                if code.upper() == from_currency:
                    continue

                if any(word in command for word in words):
                    to_currency = code.upper()

        if from_currency == to_currency:
            to_currency = "IDR" if from_currency != "IDR" else "USD"

        return from_currency, to_currency

    def format_money(self, amount, currency):
        if currency == "IDR":
            return f"Rp{amount:,.0f}".replace(",", ".")

        return f"{currency} {amount:,.2f}"

    def clean_html_text(self, value):
        value = re.sub(r"<[^>]+>", "", value)
        value = unescape(value)
        value = value.replace("\xa0", " ")
        return " ".join(value.split()).strip()

    def clean_rate_value(self, value):
        return re.sub(r"\s*\([^)]*\)", "", value).strip()

    def parse_indonesian_number(self, value):
        cleaned = self.clean_rate_value(value)
        cleaned = cleaned.replace(".", "").replace(",", ".")
        return float(cleaned)

    def format_indonesian_rate(self, value):
        return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    def extract_kursdollar_row(self, html, currency):
        pattern = (
            rf"change_chart_details\('{re.escape(currency)}','[^']+'\).*?</tr>"
        )
        match = re.search(pattern, html, flags=re.IGNORECASE | re.DOTALL)

        if not match:
            return None

        row = match.group(0)
        cells = re.findall(r"<td[^>]*>(.*?)</td>", row, flags=re.DOTALL)

        if len(cells) < 5:
            return None

        return {
            "currency": currency,
            "buy": self.clean_rate_value(self.clean_html_text(cells[1])),
            "sell": self.clean_rate_value(self.clean_html_text(cells[2])),
            "middle": self.clean_rate_value(self.clean_html_text(cells[3])),
            "spot": self.clean_html_text(cells[4]),
        }

    def extract_kursdollar_date(self, html):
        title = re.search(
            r"Kurs Dollar Hari Ini\s*-\s*([^<]+)",
            html,
            flags=re.IGNORECASE
        )
        bi_time = re.search(
            r"Bank Indonesia</a>\s*-\s*([^<]+)</td>",
            html,
            flags=re.IGNORECASE
        )

        date_text = self.clean_html_text(title.group(1)) if title else "hari ini"
        bi_text = self.clean_html_text(bi_time.group(1)) if bi_time else ""

        return date_text, bi_text

    def extract_bi_row(self, html, currency):
        row_pattern = r"<tr>\s*(.*?)\s*</tr>"

        for match in re.finditer(row_pattern, html, flags=re.IGNORECASE | re.DOTALL):
            row = match.group(1)
            cells = re.findall(r"<td[^>]*>(.*?)</td>", row, flags=re.DOTALL)

            if len(cells) < 4:
                continue

            code = self.clean_html_text(cells[0]).upper()

            if code != currency:
                continue

            return {
                "currency": currency,
                "value": self.clean_html_text(cells[1]),
                "sell": self.clean_rate_value(self.clean_html_text(cells[2])),
                "buy": self.clean_rate_value(self.clean_html_text(cells[3])),
            }

        return None

    def extract_bi_date(self, html):
        match = re.search(
            r"Update Terakhir\s*&nbsp;<span>([^<]+)</span>",
            html,
            flags=re.IGNORECASE
        )

        if match:
            return self.clean_html_text(match.group(1))

        return "hari ini"

    def get_middle_rate(self, language="en", command_text="", source="kursdollar"):
        from_currency, to_currency = self.extract_currency_pair(command_text)

        if to_currency != "IDR":
            to_currency = "IDR"

        if from_currency == "IDR":
            from_currency = "USD"

        if source == "bi":
            return self.get_middle_rate_bi(language, from_currency)

        return self.get_middle_rate_kursdollar(language, from_currency)

    def get_middle_rate_kursdollar(self, language="en", from_currency="USD"):
        try:
            response = requests.get(
                "https://kursdollar.org/",
                timeout=12,
                headers={
                    "User-Agent": "NOVA Desktop Assistant"
                }
            )
            response.raise_for_status()
            html = response.text
            row = self.extract_kursdollar_row(html, from_currency)

            if not row:
                raise ValueError("Currency row not found.")

            date_text, bi_text = self.extract_kursdollar_date(html)
            source_time = f" Data BI {bi_text}." if bi_text else ""

            if language == "id":
                return (
                    f"Kurs tengah {from_currency} terhadap rupiah di kursdollar.org "
                    f"untuk {date_text}: 1 {from_currency} sekitar Rp{row['middle']}."
                    f"{source_time} Kurs beli Rp{row['buy']}, kurs jual Rp{row['sell']}."
                )

            return (
                f"The {from_currency} middle rate against IDR on kursdollar.org "
                f"for {date_text} is about Rp{row['middle']} for 1 {from_currency}. "
                f"Buy rate Rp{row['buy']}, sell rate Rp{row['sell']}."
            )
        except requests.exceptions.Timeout:
            if language == "id":
                return "Saya belum bisa mengambil kurs tengah karena situs kurs sedang lambat."

            return "I could not get the middle rate because the exchange rate site is taking too long."
        except requests.exceptions.RequestException:
            if language == "id":
                return "Saya belum bisa mengambil kurs tengah karena koneksi ke situs kurs bermasalah."

            return "I could not get the middle rate because the exchange rate site connection failed."
        except Exception:
            if language == "id":
                return f"Saya belum bisa mengambil kurs tengah {from_currency} saat ini."

            return f"I could not get the {from_currency} middle rate right now."

    def get_middle_rate_bi(self, language="en", from_currency="USD"):
        try:
            response = requests.get(
                "https://www.bi.go.id/id/statistik/informasi-kurs/transaksi-bi/default.aspx",
                timeout=25,
                headers={
                    "User-Agent": "NOVA Desktop Assistant"
                }
            )
            response.raise_for_status()
            html = response.text
            row = self.extract_bi_row(html, from_currency)

            if not row:
                raise ValueError("Currency row not found.")

            sell = self.parse_indonesian_number(row["sell"])
            buy = self.parse_indonesian_number(row["buy"])
            middle = (sell + buy) / 2
            middle_text = self.format_indonesian_rate(middle)
            date_text = self.extract_bi_date(html)
            value_text = row["value"]

            if language == "id":
                return (
                    f"Kurs tengah BI {from_currency} terhadap rupiah untuk {date_text}: "
                    f"{value_text} {from_currency} sekitar Rp{middle_text}. "
                    f"Perhitungan dari kurs jual Rp{row['sell']} ditambah kurs beli Rp{row['buy']}, lalu dibagi dua."
                )

            return (
                f"The BI middle rate for {from_currency} against IDR on {date_text} is about "
                f"Rp{middle_text} for {value_text} {from_currency}. "
                f"It is calculated from sell rate Rp{row['sell']} plus buy rate Rp{row['buy']}, divided by two."
            )
        except requests.exceptions.Timeout:
            if language == "id":
                return "Saya belum bisa mengambil kurs tengah BI karena situs BI sedang lambat."

            return "I could not get the BI middle rate because the BI site is taking too long."
        except requests.exceptions.RequestException:
            if language == "id":
                return "Saya belum bisa mengambil kurs tengah BI karena koneksi ke situs BI bermasalah."

            return "I could not get the BI middle rate because the BI site connection failed."
        except Exception:
            if language == "id":
                return f"Saya belum bisa mengambil kurs tengah BI {from_currency} saat ini."

            return f"I could not get the BI {from_currency} middle rate right now."

    def get_currency_rate(self, language="en", command_text=""):
        from_currency, to_currency = self.extract_currency_pair(command_text)

        try:
            rate = None

            try:
                response = requests.get(
                    f"https://open.er-api.com/v6/latest/{from_currency}",
                    timeout=8,
                    headers={
                        "User-Agent": "NOVA Desktop Assistant"
                    }
                )
                response.raise_for_status()
                data = response.json()

                if data.get("result") == "success":
                    rate = data.get("rates", {}).get(to_currency)
            except requests.exceptions.RequestException:
                rate = None

            if not rate:
                response = requests.get(
                    "https://api.frankfurter.app/latest",
                    params={
                        "from": from_currency,
                        "to": to_currency,
                    },
                    timeout=8,
                    headers={
                        "User-Agent": "NOVA Desktop Assistant"
                    }
                )
                response.raise_for_status()
                data = response.json()
                rate = data.get("rates", {}).get("IDR")

            if not rate:
                raise ValueError("Exchange rate is unavailable.")

            rate_text = self.format_money(float(rate), to_currency)
            wants_sell_rate = "harga jual" in command_text.lower()

            if language == "id":
                note = (
                    " Ini kurs indikatif pasar, jadi harga jual bank atau money changer "
                    "bisa sedikit berbeda."
                )
                opening = (
                    f"Harga jual {from_currency} biasanya mengacu ke kurs jual penyedia"
                )

                if not wants_sell_rate:
                    opening = (
                        f"Kurs indikatif {from_currency} ke {to_currency} saat ini"
                    )

                return (
                    f"{opening}: 1 {from_currency} sekitar {rate_text}."
                    f"{note}"
                )

            return (
                f"The indicative {from_currency} to {to_currency} rate is about {rate_text} for 1 {from_currency}. "
                f"Bank sell rates may be slightly different."
            )
        except requests.exceptions.Timeout:
            if language == "id":
                return "Saya belum bisa mengambil kurs karena layanan kurs sedang lambat. Coba lagi sebentar lagi."

            return "I could not get the exchange rate because the exchange rate service is taking too long."
        except requests.exceptions.RequestException:
            if language == "id":
                return "Saya belum bisa mengambil kurs karena koneksi ke layanan kurs bermasalah."

            return "I could not get the exchange rate because the exchange rate service connection failed."
        except Exception:
            if language == "id":
                return "Saya belum bisa mengambil kurs saat ini."

            return "I could not get the exchange rate right now."

    def extract_crypto_id(self, command_text):
        command = command_text.lower()
        aliases = {
            "bitcoin": ["bitcoin", "btc"],
            "ethereum": ["ethereum", "etherium", "eth"],
            "solana": ["solana", "sol"],
            "binancecoin": ["bnb", "binance"],
            "ripple": ["xrp", "ripple"],
            "dogecoin": ["dogecoin", "doge"],
        }

        for coin_id, words in aliases.items():
            if any(word in command for word in words):
                return coin_id

        return "bitcoin"

    def get_crypto_price(self, language="en", command_text=""):
        coin_id = self.extract_crypto_id(command_text)

        try:
            response = requests.get(
                "https://api.coingecko.com/api/v3/simple/price",
                params={
                    "ids": coin_id,
                    "vs_currencies": "usd,idr",
                    "include_24hr_change": "true",
                },
                timeout=10,
                headers={
                    "User-Agent": "NOVA Desktop Assistant"
                }
            )
            response.raise_for_status()
            data = response.json().get(coin_id, {})
            usd = data.get("usd")
            idr = data.get("idr")
            change = data.get("usd_24h_change")

            if usd is None and idr is None:
                raise ValueError("Crypto price is unavailable.")

            coin_name = coin_id.replace("binancecoin", "BNB").title()
            idr_text = self.format_money(float(idr), "IDR") if idr else "N/A"
            usd_text = self.format_money(float(usd), "USD") if usd else "N/A"
            change_text = ""

            if change is not None:
                change_text = f" Perubahan 24 jam sekitar {float(change):.1f} persen."

            if language == "id":
                return (
                    f"Harga {coin_name} saat ini sekitar {idr_text}, "
                    f"atau {usd_text}.{change_text} "
                    "Ini harga indikatif pasar dan bisa berubah cepat."
                )

            return (
                f"{coin_name} is about {idr_text}, or {usd_text} right now. "
                "This is an indicative market price and can change quickly."
            )
        except requests.exceptions.Timeout:
            if language == "id":
                return "Saya belum bisa mengambil harga crypto karena layanan market sedang lambat."

            return "I could not get the crypto price because the market service is taking too long."
        except requests.exceptions.RequestException:
            if language == "id":
                return "Saya belum bisa mengambil harga crypto karena koneksi ke layanan market bermasalah."

            return "I could not get the crypto price because the market service connection failed."
        except Exception:
            if language == "id":
                return "Saya belum bisa mengambil harga crypto saat ini."

            return "I could not get the crypto price right now."

    def extract_weather_location(self, command_text, language="en"):
        text = command_text.lower().strip()
        text = text.replace("gimana", "bagaimana")

        markers = [
            "bagaimana cuaca di",
            "gimana cuaca di",
            "cuaca hari ini di",
            "cuaca sekarang di",
            "cuaca di",
            "cuaca untuk",
            "di",
            "weather today in",
            "weather now in",
            "weather in",
            "weather for",
        ]

        for marker in markers:
            if marker == "di" and not text.startswith("di "):
                continue

            if marker in text:
                location = text.split(marker, 1)[1].strip(" .?!,")
                if location:
                    return self.clean_weather_location(location)

        if (
            language == "id" and
            text.startswith("di") and
            not text.startswith("dimana") and
            ("hari ini" in text or "sekarang" in text)
        ):
            return self.clean_weather_location(text[2:])

        if language == "id" and (
            "hari ini" in text or
            "sekarang" in text
        ):
            return self.clean_weather_location(text)

        if language == "id":
            return "Jakarta"

        return "Jakarta"

    def clean_weather_location(self, location):
        location = location.lower().strip(" .?!,")
        fillers = [
            "hari ini",
            "sekarang",
            "today",
            "now",
            "please",
            "tolong",
        ]

        for filler in fillers:
            location = location.replace(filler, "")

        location = " ".join(location.split()).strip(" .?!,")

        if not location:
            return "Jakarta"

        return location

    def get_weather(self, language="en", command_text=""):
        location = self.extract_weather_location(command_text, language)

        try:
            geo_response = requests.get(
                "https://geocoding-api.open-meteo.com/v1/search",
                params={
                    "name": location,
                    "count": 1,
                    "language": "id" if language == "id" else "en",
                    "format": "json",
                },
                timeout=15
            )
            geo_response.raise_for_status()
            geo_data = geo_response.json()
            results = geo_data.get("results") or []

            if not results:
                if language == "id":
                    return f"Saya belum menemukan lokasi {location}."

                return f"I could not find {location}."

            place = results[0]
            latitude = place["latitude"]
            longitude = place["longitude"]
            area_name = place.get("name", location.title())
            country = place.get("country", "")

            weather_response = requests.get(
                "https://api.open-meteo.com/v1/forecast",
                params={
                    "latitude": latitude,
                    "longitude": longitude,
                    "current": (
                        "temperature_2m,"
                        "relative_humidity_2m,"
                        "apparent_temperature,"
                        "weather_code"
                    ),
                    "timezone": "auto",
                },
                timeout=15
            )
            weather_response.raise_for_status()
            current = weather_response.json()["current"]

            temp_c = round(current["temperature_2m"])
            feels_c = round(current["apparent_temperature"])
            humidity = current["relative_humidity_2m"]
            description = self.describe_weather(
                current["weather_code"],
                language
            )

            if language == "id":
                return (
                    f"Cuaca di {area_name}: {description}. "
                    f"Suhu {temp_c} derajat, terasa seperti {feels_c} derajat. "
                    f"Kelembapan {humidity} persen."
                )

            return (
                f"Weather in {area_name}, {country}: {description}. "
                f"Temperature {temp_c} degrees, feels like {feels_c}. "
                f"Humidity {humidity} percent."
            )
        except requests.exceptions.Timeout:
            fallback = self.get_weather_fallback(location, language)
            if fallback:
                return fallback

            if language == "id":
                return "Saya belum bisa mengambil data cuaca karena layanan cuaca sedang lambat. Coba lagi sebentar lagi."

            return "I could not get the weather data because the weather service is taking too long. Please try again in a moment."
        except requests.exceptions.RequestException:
            fallback = self.get_weather_fallback(location, language)
            if fallback:
                return fallback

            if language == "id":
                return "Saya belum bisa mengambil data cuaca karena koneksi ke layanan cuaca bermasalah."

            return "I could not get the weather data because the weather service connection failed."
        except Exception:
            if language == "id":
                return "Saya belum bisa mengambil data cuaca saat ini."

            return "I could not get the weather data right now."

    def get_weather_fallback(self, location, language="en"):
        try:
            response = requests.get(
                f"https://wttr.in/{location}",
                params={
                    "format": "j1",
                },
                timeout=8,
                headers={
                    "User-Agent": "NOVA Desktop Assistant"
                }
            )
            response.raise_for_status()
            data = response.json()
            current = data["current_condition"][0]
            temp_c = round(float(current["temp_C"]))
            feels_c = round(float(current["FeelsLikeC"]))
            humidity = current["humidity"]
            description = current["weatherDesc"][0]["value"].lower()
            area_name = location.title()

            if language == "id":
                return (
                    f"Cuaca di {area_name}: {description}. "
                    f"Suhu {temp_c} derajat, terasa seperti {feels_c} derajat. "
                    f"Kelembapan {humidity} persen."
                )

            return (
                f"Weather in {area_name}: {description}. "
                f"Temperature {temp_c} degrees, feels like {feels_c}. "
                f"Humidity {humidity} percent."
            )
        except Exception:
            return ""

    def describe_weather(self, code, language="en"):
        descriptions = {
            0: ("cerah", "clear"),
            1: ("sebagian cerah", "mainly clear"),
            2: ("berawan sebagian", "partly cloudy"),
            3: ("mendung", "overcast"),
            45: ("berkabut", "foggy"),
            48: ("kabut beku", "rime fog"),
            51: ("gerimis ringan", "light drizzle"),
            53: ("gerimis sedang", "moderate drizzle"),
            55: ("gerimis lebat", "dense drizzle"),
            61: ("hujan ringan", "light rain"),
            63: ("hujan sedang", "moderate rain"),
            65: ("hujan lebat", "heavy rain"),
            80: ("hujan lokal ringan", "light showers"),
            81: ("hujan lokal sedang", "moderate showers"),
            82: ("hujan lokal lebat", "violent showers"),
            95: ("badai petir", "thunderstorm"),
            96: ("badai petir dengan hujan es ringan", "thunderstorm with hail"),
            99: ("badai petir dengan hujan es lebat", "thunderstorm with heavy hail"),
        }
        default = ("tidak diketahui", "unknown")
        pair = descriptions.get(code, default)

        if language == "id":
            return pair[0]

        return pair[1]

    def shutdown_laptop(self, language="en"):
        subprocess.Popen(
            ["shutdown", "/s", "/t", "5"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        if language == "id":
            return "Mematikan laptop dalam lima detik."

        return "Shutting down the laptop in five seconds, Sir."

    def restart_laptop(self, language="en"):
        subprocess.Popen(
            ["shutdown", "/r", "/t", "5"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        if language == "id":
            return "Restart laptop dalam lima detik."

        return "Restarting the laptop in five seconds, Sir."

    def sleep_laptop(self, language="en"):
        subprocess.Popen(
            ["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        if language == "id":
            return "Membuat laptop masuk mode sleep."

        return "Putting the laptop to sleep, Sir."
