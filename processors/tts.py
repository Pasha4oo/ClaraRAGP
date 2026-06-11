import asyncio

from os import path, makedirs
from datetime import datetime

from logs import logger

from processors.tor import Tor

import requests
import time
import json
import socket

class TextToSpeech(object):
    def __init__(self):
        self.VOICE = "Lyudmila"       #Evdokiya, Isabella RU, Lyudmila
        self.SAVE_DIR = "downloads"
        self.PLAY = True

        self.tor = Tor()

        logger.info(f"Current IP: {self.tor.get_ip()}")

        logger.info("Warming up session")
        self.tor.session.get('https://speechgen.io/')
        time.sleep(1)
        self.tor.session.get('https://speechgen.io/en/', headers={'Referer': 'https://speechgen.io/'})

    async def say(self, text: str):
        '''Voices the text'''
        filepath = await asyncio.to_thread(self.tts, text)
        await self.play_audio(filepath)

    async def play_audio(self, path_to_audio: str):
        '''Plays audio using ffplay.exe'''
        
        ffplay_exe = path.join(
            path.dirname(__file__), 
            "ffmpeg-2024-07-04-git-03175b587c-full_build", "bin", 
            "ffplay.exe"
        )

        command = [ffplay_exe, "-nodisp", "-autoexit", path_to_audio]

        try:
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            await process.communicate()

        except Exception as e:
            logger.error(f"Playback error: {e}", exc_info=True)


    def tts(self, text: str) -> str:
        """TTS from speechgen.io, returns mp3_file_path"""
        mp3_url = None
        param = {
            "lang": "ru-RU", "voice": self.VOICE, "format": "mp3",
            "text": text, "captcha_value": "123456",
            "pp": "400", "ps": "300", "hz": "48000", "speed_type": 1,
            "bitrate": 64, "channels": 1, "speed": 1, "pitch": 3,
            "volume": 100, "styledegree": 1, "vocabulary": False,
            "popup_cptch": 0, "style": "whisper", "role": ""
        }

        r = self.tor.session.post('https://speechgen.io/index.php?r=tts/TextToMp3Add&lang=en',
                         data={'param': json.dumps(param)})
        data = r.json()
        logger.info(f"Sended text: {text}")
        logger.info(f"Received text: {json.dumps(data, ensure_ascii=False, indent=2)}")

        if data.get('status') == 1 and data.get('file_mp3'):
            mp3_url = 'https://speechgen.io/' + data['file_mp3']
        else:
            tid = data.get('prj_id') or data.get('id')
            if not tid:
                logger.error("There are no ID")

            total_parts = int(data.get('parts', 0))
            #print(f"  [Ожидание] ID={tid}, частей: {total_parts}, ждём статус 1...")
        
            for attempt in range(1, 51):
                time.sleep(0.2)
                r = self.tor.session.get('https://speechgen.io/index.php?r=tts/TextToMp3GetResult',
                               params={'id': tid, 'lang': 'en'})
                d = r.json()
                status = int(d.get('status', 0))
                parts_done = d.get('parts_done')
                parts = int(d.get('parts', total_parts))
                if parts > 0:
                    total_parts = parts
                print(f"  [Опрос {attempt}/50] статус={status}, частей: {parts_done}/{total_parts}")

                if status == 2:
                    logger.error("Blocked as a robot error (status=2)")
                    break

                if status == 1:
                    if d.get('file_mp3'):
                        mp3_url = 'https://speechgen.io/' + d['file_mp3']
                    break

            if not mp3_url:
                r = self.tor.session.post('https://speechgen.io/index.php?r=tts/TextToMp3Add&lang=en',
                                 data={'param': json.dumps(param)})
                data2 = r.json()

                if data2.get('file_mp3'):
                    mp3_url = 'https://speechgen.io/' + data2['file_mp3']
                else:
                    logger.error("Second Add did not provide a link")

        #downloading audio
        for retry in range(2):
            resp = self.tor.session.get(mp3_url)
            if resp.status_code == 200 and len(resp.content) > 0:
                break
            time.sleep(0.5)
        else:
            logger.error(f"Downloading audio file error {resp.status_code}")

        if not path.exists(self.SAVE_DIR):
            makedirs(self.SAVE_DIR)

        safe_text = "".join(c for c in text[:15] if c.isalpha() or c.isdigit() or c == ' ').strip()
        filename = f"{self.VOICE}_{datetime.now().strftime("%Y%m%d_%H%M%S")}_{safe_text}.mp3"
        filepath = path.join(self.SAVE_DIR, filename)

        with open(filepath, 'wb') as f:
            f.write(resp.content)

        logger.info(f"Audio file path: {filepath} ({len(resp.content)} bytes)")

        return filepath