from core.boot import boot
from core.assistant import Assistant
from core.command import CommandEngine

boot()

jarvis = Assistant("JARVIS")
engine = CommandEngine()

jarvis.say(engine.execute("hello"))
jarvis.say(engine.execute("status"))