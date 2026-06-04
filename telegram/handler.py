import asyncio

from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.handlers import MessageHandler

from ai.tool.tools import Tools
from telegram.message import MessageController

from processors.processor import Processor

from ai.tool.caller import ToolCaller

from config import API_ID, API_HASH
from logs import logger

class TelegramHandler(object):
    def __init__(self, ai_chat):
        self.API_ID = API_ID
        self.API_HASH = API_HASH

        self.ai_chat = ai_chat

        self.path_to_video: list[str] = []
        self.path_to_audio: list[str] = []
        self.path_to_image: list[str] = []
        self.message_text: list[str] = []
    
    def run(self):
        """Creates and starts Telegram session"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        self.app = Client('my_account', api_id=self.API_ID, api_hash=self.API_HASH)
        self.processor = Processor(self.ai_chat, self.app)
        self.message_controller = MessageController(self.app)
        self.tool_caller = ToolCaller(self.app, self.ai_chat)
        self._handlers()

        async def start():
            await self.app.start()
            async for dialog in self.app.get_dialogs():
                pass
            await asyncio.Event().wait()
        
        loop.run_until_complete(start())

    def _handlers(self):
        self.app.add_handler(MessageHandler(self.on_audio, ~filters.me & filters.voice))
        self.app.add_handler(MessageHandler(self.on_video, ~filters.me &  (filters.video | filters.video_note)))
        self.app.add_handler(MessageHandler(self.on_message,  ~filters.me & filters.text & ~filters.reply))
        self.app.add_handler(MessageHandler(self.on_reply,  ~filters.me & filters.text & filters.reply))
        self.app.add_handler(MessageHandler(self.on_sticker, ~filters.me & filters.sticker))
        self.app.add_handler(MessageHandler(self.on_image,  ~filters.me & filters.photo))

    async def on_reply(self, client: Client, messages: Message):
        """Executed when the Telegram client receives a text message"""
        if isinstance(messages, Message):
            self.message_text.append(messages.text)
        else:
            self.message_text.append(messages)

        await self.app.read_chat_history(search_id if isinstance(messages, str) else messages.chat.id)
        ai_response = await self.processor.debounce(3.5 if len(self.message_text) < 15 else 5, self.ai_chat.send_message, " ".join(self.message_text), search_id if isinstance(messages, str) else messages.chat.id)
        print(" ".join(self.message_text))
        if ai_response:
            tool_result = await self.tool_caller.execute_tools(ai_response)
            print(tool_result)
            wiki_data = tool_result.get("search_web") if tool_result else None
            if wiki_data:
                await self.on_message(client, wiki_data, search_id if isinstance(messages, str) else messages.chat.id)
                return

            ai_response = self.tool_caller.remove_function_calls(ai_response)

            await self.message_controller.send_message(ai_response, search_id if isinstance(messages, str) else messages.chat.id)
            self.message_text = []
        else:
            logger.info("Another text message received")

    async def on_sticker(self, client: Client, messages: Message):
        """Executed when the Telegram client receives a sticker"""

        await self.app.read_chat_history(messages.chat.id)
        print(messages.sticker.emoji)

    async def on_message(self, client: Client, messages: Message | str, search_id: int | None = None):
        """Executed when the Telegram client receives a text message"""
        if isinstance(messages, Message):
            self.message_text.append(messages.text)
        else:
            self.message_text.append(messages)

        await self.app.read_chat_history(search_id if isinstance(messages, str) else messages.chat.id)
        ai_response = await self.processor.debounce(3.5 if len(self.message_text) < 15 else 5, self.ai_chat.send_message, " ".join(self.message_text), search_id if isinstance(messages, str) else messages.chat.id)
        print(" ".join(self.message_text))
        if ai_response:
            tool_result = await self.tool_caller.execute_tools(ai_response)
            print(tool_result)
            wiki_data = tool_result.get("search_web") if tool_result else None
            if wiki_data:
                await self.on_message(client, wiki_data, search_id if isinstance(messages, str) else messages.chat.id)
                return

            ai_response = self.tool_caller.remove_function_calls(ai_response)

            await self.message_controller.send_message(ai_response, search_id if isinstance(messages, str) else messages.chat.id)
            self.message_text = []
        else:
            logger.info("Another text message received")

    async def on_audio(self, client: Client, messages: Message):
        """Executed when the Telegram client receives a voice/audio message"""
        self.path_to_audio.append(await client.download_media(messages))

        await self.app.read_chat_history(messages.chat.id)
        ai_response = await self.processor.debounce(1, self.processor.process_audio, self.path_to_audio, messages.chat.id)
        if ai_response:
            await self.tool_caller.execute_tools(ai_response)
            ai_response = self.tool_caller.remove_function_calls(ai_response)

            await self.message_controller.send_message(ai_response, messages.chat.id)
            self.path_to_audio = []
        else:
            logger.info("Another audio received")

    async def on_video(self, client: Client, messages: Message):
        """Executed when the Telegram client receives a video/video note"""
        self.path_to_video.append(await client.download_media(messages))

        await self.app.read_chat_history(messages.chat.id)
        ai_response = await self.processor.debounce(1, self.processor.process_video, self.path_to_video, messages.chat.id)
        if ai_response:
            await self.tool_caller.execute_tools(ai_response)
            ai_response = self.tool_caller.remove_function_calls(ai_response)

            await self.message_controller.send_message(ai_response, messages.chat.id)
            self.path_to_video = []
        else:
            logger.info("Another video received")

    async def on_image(self, client: Client, messages: Message):
        """Executed when the Telegram client receives a image/gif"""
        self.path_to_image.append(await client.download_media(messages))

        await self.app.read_chat_history(messages.chat.id)
        ai_response = await self.processor.debounce(1, self.processor.process_image, self.path_to_image, messages.chat.id)
        if ai_response:
            await self.tool_caller.execute_tools(ai_response)
            ai_response = self.tool_caller.remove_function_calls(ai_response)

            await self.message_controller.send_message(ai_response, messages.chat.id)
            self.path_to_image = []
        else:
            logger.info("Another image received")

