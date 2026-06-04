import os
import random
import asyncio
import enum
from typing import Literal

from pyrogram import Client
from langchain_community.utilities import WikipediaAPIWrapper
from langchain_community.tools import DuckDuckGoSearchRun, DuckDuckGoSearchResults

from ai.tool.decorator import tool

from logs import logger

class Tools(object):
    def __init__(self, app: Client, ai_chat):
        self.app = app
        self.ai_chat = ai_chat
        self.wiki = WikipediaAPIWrapper(lang="ru", top_k_results=1, doc_content_chars_max=2000)
        self.search = DuckDuckGoSearchRun()
        self.all_functions = [self.send_photos, self.search_web, self.end_dialog]

    @tool
    async def send_photos(self, userId: int, reason: str, theme: Literal["cats", "meme", "yourself", "butt"], count: int):
        """
        Отправляет собеседнику несколько фото определённой тематики.
        Используй эту функцию только, если уверен, что хочешь отправить фотографии пользователю..

        Args:
            userId: Идентификационный номер общающегося с тобой человека, у каждого он уникален (например, 6512237395)
            reason: Причина отправки фото (например, 'Договорились с собеседником обменяться фотографиями', 'Собеседник очень хорошо попросил').
            theme: Тематика фотографий.
            count: Сколько фотографий отправить (диапазон 1-3) (например, 2).
        """
        def get_random_files(folder_path: str, count: int) -> list[str]:
            file_names = []

            try:
                for entry in os.scandir(os.path.join(os.path.dirname(__file__),os.path.join("photos", folder_path))):
                    if entry.is_file():
                        file_names.append(entry.path)

                return random.sample(file_names, k=min(count, len(file_names)))
            except Exception as e:
                logger.error("get_random_files File Error", exc_info=  True)

        match theme:
            case "cats" | "meme" | "yourself" | "butt":
                print(count)
                for file in get_random_files(theme, int(count)):
                    #await self.app.send_chat_action(sender_id, enums.ChatAction.TYPING)
                    await asyncio.sleep(0.3)
                    await self.app.send_photo(int(userId), file)
                    await asyncio.sleep(0.3)
            case _:
                logger.error("Incorrect theme type")


    @tool
    async def search_web(self, userId: int, query: str):
        """
        Поиск информации в интернете, если текущих знаний недостаточно для ответа.
        Если у тебя спрашивают что-то, а ты не знаешь, сразу же попробуй загуглить в интернете.  Используй часто эту функцию, лишней информации не бывает, она добавиться в контекст.
    
        Args:
            userId: Идентификационный номер общающегося с тобой человека, у каждого он уникален (например, 6512237395)
            query: Поисковый запрос (например, 'Что обещал Трамп на своей иннаугурации')
        """

        print(f"query: {query}")
        context = await asyncio.to_thread(self.search.run, query)

        return {"search_web": f"Вот что выдал гугл на запрос '{query}': {context}"}

    @tool
    async def end_dialog(self, userId: int, reason: str):
        """
        Заканчивает диалог с собеседником.
        Используй эту функцию, сразу же, если вы с собеседником (или собеседник с вами) попрощались, или собеседник уходит, или если собеседник ведёт себя неадекватно, или все его сообщения лишены смысла, или устали от диалога. 

        Args:
            userId: Идентификационный номер общающегося с тобой человека, у каждого он уникален (например, 6512237395)
            reason: Причина завершения диалога (например, 'Собеседник ушёл', 'Вы попращались', 'Неадекватное поведение').
        """

        await self.app.send_message(int(userId), "Иди нахуй")

    #set_timer_alert: ИИ ставит себе внутренний таймер, чтобы написать вам через час: "Ну что, ты закончил дела?"