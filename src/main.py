from core.brain import Brain
from core.speaker import Speaker
from core.listener import Listener


def print_banner():
    print("\n" + "=" * 70)
    print(" " * 27 + "JARVIS READY")
    print("=" * 70 + "\n")


def main():

    brain = Brain()
    speaker = Speaker()
    listener = Listener()

    print_banner()

    speaker.speak("Hello Alfred. I am Jarvis. Systems online.")

    while True:

        print()
        print("Type your message or type LISTEN to use your microphone.")
        user = input("You : ").strip()

        if not user:
            continue

        if user.lower() == "listen":

            user = listener.listen()

            print(f"\nYou said : {user}")

            if not user:
                continue

        if user.lower() in ["exit", "quit", "bye"]:

            speaker.speak("Goodbye Alfred.")
            print("JARVIS : Goodbye Alfred.")
            break

        try:

            response = brain.ask(user)

        except Exception as error:

            response = f"Sorry, something went wrong. {error}"

        print(f"\nJARVIS : {response}")

        speaker.speak(response)


if __name__ == "__main__":
    main()