import re
import asyncio

from logs import logger

class Censor(object):
    def __init__(self, blacklist: list[str]):
        self.blacklist = [w.upper() for w in blacklist]

    async def exceptions(self, message: str) -> bool:
        message = message.upper()

        return any(word in message for word in self.blacklist)

    async def bad_words(self, message: str) -> bool:
        #while await asyncio.sleep(0, result=True):
        message_without_tools = message.split('[', 1)[0].strip()
        message_without_tools = message_without_tools.split('> ', 1)[-1].strip()

        if len(message_without_tools) >= 150 or re.search('[a-ce-zA-CE-Z]', message_without_tools) or await self.exceptions(message_without_tools):

            logger.info('Blacklist pattern detected! Reroll')
            return True

        return False




