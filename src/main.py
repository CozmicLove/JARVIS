from core.listener import Listener
from core.speaker import Speaker
from core.brain import Brain

listener = Listener()
speaker = Speaker()
brain = Brain()

WAKE_WORDS = [
    "jarvis",
    "hey jarvis",
    "okay jarvis",
    "ok jarvis",
    "hi jarvis",
    "jervis",
    "garvis",
    "garfish",
    "service"
]

EXIT_WORDS = [
    "exit",
    "quit",
    "shutdown",
    "goodbye",
    "bye"
]

STOP_WORDS = [
    "stop listening",
    "go to sleep",
    "sleep",
    "stand by",
    "standby"
]


def contains(text, words):
    text = text.lower()
    return any(word in text for word in words)


def remove_wake_word(text):
    result = text

    for word in WAKE_WORDS:
        result = result.replace(word, "")

    return result.strip(" ,.!?")


print()
print("=" * 60)
print("JARVIS READY")
print("=" * 60)

speaker.speak("Systems online, Sir.")

sleeping = True

while True:

    if sleeping:
        print()
        print("Sleeping... say 'Jarvis' to activate.")

        text = listener.listen()

        if not text:
            continue

        print()
        print("Heard :", text)

        if contains(text, EXIT_WORDS):
            speaker.speak("Goodbye Sir.")
            break

        if contains(text, WAKE_WORDS):

            command = remove_wake_word(text)

            if command == "":
                speaker.speak("Yes Sir?")
                sleeping = False
                continue

            text = command

        else:
            continue

    else:

        text = listener.listen()

        if not text:
            continue

        print()
        print("Heard :", text)

        if contains(text, EXIT_WORDS):
            speaker.speak("Goodbye Sir.")
            break

        if contains(text, STOP_WORDS):
            speaker.speak("Standing by.")
            sleeping = True
            continue

    print()
    print("Thinking...")

    answer = brain.ask(text)

    print()
    print("JARVIS :", answer)

    print()
    print("Speaking...")

    speaker.speak(answer)

    sleeping = True