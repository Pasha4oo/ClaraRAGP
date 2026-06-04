import asyncio
import re
from requests import post, Session
from bs4 import BeautifulSoup

from random import randint, choice
from pydantic import validate_call, Field

from pyrogram import Client, raw
from pyrogram.types import Sticker

from emoji import is_emoji, replace_emoji

import nlpaug.augmenter.char as nac

from logs import logger

from config import ERROR_TYPE, DEBUG

class NaturalMessageProcessor(object):
    def __init__(self):
        self.session = Session()

    async def get_pack_stiker_from_emoji(self, app: Client, emoji: str, packs: str | list[str]) -> str:
        '''Returns the ID of the random Telegram sticker from the suggested options if exists
        else returns random standart sticker (get_random_stiker_from_emoji)'''
        if not is_emoji(emoji): raise ValueError("It's not emoji")

        if isinstance(packs, str):
            packs = [packs]

        finded_stickers_id = []
        
        for pack in packs:
            sticker_set = await app.get_stickers(pack)

            for sticker in sticker_set:
                if sticker.emoji == emoji:
                    finded_stickers_id.append(sticker.file_id)

        if finded_stickers_id:
            return choice(finded_stickers_id)
        elif not(DEBUG):
            return await self.get_random_stiker_from_emoji(app, emoji)

        return None

    async def get_random_stiker_from_emoji(self, app: Client, emoji: str) -> str:
        '''Returns a random standart Telegram sticker ID from the given options.'''
        if not is_emoji(emoji): raise Exception("It's not emoji")

        result = await app.invoke(
            raw.functions.messages.GetStickers(
                emoticon=emoji,
                hash=0
            )
        )

        if result.stickers:
            raw_sticker = choice(result.stickers)
            sticker = await Sticker._parse(app, raw_sticker, {type(i): i for i in raw_sticker.attributes})
        
            return sticker.file_id

        return None

    def split_message(self, message: str) -> list:
        '''Returns splited list from message on ". ! ? \n and emoji"'''

        message_list = []

        message = str(message)

        message = message.replace('-', '')
        message = message.replace('  ', ' ')

        message = message.replace('...', '{dots}\n')
        message = message.replace('.', '\n')
        message = message.replace('{dots}', '...')
        message = message.replace('! ', '! \n')
        message = message.replace('??', '\n')
        message = message.replace('? ', '? \n')
        message = replace_emoji(message, replace=lambda chars, data_dict: f"\n{chars}\n")

        for char in message:
            if not(char == ',' and randint(1, 2) == 1):
                message_list.append(char)
            elif randint(1, 2) == 1:
                message_list.append(',')

        sentences = ("".join(message_list)).split("\n")

        final_message = []

        for sentence in sentences:
            if not sentence.strip():
                continue

            final_message.append(sentence.strip())

        return final_message

    @validate_call
    def add_errors_in_message(self, message: str, 
                              to_lowercase: bool, 
                              percent_of_errors: int = Field(gt=0, lt=100),
                              delete_extra_spaces: bool = True,
                              rand_continue_type_in_english: bool = False) -> str:
        '''Request text with errors 
        Internet needed'''

        if ERROR_TYPE.upper() == "ONLINE":
            url = 'https://seogift.ru/tools/generator-opechatok/'
        
            payload = {
                'lines' : message,
                'tolowercase' : to_lowercase,
                'deletemorespaces': "on" if delete_extra_spaces else "",
                'withenglish' : "on" if rand_continue_type_in_english else "",
                'wordscounttransp' : str(randint(0, 1)) if rand_continue_type_in_english else "0",
                'percentrepl' : percent_of_errors,
                'doactiontool' : 'do'
            }

            requested_text = self.session.post(url, data = payload)
            parsed_text = BeautifulSoup(requested_text.text,"html.parser")

            ready_text = parsed_text.find('textarea', {'class' : 'int_text textarea_block'})

            if ready_text and ready_text.text:
                return ready_text.text

            logger.error(f"Add_errors_in_message Error. ready_text: {ready_text}", exc_info=True)
            return message

        elif ERROR_TYPE.upper() == "OFFLINE":
            rules = {
                "ться": "тся",
                "тся ": "ца ",
                "стн": "сн"
            }

            return message.lower()

