import os
from logs import logger

class PromptsCollector(object):
    def __init__(self):
        self.prompts = []

        self.load_prompts();

    def load_prompts(self, folder_path: str = ""):          
        path = os.path.join(os.path.join(os.path.dirname(__file__),  folder_path or ""))

        for entry in os.scandir(path):
            if entry.is_file() and entry.name.endswith(".txt"):
                try:
                    with open(entry.path, "r", encoding="utf-8") as f:
                        self.prompts.append(f.read())
                except Exception as e:
                    logger.error("Read prompt from file Error", exc_info=True)