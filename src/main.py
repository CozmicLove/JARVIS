from core.boot import boot
from core.assistant import Assistant
from core.command import CommandEngine

boot()

jarvis = Assistant("JARVIS")
engine = CommandEngine()

jarvis.say("System Online.")
jarvis.say("Type a command. Example: hello, status, or exit.")

while True:
    user_command = input("You : ")

    if user_command.lower() == "exit":
        jarvis.say("Shutting down session.")
        break

    response = engine.execute(user_command)
    jarvis.say(response)