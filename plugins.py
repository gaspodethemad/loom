
import os
import json
import importlib

import metaprocess


class BasePlugin:
    def __init__(self, manifest):
        self.manifest = manifest

    def load(self):
        """Load the plugin."""
        pass

    def unload(self):
        """Unload the plugin."""
        pass

    @property
    def name(self):
        return self.manifest.get("name")

    @property
    def author(self):
        return self.manifest.get("author")
    
    @property
    def version(self):
        return self.manifest.get("version")


class PluginManager:
    def __init__(self, plugin_dir):
        self.plugin_dir = plugin_dir
        self.plugins = {}  # Maps plugin names to plugin instances
        self.plugin_states = {}  # Maps plugin names to their load state
        metaprocess.plugin_manager = self

    def list_plugins(self):
        """List all plugins and their manifests."""
        plugins = []
        for dirname in os.listdir(self.plugin_dir):
            plugin_path = os.path.join(self.plugin_dir, dirname)
            if os.path.isdir(plugin_path):
                manifest_path = os.path.join(plugin_path, "manifest.json")
                if os.path.isfile(manifest_path):
                    with open(manifest_path, 'r') as f:
                        manifest = json.load(f)
                        plugins.append((dirname, manifest, self.plugin_states.get(dirname, False)))
        return plugins

    def load_plugin(self, plugin_name):
        """Load a plugin by name."""
        # indempotence check
        if self.plugin_states.get(plugin_name, False):
            print(f"Plugin {plugin_name} is already loaded.")
            return False
        plugin_path = os.path.join(self.plugin_dir, plugin_name, "plugin.py")
        module_path = f"{self.plugin_dir}.{plugin_name}.plugin"
        manifest_path = os.path.join(self.plugin_dir, plugin_name, "manifest.json")
        if os.path.isfile(plugin_path) and os.path.isfile(manifest_path):
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)
            print(f"=== Loading plugin {plugin_name} v{manifest.get('version')} by {manifest.get('author')} ===")
            # Import and instantiate the plugin
            plugin_module = importlib.import_module(module_path)
            plugin_instance = plugin_module.Plugin(manifest)
            self.plugins[plugin_name] = plugin_instance
            self.plugins[plugin_name].load()

            # load plugin metaprocesses
            load_plugin_metaprocesses(os.path.join(self.plugin_dir, plugin_name))

            self.plugin_states[plugin_name] = True
            return True
        return False

    def unload_plugin(self, plugin_name):
        """Unload a plugin by name."""
        # Indempotence check
        if not self.plugin_states.get(plugin_name, False):
            # print(f"Plugin {plugin_name} is not loaded.")
            return False
        if plugin_name in self.plugins:
            # Perform any cleanup if necessary
            self.plugins[plugin_name].unload()
            # unload plugin metaprocesses
            unload_plugin_metaprocesses(os.path.join(self.plugin_dir, plugin_name))
            del self.plugins[plugin_name]
            self.plugin_states[plugin_name] = False
            return True
        return False
    
    def load_all(self):
        """Load all plugins."""
        print("=== Loading all plugins ===")
        for plugin_name, _, _ in self.list_plugins():
            self.load_plugin(plugin_name)
    
    def unload_all(self):
        """Unload all plugins."""
        print("=== Unloading all plugins ===")
        for plugin_name, _, _ in self.list_plugins():
            self.unload_plugin(plugin_name)

    def load_plugins(self, plugin_names):
        """Load selected plugins."""
        print("=== Loading selected plugins ===")
        for plugin_name in plugin_names:
            self.load_plugin(plugin_name)
    
    def unload_plugins(self, plugin_names):
        """Unload selected plugins."""
        print("=== Unloading selected plugins ===")
        for plugin_name in plugin_names:
            self.unload_plugin(plugin_name)

###########################
# Plugin loading helpers  #
###########################

def load_plugin_metaprocesses(plugin_path):
    # load plugin metaprocesses
    if os.path.exists(os.path.join(plugin_path, "metaprocesses")):
        if os.path.exists(os.path.join(plugin_path, "metaprocesses", "headers")):
            print("Found metaprocess headers")
            for filename in os.listdir(os.path.join(plugin_path, "metaprocesses", "headers")):
                if filename.endswith(".json"):
                    with open(os.path.join(plugin_path, "metaprocesses", "headers", filename), "r") as f:
                        data = json.load(f)
                    metaprocess.metaprocess_headers[filename.split(".")[0]] = data["prompt"]
        for filename in os.listdir(os.path.join(plugin_path, "metaprocesses")):
            print("Found metaprocess file", filename)
            if filename.endswith(".json"):
                print(f"Loading metaprocess \"{filename.split('.json')[0]}\" from plugin \"{plugin_path.split('/')[-1]}\"")
                metaprocess.metaprocesses[filename.split(".")[0]] = metaprocess.load_metaprocess(os.path.join(plugin_path, "metaprocesses", filename))

def unload_plugin_metaprocesses(plugin_path):
    # unload plugin metaprocesses
    if os.path.exists(os.path.join(plugin_path, "metaprocesses", "headers")):
        print("Found metaprocess headers")
        for filename in os.listdir(os.path.join(plugin_path, "metaprocesses", "headers")):
            if filename.endswith(".json"):
                del metaprocess.metaprocess_headers[filename.split(".")[0]]
    for filename in os.listdir(os.path.join(plugin_path, "metaprocesses")):
        print("Found metaprocess file", filename)
        if filename.endswith(".json"):
            print(f"Unloading metaprocess \"{filename.split('.json')[0]}\" from plugin \"{plugin_path}\"")
            del metaprocess.metaprocesses[filename.split(".")[0]]

def load_plugin_tags(plugin_path):
    ...

def unload_plugin_tags(plugin_path):
    ...

def load_plugin_resources(plugin_path):
    ...

def unload_plugin_resources(plugin_path):
    ...

def load_plugin_components(plugin_path):
    ...

def unload_plugin_components(plugin_path):
    ...