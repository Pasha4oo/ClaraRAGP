import asyncio

from emoji import is_emoji
from pyrogram import Client, enums

from processors.message import NaturalMessageProcessor
from processors.garbage import GarbageDestroyer

class MessageController(object):
    def __init__(self, app: Client):
        self.text_processor = NaturalMessageProcessor()
        self.garbage_destroyer = GarbageDestroyer()
        self.app = app

    async def send_message(self, message: str, sender_id: int):
        """Sends message into saved chat into Telegrams"""
        message = self.garbage_destroyer.destroy_all(message)
        sentences = self.text_processor.split_message(self.text_processor.add_errors_in_message(message, True, 1))
        
        for sentence in sentences:
            if is_emoji(sentence): 
                await self.app.send_chat_action(sender_id, enums.ChatAction.CHOOSE_STICKER)
                await asyncio.sleep(0.5)
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
                await asyncio.sleep(len(sentence) / 7)
                await self.app.send_message(sender_id, sentence)
