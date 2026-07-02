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
        ]

        self.exit_commands = [
            "exit",
            "quit",
            "shutdown",
            "shut down",
            "goodbye",
            "bye jarvis",
            "turn off jarvis",
        ]

    def clean(self, text):
        return text.lower().replace(",", "").replace(".", "").strip()

    def route(self, text):
        command = self.clean(text)

        if any(item in command for item in self.exit_commands):
            return {
                "type": "exit",
                "message": "Goodbye, Sir."
            }

        if any(item in command for item in self.stop_commands):
            return {
                "type": "stop",
                "message": "Listening paused."
            }

        return {
            "type": "chat",
            "message": text
        }