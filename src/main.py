from core.boot import boot
from core.assistant import Assistant
from core.command import CommandEngine
from core.brain import Brain
from core.speaker import Speaker


# Boot System
boot()


# Initialize Modules
jarvis = Assistant("JARVIS")
engine = CommandEngine()
brain = Brain()
speaker = Speaker()


# Startup Message
startup_message = "System Online."

jarvis.say(startup_message)
speaker.speak(startup_message)

welcome_message = "Type a command, ask a question, or type exit."

jarvis.say(welcome_message)
speaker.speak(welcome_message)


# Main Loop
while True:

    user = input("You : ")

    if user.lower() == "exit":
        goodbye = "Shutting down session."

        jarvis.say(goodbye)
        speaker.speak(goodbye)
        break

    response = engine.execute(user)

    if response == "Command not recognized.":
        response = brain.ask(user)

    jarvis.say(response)
    speaker.speak(response)