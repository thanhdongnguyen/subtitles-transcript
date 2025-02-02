import google.generativeai as genai
import os
from loguru import logger

class Gemini:
    def __init__(self):
        genai.configure(api_key=os.environ["GEMINI_API_KEY"])



    async def call_provider(self, model: str = "", prompt: str = "", system_prompt: str = "") -> str:
        generation_config = {
            "temperature": 0.2,
            # "top_p": 0.95,
            # "top_k": 40,
            # "max_output_tokens": 20000,
        }
        model_init = genai.GenerativeModel(
            model_name=model,
            generation_config=generation_config,
            system_instruction=system_prompt,
        )
        response = await model_init.generate_content_async(
            contents=prompt,
            stream=False

        )
        logger.info(f"model: {model}, completion: {response}\n")
        return response.text

