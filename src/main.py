from core.boot import boot
from core.assistant import Assistant

boot()

jarvis = Assistant("JARVIS")

jarvis.say("System Online.")
jarvis.say("Good evening, Alto.")