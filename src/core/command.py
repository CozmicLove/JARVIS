from plugins import hello
from plugins import status


class CommandEngine:

    def execute(self, command):

        command = command.lower()

        if command == "hello":
            return hello.run()

        elif command == "status":
            return status.run()

        else:
            return "Command not recognized."