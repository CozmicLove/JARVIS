from core.plugin_loader import PluginLoader


class CommandEngine:

    def __init__(self):
        loader = PluginLoader()
        self.plugins = loader.load_plugins()

    def execute(self, command):
        command = command.lower()

        if command in self.plugins:
            return self.plugins[command]()

        return "Command not recognized."