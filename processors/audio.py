import os
import asyncio
import json
import subprocess
import vosk
from pydub import AudioSegment, effects

from processors.tts import TextToSpeech

from logs import logger

from config import DEBUG

class AudioProcessor(object):
    def __init__(self, local_audio_path: str = ''):
        logger.info("Audio processor loading started")

        if DEBUG:
            self.model = vosk.Model(f"{os.path.dirname(__file__)}\\vosk_model_small")
        else:
            self.model = vosk.Model(f"{os.path.dirname(__file__)}\\vosk_model_large")
        self.path = local_audio_path

        logger.info("Audio processor loading succed")

    async def get_text_from_audio(self, path_to_audio: str) -> str:
        '''Converts audio file to .WAV format and recognizes speech'''

        file_path_wav = os.path.join(os.path.dirname(__file__), "new.wav")
        ffmpeg_exe = os.path.join(
            os.path.dirname(__file__), 
            "ffmpeg-2024-07-04-git-03175b587c-full_build", "bin", 
            "ffmpeg.exe")

        #converts audio into wav
        try:
            command = [ffmpeg_exe, "-y", "-i", 
                       path_to_audio, "-vn", "-acodec", "pcm_s16le", "-ar", "44100", "-ac", "2",  #44100
                       file_path_wav]

            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            await process.communicate()

        except subprocess.CalledProcessError as e:
            logger.error("Converting audio error:", exc_info=True)

            return None

        return await asyncio.to_thread(self._recognize, file_path_wav)

    async def play_audio(self, path_to_audio: str):
        '''Plays audio using ffplay.exe'''
        
        ffplay_exe = os.path.join(
            os.path.dirname(__file__), 
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


    def _recognize(self, file_path_wav: str) -> str:
        '''Uses VOSK KaldiRecognizer to extract text from audio sources'''

        rec = vosk.KaldiRecognizer(self.model, 16000)
        rec.SetWords(True)

        ogg = AudioSegment.from_wav(file_path_wav)
        ogg = ogg.set_channels(1)
        ogg = ogg.set_frame_rate(16000) #16000
        ogg = effects.normalize(ogg)

        rec.AcceptWaveform(ogg.raw_data)
        result = json.loads(rec.FinalResult())

        if os.path.exists(file_path_wav):
            os.remove(file_path_wav)

        return result['text']
