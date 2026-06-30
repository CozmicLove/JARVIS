class CommandEngine:

    def execute(self, command):

        command = command.lower()

        if command == "hello":
            return "Hello Alfred."

        elif command == "status":
            return "All systems operational."

        else:
            return "Command not recognized."