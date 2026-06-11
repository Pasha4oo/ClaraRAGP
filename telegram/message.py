import asyncio

import random

from emoji import is_emoji
from pyrogram import Client, enums

from processors.tts import TextToSpeech
from processors.message import NaturalMessageProcessor
from processors.garbage import GarbageDestroyer

from ai.corrector import TextCorrector

class MessageController(object):
    def __init__(self, app: Client):
        self.text_processor = NaturalMessageProcessor()
        self.garbage_destroyer = GarbageDestroyer()
        self.app = app

        #self.corrector = TextCorrector()

        self.send_task = None

        self.tts = TextToSpeech()

    async def send_message(self, message: str, sender_id: int):
        """Sends message into saved chat into Telegrams"""
        if self.send_task and not self.send_task.done():
            self.send_task.cancel()

        self.send_task = asyncio.current_task()

        message = self.garbage_destroyer.destroy_all(message)
        #corrected = self.corrector.correct_message(message)
        asyncio.create_task(self.tts.say(message))
        sentences = self.text_processor.split_message(self.text_processor.add_errors_in_message(message, True, 1))
        
        for sentence in sentences:
            if asyncio.current_task().cancelled():
                return

            if is_emoji(sentence): 
                await self.app.send_chat_action(sender_id, enums.ChatAction.CHOOSE_STICKER)
                await asyncio.sleep(random.randint(8, 18) / 10)
                sticker = await self.text_processor.get_pack_stiker_from_emoji(self.app, sentence, 
                                                                                                 ["manga001", 
                                                                                                  "buigzo_by_sempai_stickersbot",
                                                                                                  "oumae",
                                                                                                  "KatShi_StickerChest",
                                                                                                  "mizy_vk",
                                                                                                  "f_hjquqjqd_1415101787_by_fStikBot"])
                if sticker:
                    await self.app.send_sticker(sender_id, sticker)
            else:
                await self.app.send_chat_action(sender_id, enums.ChatAction.TYPING)
                await asyncio.sleep(len(sentence) / 6 + 0.3)
                await self.app.send_message(sender_id, sentence)
