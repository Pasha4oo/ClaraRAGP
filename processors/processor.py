import asyncio
from os import path

from pyrogram import Client
from pyrogram.types import Message

from processors.audio import AudioProcessor
from processors.visual import VisualProcessor

from logs import logger

class Processor(object):
    def __init__(self, ai_chat, app):
        self.ai_chat = ai_chat
        self.app = app

        self.audio_processor = AudioProcessor()
        self.visual_processor = VisualProcessor(ai_chat)

        self.current_task = None
        self.current_timeout = 5

    async def process_audio(self, paths_to_audio: str | list[str], sender_id: int):
        """Returns the AI ​​response to the transcribed audio"""
        if isinstance(paths_to_audio, str):
            paths_to_audio = [paths_to_audio]

        transcribed_text = ''

        for index, path_to_audio in enumerate(paths_to_audio):
            transcribed_text += f"{await self.audio_processor.get_text_from_audio(path_to_audio)}"

            #Audio from video note number {index + 1} text is '{

        ai_response = await self.ai_chat.send_message(transcribed_text, sender_id)
        # The user has provided a couple of short audio messages 
        #                                             (bad quality, some words can be not heard or replaced with similar-sounding ones). 
        #                                             The transcribed audio says: {transcribed_text}.
        #                                             Dont say word 'audio' or similar, only soft reaction
        return ai_response

    async def process_video(self, paths_to_video: str | list[str], sender_id: int):
        """Returns the AI ​​response to the transcribed audio and frames from video"""
        if isinstance(paths_to_video, str):
            paths_to_video = [paths_to_video]
        
        transcribed_text = ''
        video_description = ''

        for index, path_to_video in enumerate(paths_to_video):
            transcribed_text += f"Video note number {index + 1} text is '{await self.audio_processor.get_text_from_audio(path_to_video)} '"
            video_description += f"Video note number {index + 1} description is '{await self.visual_processor.video_analysis(path_to_video)} '"

        ai_response = await self.ai_chat.send_message(f"""
                                                The user has provided a couple of short video messages (circular video notes).
                                                Often, while someone is talking, they put on a meaningless video background  (carpet washing, gaming, soap cutting, manufacturing). 
                                                If the audio has nothing to do with the background, then the background probably doesn't matter; focus on the audio.
                                                The transcribed audio (audio in a bad quality) from this videos says: "{transcribed_text}".
                                                Video description: "{video_description}".
                                                Video and audio are one whole. Answer very short and only about one whole video, don't separate answer on audio and video.
                                                Dont say word 'video' or similar, only soft reaction""",sender_id)
        return ai_response

    async def process_image(self, paths_to_image: str | list[str], sender_id: int) -> str:
        """Returns the AI ​​response to images"""
        if isinstance(paths_to_image, str):
            paths_to_image = [paths_to_image]
       
        image_description = ''

        for index, path_to_image in enumerate(paths_to_image):
            image_description += f"Number {index + 1} description is '{await self.visual_processor.image_analysis(path_to_image)}' "

        ai_response = await self.ai_chat.send_message(f"""The user has provided a couple of images. Important. If the image is erotic, ask for more. The picture shows: {image_description}
                                            Important! Dont say word 'image', 'photo', 'picture' and others, don't use enumerations ('first', 'second'...), only soft reaction""", sender_id)
        return ai_response

    async def debounce(self, delay: int, func, *args, **kwargs):
        """Executes the last passed async function after a period of time, and resets the timer when called again"""
        logger.info("debounce started")

        if self.current_task and not self.current_task.done():
            self.current_task.cancel()
            self.current_timeout = 3.5
            try:
                await self.current_task 
            except asyncio.CancelledError:
                logger.info("debounce canceled")
                pass 
        else:
            self.current_timeout = delay

        self.current_task = asyncio.create_task(self._run_with_delay(func, *args, **kwargs))
        return await self.current_task

    async def _run_with_delay(self, func, *args, **kwargs):
        try:
            logger.info("_run_with_delay sleep started")
            await asyncio.sleep(self.current_timeout)
            logger.info("_run_with_delay sleep ended")
            #await self.app.send_chat_action(chat_id, enums.ChatAction.TYPING)
            return await func(*args, **kwargs)
        except asyncio.CancelledError:
            logger.info("_run_with_delay canceled")
            return None


