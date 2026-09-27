import os
import requests
import re


class OnlineTools:

    def __init__(self):
        base = os.path.dirname(os.path.dirname(__file__))
        project_root = os.path.dirname(base)
        self.env_file = os.path.join(project_root, ".env")
        self.load_env_file()
        self.tavily_api_key = os.getenv("TAVILY_API_KEY", "").strip()
        self.tavily_url = "https://api.tavily.com/search"

    def load_env_file(self):
        if not os.path.exists(self.env_file):
            return

        try:
            with open(self.env_file, "r", encoding="utf-8") as file:
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

    def search(self, query, language="id"):
        query = self.clean_query(query)

        if not self.tavily_api_key:
            if language == "id":
                return {
                    "ok": False,
                    "error": "TAVILY_API_KEY belum diset.",
                    "query": query,
                }

            return {
                "ok": False,
                "error": "TAVILY_API_KEY is not set.",
                "query": query,
            }

        payload = {
            "query": query,
            "topic": "general",
            "search_depth": "basic",
            "max_results": 5,
            "include_answer": True,
            "include_raw_content": False,
        }
        headers = {
            "Authorization": f"Bearer {self.tavily_api_key}",
            "Content-Type": "application/json",
        }

        try:
            response = requests.post(
                self.tavily_url,
                json=payload,
                headers=headers,
                timeout=15
            )
            response.raise_for_status()
            data = response.json()
            results = data.get("results") or []

            return {
                "ok": True,
                "query": query,
                "answer": data.get("answer", ""),
                "results": [
                    {
                        "title": item.get("title", ""),
                        "url": item.get("url", ""),
                        "content": item.get("content", ""),
                    }
                    for item in results[:5]
                ],
            }
        except requests.exceptions.Timeout:
            return {
                "ok": False,
                "error": "Pencarian online terlalu lama." if language == "id" else "Online search timed out.",
                "query": query,
            }
        except requests.exceptions.RequestException as error:
            return {
                "ok": False,
                "error": f"Pencarian online gagal: {error}" if language == "id" else f"Online search failed: {error}",
                "query": query,
            }

    def clean_query(self, query):
        text = (query or "").strip(" .?!,")

        replacements = [
            "bagaimana kamu cari tahu lebih dalam tentang",
            "gimana kamu cari tahu lebih dalam tentang",
            "bagaimana cari tahu lebih dalam tentang",
            "gimana cari tahu lebih dalam tentang",
            "saya mau tahu lebih dalam tentang",
            "saya ingin tahu lebih dalam tentang",
            "saya tahu lebih dalam tentang",
            "cari informasi lebih dalam tentang",
            "cari tahu lebih dalam tentang",
            "coba kamu gali lebih dalam tentang",
            "coba gali lebih dalam tentang",
            "gali lebih dalam tentang",
            "bahas lebih dalam tentang",
            "lebih dalam tentang",
            "jelaskan lebih dalam tentang",
            "coba kamu cari tahu tentang",
            "coba cari tahu tentang",
            "tolong cari tahu tentang",
            "cari tahu tentang",
            "apa yang kamu tahu tentang",
            "apa yang anda tahu tentang",
            "apa yang kau tahu tentang",
            "apa itu",
            "siapa itu",
            "tentang",
        ]

        for replacement in replacements:
            text = re.sub(
                rf"(?<!\w){re.escape(replacement)}(?!\w)",
                " ",
                text,
                flags=re.IGNORECASE,
            )

        corrections = {
            "adirai": "Ade Rai",
            "aderai": "Ade Rai",
            "ade rai": "Ade Rai",
            "hyundai kereta": "Hyundai Creta",
            "hyundai kerta": "Hyundai Creta",
            "hyundai kreta": "Hyundai Creta",
            "hyundai creta": "Hyundai Creta",
        }

        for source, replacement in corrections.items():
            text = re.sub(
                rf"(?<!\w){re.escape(source)}(?!\w)",
                replacement,
                text,
                flags=re.IGNORECASE,
            )

        return " ".join(text.split()).strip(" .?!,") or query

    def format_context(self, data):
        lines = []

        if data.get("answer"):
            lines.append(f"Search summary: {data['answer']}")

        for index, item in enumerate(data.get("results", []), start=1):
            title = item.get("title", "").strip()
            url = item.get("url", "").strip()
            content = item.get("content", "").strip()

            if title or content:
                lines.append(
                    f"{index}. {title}\nURL: {url}\nSnippet: {content}"
                )

        return "\n\n".join(lines).strip()
