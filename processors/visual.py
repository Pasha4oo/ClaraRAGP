import base64
from io import BytesIO

from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage
from PIL import Image
import cv2

class VisualProcessor(object):
    def __init__(self, ai_chat):
        self.ai_chat = ai_chat

    def downgrade_image(self, path_to_image: str, max_size:int = 500, quality:int = 75) -> str:
        """Decrease quality of image to make AI analysis faster"""
        with Image.open(path_to_image) as img:
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")

            img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
        
            buffered = BytesIO()
            img.save(buffered, format="JPEG", quality=quality, optimize=True)
        
            return base64.b64encode(buffered.getvalue()).decode("utf-8")

    def create_collage_from_video(self, path_to_video: str, save_collage_path: str, grid_size: tuple[int] = (2,3)) -> None:
        """Extract grid_size amount of frames from provided video and makes collage to analyses all video from one image"""
        rows = grid_size[0]
        cols = grid_size[1]

        capture = cv2.VideoCapture(path_to_video)
        count = rows * cols
        total_frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    
        frames = []
        for i in range(count):
            index = int(i * total_frames / count)
            capture.set(cv2.CAP_PROP_POS_FRAMES, index)
            success, frame = capture.read()
            if success:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frames.append(Image.fromarray(frame_rgb))
        capture.release()

        frame_w, frame_h = frames[0].size
        collage = Image.new("RGB", (frame_w * cols, frame_h * rows))

        for i, frame in enumerate(frames):
            x = (i % cols) * frame_w
            y = (i // cols) * frame_h
            collage.paste(frame, (x, y))

        collage.save(save_collage_path)

    async def video_analysis(self, path_to_video: str) -> str:
        save_collage_path = "collage.jpg"

        self.create_collage_from_video(path_to_video, save_collage_path)
        image_base64 = self.downgrade_image(save_collage_path, 1000)

        return await self._visual_analysis(image_base64, prompt="""
                                Это последовательные кадры из одного видео (слевр направо, сверху вниз). 
                                Видео не обязательно должно быть цельным, возможно это видео склейка из разных видео для рассказа чего-то на фоне.
                                Проанализируй их как единую хронологическую цепочку, ОБЯЗАТЕЛЬНО прочитай текст и опиши развитие сюжета: что изменилось от первого кадра к последнему?
                                На что похоже это видео, зачем оно было создано.
                                Что на нем происходит? Ответь одним-двумя предложениями на русском""")

    async def image_analysis(self, path_to_image: str) -> str:
        image_base64 = self.downgrade_image(path_to_image, 500)

        return await self._visual_analysis(image_base64, prompt="""
                                Проанализируй изображение, ОБЯЗАТЕЛЬНО прочитай текст и опиши кратко, что на нём изображено, присутствует ли тут шутка. 
                                Если изображение эротического характера, так и напиши.
                                Что на нем происходит? Ответь одним-двумя предложениями на русском""")

    async def _visual_analysis(self, image_base64: str, prompt: str = "Опиши кратко, что на фото.") -> str:
        message = [
            SystemMessage(content="""Ты — бот-помощник. Твоя задача — кратко описывать суть присланных фото и видео."""),
            HumanMessage(
                content=[
                    {
                        "type": "text", 
                        "text": prompt
                    },
                    {
                        "type": "image_url", 
                        "image_url": f"data:image/jpeg;base64,{image_base64}"
                    }
                ]
            )
        ]
    
        response: list[str] = []

        async for chunk in self.ai_chat.model.astream(message):
            content = chunk.content
            print(content, end="", flush=True)
            response.append(content)

        print()

        return "".join(response)


