import importlib.util
from pathlib import Path


class PluginLoader:

    def __init__(self, plugins_folder="plugins"):
        self.plugins_folder = Path(plugins_folder)
        self.plugins = {}

    def load_plugins(self):
        for plugin_file in self.plugins_folder.glob("*.py"):
            if plugin_file.name == "__init__.py":
                continue

            plugin_name = plugin_file.stem
            spec = importlib.util.spec_from_file_location(plugin_name, plugin_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            if hasattr(module, "run"):
                self.plugins[plugin_name] = module.run

        return self.plugins