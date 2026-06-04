import asyncio
from threading import Thread
import time

import emoji

from telegram.handler import TelegramHandler
from ai.chat import AIChat

from logs import logger

ai_chat = AIChat()
telegram = TelegramHandler(ai_chat)

#async def test_functions():
 #   await image_processor.analyze_image()

if __name__ == '__main__':
    logger.info("Loading complete succsesfully")
    thread = Thread(target=telegram.run, daemon=True)
    thread.start()
    logger.info("Thread started succsesfully")
    #asyncio.run(test_functions())

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nExit...")
