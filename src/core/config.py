import json


def load_settings():
    with open("config/settings.json", "r", encoding="utf-8") as file:
        return json.load(file)