import asyncio
import json
from venv import logger

from langchain_ollama import ChatOllama
from langchain_community.llms import LlamaCpp
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser

from processors.censor import Censor

from ai.corrector import TextCorrector
from ai.prompt.prompts import PromptsCollector
from ai.tool.decorator import registry

from logs import logger
from timer import Timer, Time

from config import CENSOR_WORDS
import llama_cpp
import os

class AIChat(object):
    def __init__(self):
        self.prompts_collector = PromptsCollector()
        prompt = self.prompts_collector.prompts[1]
        print(prompt)

        #print(f"!!! CUDA SUPPORTED: {llama_cpp.llama_supports_gpu_offload()} !!!")

        self.model = ChatOllama(
            model="gemma4:latest", #hf.co/mradermacher/gemma-3-12b-it-abliterated-i1-GGUF:Q4_K_M #gemma-4-26B-A4B-it-UD-IQ2_M.gguf
            temperature=0.7,
            num_ctx=10000,
            num_predict=1024,
            num_thread=8,
            verbose=True,
            num_gpu=99,
            think=False,
            enable_thinking=False,
            model_kwargs={
                "flash_attention": True,
                "kv_cache_type": "q4_0",
                "mirostat": 2,
                "mirostat_tau": 6.0,
                "mirostat_eta": 0.1,
                "repeat_penalty": 1.15,
                "use_mmap": True,
                "use_mlock": True,
                "think": False,
                "enable_thinking": False
            }
        )

        self.corrector = TextCorrector()

        self.censor = Censor(CENSOR_WORDS)

        print(json.dumps(registry, indent=2, ensure_ascii=False))

        self.prompt = ChatPromptTemplate.from_messages([#:), :(, :D, ??, ??, ??, ??, ??
            ("system", prompt),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{input}"),
        ])

        self.chain = self.prompt | self.model

        self.history = []
                

    async def send_message(self, message: str, userId: int) -> str:
        '''Sends message to local ollama AI model and returns response'''

        message_arrived_date_time = Time.get_current_date_time()

        while await asyncio.sleep(0, result=True):
            response = ""
            is_bad = False

            corrected_message = self.corrector.correct_message(message)
            corrected_message_with_date_time = f"<time>{message_arrived_date_time}</time> <userId>{userId}</userId> {corrected_message}"
            print(corrected_message_with_date_time)

            with Timer() as time:
                async for chunk in self.chain.astream({
                    "input": corrected_message_with_date_time,
                    "history": self.history,
                    "tools": json.dumps(registry, indent=2, ensure_ascii=False)
                }):
                    content = chunk.content
                    print(content, end="", flush=True)
                    response += content
                    if await self.censor.bad_words(response): 
                        print("\n")
                        is_bad = True
                        break
                if is_bad:
                    continue
                break

        print("\n")

        logger.info(f"{response} : {time.duration:.2f}")

        self.history.append(HumanMessage(content=corrected_message_with_date_time))
        self.history.append(AIMessage(content=response))

        return response