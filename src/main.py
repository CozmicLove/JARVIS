from core.runtime import NovaRuntime


def print_status(status):
    if status == "STANDBY":
        print()
        print("Standby... listening for command.")
    elif status == "SLEEPING":
        print()
        print("Sleeping... say 'wake up' to activate.")
    elif status == "THINKING":
        print()
        print("Thinking...")
    elif status == "SPEAKING":
        print()
        print("Speaking...")


def print_heard(text):
    print()
    print("Heard :", text)


def print_answer(answer):
    print()
    print("NOVA :", answer)


print()
print("=" * 60)
print("NOVA READY")
print("=" * 60)

runtime = NovaRuntime()
runtime.run(
    callbacks={
        "status": print_status,
        "heard": print_heard,
        "answer": print_answer,
    }
)
