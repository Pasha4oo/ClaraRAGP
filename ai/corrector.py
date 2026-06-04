import os
import torch
from transformers import pipeline

from timer import Timer
from logs import logger

from config import DEBUG

class TextCorrector(object):
    def __init__(self):   #ai-forever/sage-fredt5-distilled-95m ai-forever/sage-fredt5-large
        logger.info("Corrector model loading")

        os.environ["OPENVINO_NUM_THREADS"] = "8"

        torch.set_num_interop_threads(1)
        torch.set_num_threads(8)

        self.fixer = pipeline("text2text-generation", 
                model="ai-forever/sage-fredt5-distilled-95m",
                device="cpu" if torch.cuda.is_available() else -1,
                dtype=torch.bfloat16) #C:\Users\user\.cache\huggingface\hub

        if not(DEBUG) and hasattr(torch, 'compile'):
            try:
                logger.info("Corrector model compilation")
                torch._dynamo.config.suppress_errors = True 
                self.fixer.model = torch.compile(self.fixer.model, mode="max-autotune", backend="inductor")
                
                logger.info("Model cold start")
                self.fixer("Относительно длинный текст на русском языке для прогрева модели и последующего ускорения его запуска", max_length=30)[0]['generated_text']
                logger.info("Corrector model is ready")
            except Exception as e:
                logger.error("Precompile failed, run slow mode", exc_info=True)

    def correct_message(self, message: str) -> str:
        with Timer() as time:
            corrected_message = self.fixer(message, max_length=300, num_beams=1, do_sample=False)[0]['generated_text']

        logger.info(f"{message} : {corrected_message} : {time.duration:.2f}")

        return corrected_message





