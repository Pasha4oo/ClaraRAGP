import os
import sys
import logging
from time import time

import emoji

class Logger(logging.Logger):
    def __init__(self, name=__name__):
        super().__init__(name)
        self.setLevel(logging.INFO)

        formatter = logging.Formatter('%(name)s - %(asctime)s - %(levelname)s - %(message)s')
        
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        
        if not self.handlers:
            self.addHandler(console_handler)

    def save_chat(self, who:str, text: str) -> None:
        """Saves message, converts emojis into text"""

        try:
            with open(f"{os.path.dirname(__file__)}\\downloads\\chats\\chats.txt", 'a', encoding="utf-8-sig") as chat:
                chat.write(f'{who} :: {emoji.demojize(text)} :: {time()} \n')
        except Exception as error:
            print(f'LOGGER ERROR: {error}')

logger = Logger()