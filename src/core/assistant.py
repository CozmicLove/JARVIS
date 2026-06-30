class Assistant:

    def __init__(self, name):
        self.name = name

    def say(self, message):
        print(f"{self.name} : {message}")