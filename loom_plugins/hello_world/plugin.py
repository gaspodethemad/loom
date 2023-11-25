from plugins import BasePlugin

class Plugin(BasePlugin):
    def __init__(self, manifest):
        super().__init__(manifest)

    def load(self):
        print("Hello World!")

    def unload(self):
        print("Bye World!")