import importlib.util
from pathlib import Path


class PluginLoader:

    def __init__(self, plugins_folder="plugins"):
        project_root = Path(__file__).resolve().parents[2]
        self.plugins_folder = Path(plugins_folder)

        if not self.plugins_folder.is_absolute():
            self.plugins_folder = project_root / self.plugins_folder

        self.plugins = {}
        self.errors = {}

    def load_plugins(self):
        self.plugins = {}
        self.errors = {}

        if not self.plugins_folder.exists():
            return self.plugins

        for plugin_file in self.plugins_folder.glob("*.py"):
            if plugin_file.name == "__init__.py":
                continue

            plugin_name = plugin_file.stem

            try:
                spec = importlib.util.spec_from_file_location(
                    plugin_name,
                    plugin_file
                )

                if spec is None or spec.loader is None:
                    self.errors[plugin_name] = "Plugin spec could not be loaded."
                    continue

                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                if hasattr(module, "run") and callable(module.run):
                    self.plugins[plugin_name] = module.run
                else:
                    self.errors[plugin_name] = "Plugin has no callable run function."
            except Exception as error:
                self.errors[plugin_name] = str(error)

        return self.plugins
